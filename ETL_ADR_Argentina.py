import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
from fredapi import Fred # INTEGRACIÓN API FRED
import streamlit as st # <-- IMPORTACIÓN PARA QUE OBTENER LA API KEY DESDE Streamlit

# Obtenemos la clave de forma segura desde los secretos de Streamlit
FRED_API_KEY = st.secrets["FRED_API_KEY"]

def extract():
    print("--- Iniciando Extracción ---")
    # Agregamos GGAL.BA (cotización de Galicia en la bolsa local, en ARS)
    tickers = ["GGAL", "GGAL.BA", "YPF", "BMA", "PAM", "CEPU"]
    
    yf_data = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
    
    if yf_data.empty: # Corregido: Variable correcta
        print("Error: No se pudieron descargar datos de Yahoo Finance.")
        return None

    df_yf = yf_data['Close'] # Corregido: Variable correcta para el return

    # 2. Extracción Macroeconómica (API de FRED)
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # Tipo de cambio oficial (Pesos por Dólar)
        dolar_oficial = fred.get_series('DEXARUS').to_frame(name='Dolar_Oficial')
        # Tasa libre de riesgo (Bono del Tesoro a 10 años, en porcentaje)
        risk_free = fred.get_series('DGS10').to_frame(name='Risk_Free_Rate')
        
        # Unimos las variables macroeconómicas por su fecha
        macro_data = dolar_oficial.join(risk_free, how='outer')
        print("Datos macroeconómicos de FRED extraídos exitosamente.")
        
    except Exception as e:
        print(f"Advertencia: Falló la conexión con FRED ({e}). Se usarán datos nulos.")
        macro_data = pd.DataFrame()
        
    # Retornamos ambos conjuntos de datos en un diccionario
    return {'yf': df_yf, 'macro': macro_data}

def transform(raw_data): # Corregido: Ahora recibe el diccionario
    print("--- Iniciando Transformación ---")
    
    # Separamos los diccionarios
    df = raw_data['yf'].copy()
    macro_df = raw_data['macro'].copy()

    # ---> NUEVO: Normalizamos las zonas horarias para que Pandas pueda cruzarlas <---
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    # 1. Cruzamos las cotizaciones de Wall Street con la macro de FRED (por fecha)
    if not macro_df.empty:
        df = df.join(macro_df, how='left')
    
    df = df.reset_index()
    
    # 2. Cálculo del Dólar CCL Sintético
    # Ratio de conversión: 10 acciones locales = 1 ADR en NY
    df['Dolar_CCL'] = (df['GGAL.BA'] / df['GGAL']) * 10

    # Rellena los huecos (feriados) propagando el dólar del día anterior hacia adelante
    df['Dolar_CCL'] = df['Dolar_CCL'].ffill()
    
    # 3. Tratamiento de Feriados Macroeconómicos y Cálculo de Brecha
    if 'Dolar_Oficial' in df.columns:
        # Propagamos la tasa y el oficial para cubrir feriados
        df['Dolar_Oficial'] = df['Dolar_Oficial'].ffill()
        df['Risk_Free_Rate'] = df['Risk_Free_Rate'].ffill()
        
        # Calculamos la Brecha Cambiaria en %
        df['Brecha_Cambiaria'] = ((df['Dolar_CCL'] / df['Dolar_Oficial']) - 1) * 100
    else:
        df['Dolar_Oficial'] = None
        df['Risk_Free_Rate'] = 0.0
        df['Brecha_Cambiaria'] = None
        
    # 4. Descartamos la acción local para no arruinar el dashboard de ADRs
    df = df.drop(columns=['GGAL.BA'])
    
    # 5. Formato 'Long'. CLAVE: Agregamos las variables macro a los id_vars 
    # para que viajen duplicadas junto a cada fila de ticker.
    df_melted = df.melt(
        id_vars=['Date', 'Dolar_CCL', 'Dolar_Oficial', 'Risk_Free_Rate', 'Brecha_Cambiaria'], 
        var_name='Ticker', 
        value_name='Price_USD'
    )
    
    # 6. Limpieza y cálculos finales
    df_melted = df_melted.dropna(subset=['Price_USD'])
    df_melted = df_melted.sort_values(by=['Ticker', 'Date'])
    df_melted['Daily_Return'] = df_melted.groupby('Ticker')['Price_USD'].pct_change()
    df_melted['processed_at'] = datetime.now()
    
    return df_melted

def load(df):
    print("--- Iniciando Carga a SQLite ---")
    # Creamos la conexión a la base de datos local
    engine = create_engine('sqlite:///adr_argentina.db')
    
    # Guardamos los datos. 'replace' sobrescribe, 'append' acumula.
    df.to_sql('market_data', con=engine, if_exists='replace', index=False)
    print("¡Datos cargados exitosamente en adr_argentina.db!")

if __name__ == "__main__":
    # Ejecución del Pipeline
    raw_data = extract()
    transformed_data = transform(raw_data)
    load(transformed_data)
    
    print("\nResumen de los datos procesados:")
    print(transformed_data.head())
