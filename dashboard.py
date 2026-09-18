"""
Dashboard de indicadores del BCRA.

Lee directamente de sql/queries.sql: cada consulta se etiqueta con
"-- N)" en el archivo y se ejecuta contra data/bcra.db. La idea es que
lo que ves en el gráfico sea exactamente la consulta que se muestra
abajo en "Ver SQL", sin duplicar la lógica en Python.
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

import extract

DB_PATH = Path(__file__).parent / "data" / "bcra.db"
QUERIES_PATH = Path(__file__).parent / "sql" / "queries.sql"

VARIABLES = {
    1: "Reservas internacionales (millones USD)",
    4: "Tipo de cambio minorista (ARS/USD)",
    5: "Tipo de cambio mayorista (ARS/USD)",
    15: "Base monetaria (millones ARS)",
    27: "Inflación mensual (%)",
}


@st.cache_data(ttl=3600)
def load_queries() -> dict[int, str]:
    """Parsea sql/queries.sql y devuelve {numero_de_consulta: sql}."""
    texto = QUERIES_PATH.read_text(encoding="utf-8")
    marcadores = list(re.finditer(r"^-- (\d)\)", texto, flags=re.MULTILINE))
    consultas = {}
    for actual, siguiente in zip(marcadores, marcadores[1:] + [None]):
        numero = int(actual.group(1))
        fin = siguiente.start() if siguiente else len(texto)
        consultas[numero] = texto[actual.start():fin].strip()
    return consultas


def run_query(sql: str, params: dict) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


st.set_page_config(page_title="Indicadores BCRA", layout="wide")
st.title("Indicadores económicos del BCRA")
st.caption(
    "Pipeline ETL (Python + API pública del BCRA) → SQLite → consultas SQL → "
    "este dashboard. Código completo en el repo."
)

@st.cache_resource
def asegurar_datos() -> None:
    """La primera vez que se levanta la app (local o en la nube) no hay
    base de datos todavía: la generamos on-demand en vez de exigirle al
    usuario un paso manual aparte."""
    if not DB_PATH.exists():
        with st.spinner("Primera carga: descargando datos del BCRA..."):
            extract.run()


asegurar_datos()

queries = load_queries()

st.subheader("Últimos valores informados")
kpis = run_query(queries[4], {})
cols = st.columns(len(kpis))
for col, (_, row) in zip(cols, kpis.iterrows()):
    col.metric(row["descripcion"], f"{row['valor']:,.2f}", help=f"{row['unidad']} · al {row['fecha']}")

st.divider()

col_izq, col_der = st.columns([1, 2])
with col_izq:
    id_variable = st.selectbox(
        "Variable", options=list(VARIABLES.keys()), format_func=lambda i: VARIABLES[i]
    )
    desde = st.date_input("Desde", value=pd.Timestamp.today() - pd.Timedelta(days=180))
    hasta = st.date_input("Hasta", value=pd.Timestamp.today())

with col_der:
    serie = run_query(
        queries[1],
        {"id_variable": id_variable, "desde": str(desde), "hasta": str(hasta)},
    )
    if serie.empty:
        st.warning("Sin datos para ese rango. Probá correr extract.py de nuevo.")
    else:
        st.line_chart(serie.set_index("fecha")["valor"], height=320)

        ultima = serie.iloc[-1]
        st.caption(
            f"Último valor: {ultima['valor']:,.2f} "
            f"({ultima['variacion_pct']:+.2f}% vs. día hábil anterior)"
        )

    with st.expander("Ver SQL de este gráfico"):
        st.code(queries[1], language="sql")

st.divider()
st.subheader("Brecha cambiaria (minorista vs. mayorista)")
brecha = run_query(queries[3], {})
st.line_chart(brecha.set_index("fecha")["brecha_pct"], height=250)
with st.expander("Ver SQL de la brecha cambiaria"):
    st.code(queries[3], language="sql")
