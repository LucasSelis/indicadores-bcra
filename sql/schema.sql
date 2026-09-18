-- Esquema del pipeline de indicadores del BCRA.
-- variables: metadata de cada serie (una fila por indicador monetario/cambiario).
-- valores: series de tiempo, una fila por (variable, fecha).

CREATE TABLE IF NOT EXISTS variables (
    id_variable     INTEGER PRIMARY KEY,
    descripcion     TEXT NOT NULL,
    categoria       TEXT,
    periodicidad    TEXT,
    unidad          TEXT,
    moneda          TEXT
);

CREATE TABLE IF NOT EXISTS valores (
    id_variable     INTEGER NOT NULL REFERENCES variables(id_variable),
    fecha           TEXT NOT NULL,
    valor           REAL NOT NULL,
    PRIMARY KEY (id_variable, fecha)
);

CREATE INDEX IF NOT EXISTS idx_valores_fecha ON valores(fecha);
