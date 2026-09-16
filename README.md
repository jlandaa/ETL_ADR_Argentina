# 📊 ADRs Argentinos: End-to-End Data Pipeline & Dashboard
![Status: Maintained](https://img.shields.io/badge/Status-Maintained-brightgreen?style=for-the-badge)
![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

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
* **Visualización:** Streamlit y Plotly (UI/UX corporativa con Sidebar).
* **Observabilidad:** Módulo `logging` nativo para auditoría de procesos en backend.
* **Despliegue:** Streamlit Community Cloud.

## 🏗️ Arquitectura del Pipeline (ETL)
El sistema se divide en tres fases modulares para asegurar la robustez del flujo:

1.  **Extract:** Descarga automatizada de precios de cierre ajustados para tickers clave como `GGAL`, `YPF`, `BMA`, `PAM` y `CEPU`.
2.  **Transform:** Limpieza de datos y normalización de series temporales.
    * Cálculo de **Retornos Diarios** porcentuales.
    * Generación de metadatos de procesamiento (`timestamp`).
3.  **Load:** Persistencia de los datos en una base de datos relacional local (`.db`) para garantizar la integridad y velocidad de consulta desde el Dashboard.

* **Observabilidad:** Registro silencioso de eventos (`etl_process.log`) para monitorear el estado de ejecución y detectar fallos de red sin interrumpir la experiencia del usuario.

## 📈 Funcionalidades del Dashboard y Analytics

* **Optimizador de Portafolios (Markowitz):** Integración de un motor de simulación estocástica (Monte Carlo) que genera miles de combinaciones de activos en tiempo real para graficar la **Frontera Eficiente**. Identifica matemáticamente la cartera de Máximo Ratio de Sharpe y sugiere la distribución óptima de capital.
* **Análisis Cuantitativo "What-If":** Simulador dinámico e interactivo que permite al usuario asignar capital y pesos porcentuales personalizados mediante *sliders*. El sistema normaliza matemáticamente las proporciones base 100 y calcula la curva de *equity* histórica utilizando vectorización pura en Pandas.
* **Integración Macroeconómica Sintética:** Desarrollo de lógica cruzada de activos locales (BYMA) e internacionales (NYSE) para calcular en el backend el **Dólar CCL implícito**. Incluye un *toggle* en la interfaz para deflactar los precios en tiempo real y aislar el rendimiento genuino de la ilusión monetaria (inflación/devaluación).
* **Métricas de Riesgo Institucional:** Evolución de las tarjetas de KPIs clásicas hacia un análisis de riesgo profundo. Calcula en tiempo real el Ratio de Sharpe anualizado, el **VaR (Value at Risk al 95%)** y el **Maximum Drawdown**, métricas estándar en la industria de fondos de inversión.
* **Auto-Healing ETL & Data Quality:** Pipeline de datos defensivo. El sistema detecta autónomamente si falta la base de datos y la regenera. Implementa limpieza segura mediante `.dropna()` orientada a celdas para evitar el borrado masivo por fallos de API, y utiliza *Forward Fill* (`.ffill()`) para corregir desincronizaciones de feriados entre calendarios internacionales.
* **Análisis de Riesgo y Volatilidad:** Histogramas y Box-plots superpuestos con zoom estadístico automático filtrando los percentiles 1% y 99% (Outlier Mitigation) para asegurar la máxima legibilidad de la distribución.
* **Matriz de Correlación:** Mapa de calor (Heatmap) interactivo para identificar movimientos conjuntos de mercado y oportunidades de diversificación.
* **UI/UX Corporativa y Performance Optimizada:** Diseño *Data-Driven* con filtros temporales dinámicos en un Sidebar. Implementación de decoradores de memoria en RAM (`@st.cache_data`) con Time-To-Live (TTL), reduciendo el impacto en la base de datos a cero durante la interacción del usuario y garantizando respuestas en milisegundos.



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
