import numpy as np
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

# 1. Obtenemos las opciones reales disponibles en el DataFrame filtrado
opciones_tickers = df['Ticker'].unique().tolist()

# 2. Definimos los que nos gustaría que estén por defecto
valores_deseados = ["GGAL", "YPF"]

# 3. Intersección: Solo guardamos los defaults que REALMENTE existen en las opciones
defaults_validos = [ticker for ticker in valores_deseados if ticker in opciones_tickers]

# 4. Renderizamos el widget de forma segura
tickers = st.sidebar.multiselect(
    "Selecciona los ADRs a comparar:", 
    options=opciones_tickers, 
    default=defaults_validos
)

if tickers:
    df_filtered = df[df['Ticker'].isin(tickers)]

    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Exportar Datos")
    
    # Convertimos el DataFrame filtrado a CSV
    @st.cache_data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')
    
    csv = convert_df(df_filtered)
    
    st.sidebar.download_button(
        label="Descargar datos en CSV",
        data=csv,
        file_name='adrs_argentinos_filtrados.csv',
        mime='text/csv',
    )

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

            # NUEVO: Métricas de Riesgo Institucional
            # VaR 95%: El percentil 5 de los retornos diarios
            var_95 = ticker_returns.quantile(0.05) * 100
            
            # Max Drawdown: La peor caída desde un pico histórico
            cumulative_returns = (1 + ticker_returns).cumprod()
            peak = cumulative_returns.cummax()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = drawdown.min() * 100

            # Modificamos cómo se dibuja la columna para mostrar todo
            with cols[i]:
                st.metric(
                    label=f"{ticker} (Sharpe: {sharpe_str})",
                    value=f"{total_ret:.1f}%",
                    # Agregamos el signo negativo al texto si el retorno es menor a 0
                    delta="- Retorno Total" if total_ret < 0 else "Retorno Total"
                )
                # Agregamos las métricas extra en texto pequeño
                # Solución UX: white-space: nowrap fuerza a que el número nunca se caiga al renglón de abajo
                risk_metrics_html = f"""
                <div style="font-size: 0.75em; color: #808495; line-height: 1.4;">
                    <span style="white-space: nowrap;">🔻 VaR (95%): {var_95:.2f}%</span><br>
                    <span style="white-space: nowrap;">📉 Max Drawdown: {max_drawdown:.2f}%</span>
                </div>
                """
                st.markdown(risk_metrics_html, unsafe_allow_html=True)
        
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

# --- Simulador de Portafolios (Frontera de Markowitz) ---
    st.markdown("---")
    st.subheader("🧠 Optimizador de Portafolios (Markowitz)")
    
    # Necesitamos al menos 2 activos para hacer un portafolio
    if len(tickers) > 1:
        # 1. Parámetros y Cálculos Estadísticos (Anualizados)
        returns_pivot = df_pivot.dropna()
        mean_returns = returns_pivot.mean() * 252
        cov_matrix = returns_pivot.cov() * 252
        num_portfolios = 5000
        risk_free_rate = 0.0 # Tasa libre de riesgo simplificada
        
        # Matrices para guardar los resultados
        results = np.zeros((3, num_portfolios))
        weights_record = []
        
        # 2. Simulación de Monte Carlo
        for i in range(num_portfolios):
            # Generar pesos aleatorios que sumen 1 (100%)
            weights = np.random.random(len(tickers))
            weights /= np.sum(weights)
            weights_record.append(weights)
            
            # Aplicar fórmulas matemáticas (Álgebra Lineal)
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_std_dev = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            # Almacenar Retorno, Volatilidad y Ratio de Sharpe
            results[0,i] = portfolio_return
            results[1,i] = portfolio_std_dev
            results[2,i] = (portfolio_return - risk_free_rate) / portfolio_std_dev
            
        # 3. Identificar el Portafolio Óptimo (Max Sharpe)
        max_sharpe_idx = np.argmax(results[2])
        opt_ret = results[0, max_sharpe_idx]
        opt_vol = results[1, max_sharpe_idx]
        opt_weights = weights_record[max_sharpe_idx]
        
        # 4. Visualización Interactiva
        fig_ef = px.scatter(
            x=results[1,:], y=results[0,:], color=results[2,:],
            labels={'x': 'Riesgo (Volatilidad)', 'y': 'Retorno Esperado', 'color': 'Sharpe Ratio'},
            title="Frontera Eficiente (5000 Simulaciones)",
            color_continuous_scale="Viridis"
        )
        
        # Resaltar la estrella roja (El mejor portafolio)
        fig_ef.add_scatter(
            x=[opt_vol], y=[opt_ret], mode='markers',
            marker=dict(color='red', size=14, symbol='star'),
            name='Máximo Sharpe', hoverinfo='skip'
        )
        
        st.plotly_chart(fig_ef, use_container_width=True)
        
        # 5. Mostrar la recomendación de inversión
        st.write("**Distribución Sugerida de Capital (Para Maximizar el Ratio de Sharpe):**")
        weights_df = pd.DataFrame({
            'Activo': tickers, 
            'Asignación Sugerida': [f"{w*100:.1f}%" for w in opt_weights]
        })
        st.dataframe(weights_df, hide_index=True)
        
    else:
        st.info("💡 Selecciona al menos dos activos en el menú lateral para habilitar el simulador de portafolios.")




