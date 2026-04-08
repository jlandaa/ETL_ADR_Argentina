import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Agregamos text
import plotly.express as px
import os
import sys
import logging

logging.basicConfig(
    filename='etl_process.log',      # Nombre del archivo silencioso
    level=logging.INFO,              # Nivel de registro (INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s' # Formato: Fecha - Nivel - Mensaje
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem; /* Reduce el espacio superior */
            padding-bottom: 0rem;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Configuración de rutas y módulos
sys.path.append(os.path.dirname(__file__))
import ETL_ADR_Argentina as etl 

# 2. Configuración de Base de Datos
db_file = 'adr_argentina.db'
engine = create_engine(f'sqlite:///{db_file}')

# 3. Lógica de Control de Datos (Auto-ETL) con Logging
def check_and_run_etl():
    table_exists = False
    if os.path.exists(db_file):
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='market_data'"))
            table_exists = result.fetchone() is not None

    if not table_exists:
        st.warning("📊 Generando base de datos financiera por primera vez...")
        logging.info("Iniciando proceso ETL automático: No se detectó la base de datos local.") # <-- LOG
        
        raw = etl.extract()
        if raw is not None:
            transformed = etl.transform(raw)
            etl.load(transformed)
            st.success("✅ Datos procesados y cargados.")
            logging.info("Proceso ETL finalizado con éxito. Datos cargados en SQLite.") # <-- LOG
        else:
            st.error("No se pudieron obtener datos de la API.")
            logging.error("Fallo crítico: No se pudieron extraer datos desde Yahoo Finance.") # <-- LOG ERROR
            st.stop()
    else:
        logging.info("Verificación de DB exitosa. Inicializando Dashboard.") # <-- LOG

# Ejecutamos la verificación antes de cualquier carga
check_and_run_etl()

# 4. Función de carga protegida
@st.cache_data(ttl=3600)  # Mantiene los datos en memoria por 1 hora (3600 segundos)
def load_data():
    query = "SELECT * FROM market_data"
    # Usamos la conexión de engine para leer
    return pd.read_sql(query, engine.connect())
    
# --- INTERFAZ DEL DASHBOARD ---
st.title("📊 Análisis de ADRs Argentinos")

# Carga inicial y conversión de fechas
df = load_data()
df['Date'] = pd.to_datetime(df['Date'])

# --- CONTROLES EN EL SIDEBAR ---
st.sidebar.header("⚙️ Filtros del Dashboard")

st.sidebar.subheader("📅 Período de Análisis")
time_filter = st.sidebar.radio(
    "Selecciona el rango de tiempo:",
    options=["1 Mes", "3 Meses", "6 Meses", "YTD", "1 Año", "Máximo"],
    index=4
)

# Lógica de fechas (se mantiene igual)
max_date = df['Date'].max()
if time_filter == "1 Mes":
    start_date = max_date - pd.DateOffset(months=1)
elif time_filter == "3 Meses":
    start_date = max_date - pd.DateOffset(months=3)
elif time_filter == "6 Meses":
    start_date = max_date - pd.DateOffset(months=6)
elif time_filter == "YTD":
    start_date = pd.to_datetime(f"{max_date.year}-01-01")
elif time_filter == "1 Año":
    start_date = max_date - pd.DateOffset(years=1)
else:
    start_date = df['Date'].min()

df = df[df['Date'] >= start_date]

st.sidebar.markdown("---")
st.sidebar.subheader("🏢 Activos")
tickers = st.sidebar.multiselect(
    "Selecciona los ADRs a comparar:", 
    options=df['Ticker'].unique(), 
    default=["GGAL", "YPF"]
)

if tickers:
    df_filtered = df[df['Ticker'].isin(tickers)]

    # --- Cálculo de Métricas (Ratio de Sharpe) ---
    st.markdown("### 📈 Métricas de Rendimiento")
    cols = st.columns(len(tickers))
    
    for i, ticker in enumerate(tickers):
        t_data = df_filtered[df_filtered['Ticker'] == ticker].sort_values('Date')
        ticker_returns = t_data['Daily_Return'].dropna()
        
        if not ticker_returns.empty:
            # Cálculo del Ratio de Sharpe (Anualizado)
            # Asumimos una tasa libre de riesgo de 0 para simplificar el análisis de renta variable pura
            sharpe_ratio = (ticker_returns.mean() / ticker_returns.std()) * (252**0.5)
            
            # Rendimiento Total en el periodo
            total_ret = (t_data['Price_USD'].iloc[-1] / t_data['Price_USD'].iloc[0] - 1) * 100
    
            # Lógica de formateo dinámico
            if abs(sharpe_ratio) < 0.01 and sharpe_ratio != 0:
                sharpe_str = f"{sharpe_ratio:.4f}" # Muestra 4 decimales si es muy chiquito
            else:
                sharpe_str = f"{sharpe_ratio:.2f}" # Muestra 2 decimales si es un número normal

            with cols[i]:
                st.metric(
                    label=f"Sharpe Ratio - {ticker}",
                    value=sharpe_str, # Usamos la variable dinámica
                    delta=f"{total_ret:.1f}% Retorno Total"
                )
        
    # Gráfico de Precios
    fig_price = px.line(df_filtered, x='Date', y='Price_USD', color='Ticker',
                        title="Evolución de Precios (USD)")
    st.plotly_chart(fig_price, use_container_width=True)
    
    # --- Gráfico de Retornos (Optimizado para Data Quality) ---
    # 1. Calculamos los límites para hacer zoom (descartamos el 1% de outliers extremos)
    min_val = df_filtered['Daily_Return'].quantile(0.01)
    max_val = df_filtered['Daily_Return'].quantile(0.99)

    # 2. Generamos el histograma con granularidad y límites dinámicos
    fig_ret = px.histogram(
        df_filtered, 
        x='Daily_Return', 
        color='Ticker',
        marginal="box", 
        title="Distribución de Retornos Diarios (Zoom en el 98% del volumen)",
        nbins=100, # Fuerza barras más finitas
        range_x=[min_val, max_val] # Ajusta el eje X a la zona normal
    )
    
    # 3. Superponemos las barras con transparencia para comparar mejor las distribuciones
    fig_ret.update_layout(barmode='overlay')
    fig_ret.update_traces(opacity=0.75)
    
    st.plotly_chart(fig_ret, use_container_width=True)

    # Matriz de Correlación
    st.markdown("---")
    st.subheader("🔗 Matriz de Correlación de Retornos")
    df_pivot = df_filtered.pivot(index='Date', columns='Ticker', values='Daily_Return')
    corr_matrix = df_pivot.corr()
    fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto",
                         color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.warning("Selecciona al menos un ticker para visualizar los datos.")





