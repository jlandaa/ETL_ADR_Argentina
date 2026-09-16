import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

def extract():
    print("--- Iniciando Extracción ---")
    # Agregamos GGAL.BA (cotización de Galicia en la bolsa local, en ARS)
    tickers = ["GGAL", "GGAL.BA", "YPF", "BMA", "PAM", "CEPU"]
    
    data = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
    
    if data.empty:
        print("Error: No se pudieron descargar datos.")
        return None

    df_raw = data['Close']
    return df_raw

def transform(df):
    print("--- Iniciando Transformación ---")
    df = df.reset_index()
    
    # 1. Cálculo del Dólar CCL Sintético
    # Ratio de conversión: 10 acciones locales = 1 ADR en NY
    df['Dolar_CCL'] = (df['GGAL.BA'] / df['GGAL']) * 10

    # Rellena los huecos (feriados) propagando el dólar del día anterior hacia adelante
    df['Dolar_CCL'] = df['Dolar_CCL'].ffill()
    
    # 2. Descartamos la acción local para no arruinar el dashboard de ADRs
    df = df.drop(columns=['GGAL.BA'])
    
    # 3. Formato 'Long'. CLAVE: Agregamos 'Dolar_CCL' a los id_vars 
    # para que el valor del dólar se duplique en cada fila de ticker.
    df_melted = df.melt(id_vars=['Date', 'Dolar_CCL'], var_name='Ticker', value_name='Price_USD')
    
    # 4. Limpieza y cálculos
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
