import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

def extract():
    print("--- Iniciando Extracción Consolidada ---")
    # Sumamos ARS=X (Dólar Oficial) y ^TNX (Tasa del Tesoro a 10 años) a la lista
    tickers = ["GGAL", "GGAL.BA", "YPF", "BMA", "PAM", "CEPU", "ARS=X", "^TNX"]
    
    yf_data = yf.download(tickers, period="1y", interval="1d", auto_adjust=True)
    
    if yf_data.empty:
        print("Error: No se pudieron descargar datos de Yahoo Finance.")
        return None

    # Retornamos solo la tabla de precios de cierre
    df_yf = yf_data['Close'] 
    return {'yf': df_yf}

def transform(raw_data): 
    print("--- Iniciando Transformación ---")
    df = raw_data['yf'].copy()

    # Normalización extrema de fechas
    df.index = pd.to_datetime(df.index).normalize()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
        
    # Renombramos las columnas macro antes de procesarlas
    df = df.rename(columns={'ARS=X': 'Dolar_Oficial', '^TNX': 'Risk_Free_Rate'})
    
    df = df.reset_index()
    
    # 1. Cálculo del Dólar CCL Sintético
    df['Dolar_CCL'] = (df['GGAL.BA'] / df['GGAL']) * 10
    
    # 2. Tratamiento de Feriados Macroeconómicos (Propagamos hacia adelante y atrás para evitar nulos)
    df['Dolar_CCL'] = df['Dolar_CCL'].ffill().bfill()
    df['Dolar_Oficial'] = df['Dolar_Oficial'].ffill().bfill()
    df['Risk_Free_Rate'] = df['Risk_Free_Rate'].ffill().bfill()
    
    # 3. Calculamos la Brecha Cambiaria en %
    df['Brecha_Cambiaria'] = ((df['Dolar_CCL'] / df['Dolar_Oficial']) - 1) * 100
        
    # 4. Descartamos la acción local para no arruinar el dashboard de ADRs
    df = df.drop(columns=['GGAL.BA'])
    
    # 5. Formato 'Long'
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
