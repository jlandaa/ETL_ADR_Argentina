import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Agregamos text
import plotly.express as px
import os
import sys

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

# 3. Lógica de Control de Datos (Auto-ETL)
def check_and_run_etl():
    # Verificamos si la tabla existe realmente en el archivo .db
    table_exists = False
    if os.path.exists(db_file):
        with engine.connect() as conn:
            # Consulta para verificar si la tabla market_data existe en SQLite
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='market_data'"))
            table_exists = result.fetchone() is not None

    if not table_exists:
        st.warning("📊 Generando base de datos financiera por primera vez...")
        raw = etl.extract()
        if raw is not None:
            transformed = etl.transform(raw)
            etl.load(transformed)
            st.success("✅ Datos procesados y cargados.")
        else:
            st.error("No se pudieron obtener datos de la API.")
            st.stop()

# Ejecutamos la verificación antes de cualquier carga
check_and_run_etl()

# 4. Función de carga protegida
def load_data():
    query = "SELECT * FROM market_data"
    # Usamos la conexión de engine para leer
    return pd.read_sql(query, engine.connect())
    
# --- INTERFAZ DEL DASHBOARD ---
st.title("📊 Análisis de ADRs Argentinos")
df = load_data()

tickers = st.multiselect("Selecciona los ADRs a comparar:", 
                         options=df['Ticker'].unique(), 
                         default=["GGAL", "YPF"])

if tickers:
    df_filtered = df[df['Ticker'].isin(tickers)]

    # --- Cálculo de Métricas (Ratio de Sharpe) ---
    st.markdown("### 📈 Métricas de Rendimiento")
    cols = st.columns(len(tickers))
    
    for i, ticker in enumerate(tickers):
        ticker_data = df_filtered[df_filtered['Ticker'] == ticker]['Daily_Return'].dropna()
        
        if not ticker_data.empty:
            # Cálculo del Ratio de Sharpe (Anualizado)
            # Asumimos una tasa libre de riesgo de 0 para simplificar el análisis de renta variable pura
            sharpe_ratio = (ticker_data.mean() / ticker_data.std()) * (252**0.5)
            
            # Rendimiento Total en el periodo
            total_ret = (df_filtered[df_filtered['Ticker'] == ticker]['Price_USD'].iloc[-1] / 
                         df_filtered[df_filtered['Ticker'] == ticker]['Price_USD'].iloc[0] - 1) * 100
    
            with cols[i]:
                st.metric(
                    label=f"Sharpe Ratio - {ticker}",
                    value=f"{sharpe_ratio:.2f}",
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
    df_pivot = df.pivot(index='Date', columns='Ticker', values='Daily_Return')
    corr_matrix = df_pivot.corr()
    fig_corr = px.imshow(corr_matrix, text_auto=".2f", aspect="auto",
                         color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
    st.plotly_chart(fig_corr, use_container_width=True)
else:
    st.warning("Selecciona al menos un ticker para visualizar los datos.")





