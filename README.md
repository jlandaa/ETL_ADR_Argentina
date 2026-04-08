# 📊 ADRs Argentinos: End-to-End Data Pipeline & Dashboard

Este proyecto implementa un ciclo completo de **Data Analysis** y **Data Engineering** para monitorear y analizar los **ADRs (American Depositary Receipts)** de empresas argentinas que cotizan en el NYSE. 

## 🔗 Demo en Vivo
Puedes acceder al dashboard interactivo aquí:  
👉 **[https://jml-dashboard-adr.streamlit.app/](https://jml-dashboard-adr.streamlit.app/)**

## 🎯 Objetivo del Proyecto
Automatizar la recolección, transformación y visualización de activos financieros para facilitar la toma de decisiones. La herramienta permite analizar la volatilidad, los retornos diarios, la correlación sectorial y el **rendimiento ajustado por riesgo** en tiempo real mediante un pipeline de datos robusto.

## 🛠️ Stack Tecnológico
* **Lenguaje:** Python (Pandas y NumPy para estadística financiera).
* **Extracción:** API de Yahoo Finance (`yfinance`).
* **Almacenamiento:** SQLite con SQLAlchemy (ORM).
* **Visualización:** Streamlit y Plotly (UI/UX interactiva).
* **Despliegue:** Streamlit Community Cloud.

## 🏗️ Arquitectura del Pipeline (ETL)
El sistema se divide en tres fases modulares para asegurar la robustez del flujo:

1.  **Extract:** Descarga automatizada de precios de cierre ajustados para tickers clave como `GGAL`, `YPF`, `BMA`, `PAM` y `CEPU`.
2.  **Transform:** Limpieza de datos y normalización de series temporales.
    * Cálculo de **Retornos Diarios** porcentuales.
    * Generación de metadatos de procesamiento (`timestamp`).
3.  **Load:** Persistencia de los datos en una base de datos relacional local (`.db`) para garantizar la integridad y velocidad de consulta desde el Dashboard.

## 📈 Funcionalidades del Dashboard
* **KPIs Financieros (NUEVO):** Tarjetas de métricas interactivas que calculan en tiempo real el **Ratio de Sharpe** anualizado y el **Retorno Total** de la selección, con formateo dinámico condicional para gestionar escenarios de "Volatility Drag".
* **Evolución Histórica:** Gráficos de líneas interactivos para comparar precios ajustados en USD de múltiples activos simultáneamente.
* **Análisis de Riesgo y Volatilidad:** Histogramas y Box-plots superpuestos. Se implementó un zoom estadístico automático filtrando los percentiles 1% y 99% (Outlier Mitigation) para asegurar la máxima legibilidad de la campana de distribución.
* **Matriz de Correlación:** Mapa de calor (Heatmap) dinámico que se ajusta a la selección del usuario para identificar movimientos conjuntos de mercado y oportunidades de diversificación.
* **Auto-Healing ETL:** El dashboard detecta automáticamente el estado de la base de datos; si la tabla no existe o está vacía, dispara el proceso de extracción y carga de forma autónoma antes de renderizar la interfaz.



## 🚀 Instalación y Uso Local
1.  Clonar el repositorio:
    ```bash
    git clone https://github.com/jlandaa/ETL_ADR_Argentina.git
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
