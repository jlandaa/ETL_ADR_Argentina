import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

def extract():
    print("--- Iniciando Extracción ---")
    tickers = ["GGAL", "YPF", "BMA", "PAM", "CEPU"]
    
    # Usamos auto_adjust=True para que 'Close' ya sea el precio ajustado
    data = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
    
    # Verificamos si bajó datos
    if data.empty:
        print("Error: No se pudieron descargar datos. Revisa tu conexión.")
        return None

    # En versiones nuevas, yfinance devuelve un MultiIndex. 
    # Seleccionamos la sección 'Close' que contiene todos los tickers.
    df_raw = data['Close']
    return df_raw

def transform(df):
    print("--- Iniciando Transformación ---")
    # 1. Limpieza: Eliminar filas con valores nulos (días sin mercado)
    df = df.dropna()
    
    # 2. Resetear índice para tener la fecha como columna
    df = df.reset_index()
    
    # 3. Formato 'Long': Ideal para análisis de datos y SQL
    df_melted = df.melt(id_vars=['Date'], var_name='Ticker', value_name='Price_USD')
    
    # 4. Cálculo de Retornos Diarios (%)
    df_melted['Daily_Return'] = df_melted.groupby('Ticker')['Price_USD'].pct_change()
    
    # 5. Agregar metadata: Fecha de procesamiento
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