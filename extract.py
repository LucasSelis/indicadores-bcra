"""
Extrae series monetarias y cambiarias del BCRA (API pública, sin API key)
y las carga en SQLite.

API: https://api.bcra.gob.ar/estadisticas/v4.0/monetarias
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
DB_PATH = Path(__file__).parent / "data" / "bcra.db"
SCHEMA_PATH = Path(__file__).parent / "sql" / "schema.sql"

# Variables que nos interesan para el dashboard: id -> descripción corta.
# El id es el "idVariable" que expone la API del BCRA.
VARIABLES = {
    1: "Reservas internacionales",
    4: "Tipo de cambio minorista",
    5: "Tipo de cambio mayorista",
    15: "Base monetaria",
    27: "Inflación mensual",
}

# requests.get a la API pública del BCRA falla la verificación SSL con
# algunas cadenas de certificados corporativos/Windows; se desactiva la
# verificación acá porque el destino es fijo y conocido (api.bcra.gob.ar).
VERIFY_SSL = False


def fetch_metadata() -> dict[int, dict]:
    """Trae la descripción/unidad/periodicidad oficial de cada variable."""
    resp = requests.get(BASE_URL, params={"limit": 1000}, verify=VERIFY_SSL, timeout=30)
    resp.raise_for_status()
    resultados = resp.json()["results"]
    return {r["idVariable"]: r for r in resultados if r["idVariable"] in VARIABLES}


def fetch_serie(id_variable: int, desde: str, hasta: str) -> list[dict]:
    """Trae la serie histórica de una variable entre dos fechas (paginada)."""
    detalle: list[dict] = []
    offset = 0
    while True:
        resp = requests.get(
            f"{BASE_URL}/{id_variable}",
            params={"desde": desde, "hasta": hasta, "limit": 1000, "offset": offset},
            verify=VERIFY_SSL,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        pagina = payload["results"][0]["detalle"] if payload["results"] else []
        detalle.extend(pagina)
        total = payload["metadata"]["resultset"]["count"]
        offset += len(pagina)
        if offset >= total or not pagina:
            break
    return detalle


def build_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_variables(conn: sqlite3.Connection, metadata: dict[int, dict]) -> None:
    rows = [
        (
            meta["idVariable"],
            meta["descripcion"].strip(),
            meta.get("categoria"),
            meta.get("periodicidad"),
            meta.get("unidadExpresion"),
            meta.get("moneda"),
        )
        for meta in metadata.values()
    ]
    conn.executemany(
        """
        INSERT INTO variables (id_variable, descripcion, categoria, periodicidad, unidad, moneda)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_variable) DO UPDATE SET
            descripcion = excluded.descripcion,
            categoria = excluded.categoria,
            periodicidad = excluded.periodicidad,
            unidad = excluded.unidad,
            moneda = excluded.moneda
        """,
        rows,
    )


def load_valores(conn: sqlite3.Connection, id_variable: int, detalle: list[dict]) -> None:
    rows = [(id_variable, d["fecha"], d["valor"]) for d in detalle]
    conn.executemany(
        """
        INSERT INTO valores (id_variable, fecha, valor)
        VALUES (?, ?, ?)
        ON CONFLICT(id_variable, fecha) DO UPDATE SET valor = excluded.valor
        """,
        rows,
    )


def run(anios_historia: int = 2) -> None:
    hasta = dt.date.today()
    desde = hasta - dt.timedelta(days=365 * anios_historia)

    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        build_schema(conn)

        print("Descargando metadata de variables...")
        metadata = fetch_metadata()
        load_variables(conn, metadata)

        for id_variable, nombre in VARIABLES.items():
            print(f"Descargando serie: {nombre} (id={id_variable})...")
            detalle = fetch_serie(id_variable, desde.isoformat(), hasta.isoformat())
            load_valores(conn, id_variable, detalle)
            print(f"  {len(detalle)} registros cargados")

        conn.commit()
        print(f"\nListo. Base de datos actualizada en {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    run()
