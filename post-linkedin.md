Sumé SQL a mi caja de herramientas con un proyecto completo, de punta a punta.

Vengo del lado de negocio (Economía Empresarial, análisis financiero) y en mi trabajo actual en Pronto Express armé automatizaciones y paneles con Power BI, JavaScript e integraciones con nuestro ERP. Lo que no tenía documentado en ningún lado era SQL "puro" — así que armé un proyecto específicamente para eso.

Es un pipeline de indicadores económicos de Argentina, con datos públicos del BCRA:

→ Extracción: Python consume la API pública del BCRA (reservas, tipo de cambio, base monetaria, inflación)
→ Modelo: SQLite, con las series cargadas en un esquema simple de variables + valores
→ Análisis: consultas SQL con window functions (LAG, ROW_NUMBER) para variaciones diarias, promedios mensuales y la brecha cambiaria minorista vs. mayorista
→ Visualización: un dashboard en Streamlit donde cada gráfico tiene un botón "Ver SQL" que muestra la consulta real que lo genera

Código completo acá: https://github.com/LucasSelis/indicadores-bcra

Sigo sumando proyectos de datos — si estás armando algo parecido o querés compartir feedback, encantado de charlar.

#SQL #Python #DataAnalytics #BusinessIntelligence #BCRA
