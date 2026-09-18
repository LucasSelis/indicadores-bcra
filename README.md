# Indicadores económicos del BCRA

Dashboard de indicadores monetarios y cambiarios de Argentina, armado con
datos públicos del Banco Central (BCRA). Pensado como pieza de portfolio
para roles de **Data Analyst / Data Engineer**: cubre extracción vía API,
modelado en SQL y visualización, de punta a punta.

## Qué hace

1. **Extracción (`extract.py`)**: descarga series históricas de la
   [API pública del BCRA](https://api.bcra.gob.ar/estadisticas/v4.0/monetarias)
   (reservas internacionales, tipo de cambio minorista/mayorista, base
   monetaria, inflación mensual) y las carga en SQLite.
2. **Modelo (`sql/schema.sql`)**: dos tablas — `variables` (metadata de cada
   serie) y `valores` (serie de tiempo `id_variable` + `fecha` + `valor`).
3. **Análisis (`sql/queries.sql`)**: las consultas que alimentan el
   dashboard, con `LAG()` para variación día a día, `GROUP BY` para
   promedios mensuales, un `JOIN` para la brecha cambiaria minorista vs.
   mayorista, y `ROW_NUMBER() OVER (PARTITION BY ...)` para el último valor
   de cada variable.
4. **Dashboard (`dashboard.py`)**: Streamlit. Cada gráfico tiene un
   desplegable "Ver SQL" que muestra la consulta real que lo generó —
   no hay lógica de negocio duplicada en Python.

## Cómo correrlo

```bash
pip install -r requirements.txt
python extract.py          # descarga los datos y arma data/bcra.db
streamlit run dashboard.py # levanta el dashboard en http://localhost:8501
```

## Estructura

```
extract.py          # ETL: API del BCRA -> SQLite
dashboard.py         # UI Streamlit, ejecuta sql/queries.sql
sql/
  schema.sql          # DDL de las tablas
  queries.sql         # consultas analíticas (una por gráfico)
data/
  bcra.db             # generado por extract.py (no versionado)
```

## Por qué este proyecto

Arranqué desde el lado de negocio (Economía Empresarial, análisis
financiero) y sumé BI/automatización en mi trabajo actual con Power BI,
JavaScript y paneles conectados a un ERP. Lo que no tenía documentado en
ningún lado era SQL "puro" — este proyecto lo muestra explícitamente:
window functions, agregaciones y joins corriendo contra una base real,
no solo consultas visuales armadas en una herramienta de BI.

## Stack

Python · SQL (SQLite) · Streamlit · API REST
