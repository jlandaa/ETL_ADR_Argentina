# 📊 ADRs Argentinos: End-to-End Data Pipeline & Dashboard

Este proyecto implementa un ciclo completo de **Data Analysis** y **Data Engineering** para monitorear y analizar los **ADRs (American Depositary Receipts)** de empresas argentinas que cotizan en el NYSE. 

## 🔗 Demo en Vivo
Puedes acceder al dashboard interactivo aquí:  
👉 **[https://jml-dashboard-adr.streamlit.app/](https://jml-dashboard-adr.streamlit.app/)**

## 🎯 Objetivo del Proyecto
Automatizar la recolección, transformación y visualización de activos financieros para facilitar el análisis de volatilidad, retornos diarios y correlación de mercado en tiempo real.

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python (Pandas, NumPy).
* **Extracción:** API de Yahoo Finance (`yfinance`).
* **Almacenamiento:** SQLite con SQLAlchemy (ORM).
* **Visualización:** Streamlit y Plotly.
* **Despliegue:** Streamlit Community Cloud.

## 🏗️ Arquitectura del Pipeline (ETL)
El sistema se divide en tres fases modulares para asegurar la robustez del flujo:

1.  **Extract:** Descarga automatizada de precios de cierre ajustados para tickers clave como `GGAL`, `YPF`, `BMA`, `PAM` y `CEPU`.
2.  **Transform:** Limpieza de datos y normalización de series temporales.
    * Cálculo de **Retornos Diarios** porcentuales.
    * Generación de metadatos de procesamiento (`timestamp`).
3.  **Load:** Persistencia de los datos en una base de datos relacional local (`.db`) para garantizar la integridad y velocidad de consulta desde el Dashboard.

## 📈 Funcionalidades del Dashboard
* **Evolución Histórica:** Gráficos interactivos para comparar precios en USD.
* **Análisis de Volatilidad:** Histogramas con Box-plots para entender la distribución de retornos.
* **Matriz de Correlación:** Mapa de calor (Heatmap) para identificar movimientos conjuntos de activos y diversificación de riesgo.
* **Auto-Healing:** El dashboard detecta automáticamente el estado de la base de datos; si los datos no existen, dispara el proceso ETL de forma autónoma.



## 🚀 Instalación y Uso Local
1.  Clonar el repositorio:
    ```bash
    git clone [https://github.com/jlandaa/ETL_ADR_Argentina.git](https://github.com/jlandaa/ETL_ADR_Argentina.git)
    ```
2.  Crear y activar un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```
3.  Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```
4.  Ejecutar la aplicación:
    ```bash
    streamlit run dashboard_adr.py
    ```

---

## 👨‍💻 Sobre mí
**Juan Manuel Landa**
* **Ingeniero en Computación** | **Data Analyst & BI Consultant**
* 📍 Quilmes, Buenos Aires, Argentina
* 💼 [LinkedIn](https://ar.linkedin.com/in/juan-manuel-landa/en)
* 🌐 [Portfolio Personal](https://juan-manuel-landa.netlify.app/)

Este proyecto forma parte de mi búsqueda activa de nuevas oportunidades en el área de **Data & Business Intelligence**.
