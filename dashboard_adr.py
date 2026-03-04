import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import sys
import os
# Añadimos la carpeta actual al "path" de Python para que encuentre el archivo ETL
sys.path.append(os.path.dirname(__file__))
import ETL_ADR_Argentina.py  # IMPORTANTE: Esto conecta ambos archivos

# Configuración de la página
st.set_page_config(page_title="Dashboard ADRs Argentinos", layout="wide")

# LÓGICA DE AUTO-ETL
db_file = 'adr_argentina.db'
engine = create_engine(f'sqlite:///{db_file}')

if not os.path.exists(db_file):
    st.warning("Base de datos no encontrada. Iniciando ETL...")
    raw = etl_adr_argentina.extract()
    if raw is not None:
        transformed = etl_adr_argentina.transform(raw)
        etl_adr_argentina.load(transformed)
        st.success("Datos cargados correctamente.")

def load_data():
    query = "SELECT * FROM market_data"
    df = pd.read_sql(query, engine)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

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


