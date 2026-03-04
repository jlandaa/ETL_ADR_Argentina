import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text # Agregamos text
import plotly.express as px
import os
import sys

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
    
    # Gráfico de Precios
    fig_price = px.line(df_filtered, x='Date', y='Price_USD', color='Ticker',
                        title="Evolución de Precios (USD)")
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Gráfico de Retornos
    fig_ret = px.histogram(df_filtered, x='Daily_Return', color='Ticker',
                           marginal="box", title="Distribución de Retornos Diarios")
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





