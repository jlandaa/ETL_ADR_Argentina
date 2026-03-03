import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard ADRs Argentinos", layout="wide")

# Conexión a la base de datos que creaste con el ETL
engine = create_engine('sqlite:///adr_argentina.db')

def load_data():
    query = "SELECT * FROM market_data"
    df = pd.read_sql(query, engine)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

st.title("📊 Análisis de ADRs Argentinos")
df = load_data()

# Filtro de Tickers
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
else:
    st.warning("Selecciona al menos un ticker para visualizar los datos.")



# --- Nueva Sección: Matriz de Correlación ---
st.markdown("---")
st.subheader("🔗 Matriz de Correlación de Retornos")
st.info("Muestra qué tan alineados se mueven los activos entre sí (1.0 es correlación perfecta).")

# 1. Transformar datos de formato 'long' a 'wide' para calcular correlación
df_pivot = df.pivot(index='Date', columns='Ticker', values='Daily_Return')

# 2. Calcular la matriz de correlación de Pearson
corr_matrix = df_pivot.corr()

# 3. Crear el Mapa de Calor (Heatmap) con Plotly
fig_corr = px.imshow(
    corr_matrix,
    text_auto=".2f", # Muestra los números con 2 decimales
    aspect="auto",
    color_continuous_scale='RdBu_r', # Rojo para negativa, Azul para positiva
    zmin=-1, zmax=1,                 # Escala fija de correlación
    title="Correlación de Retornos Diarios (Último Año)"
)

st.plotly_chart(fig_corr, use_container_width=True)