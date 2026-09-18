-- Consultas analíticas usadas por el dashboard.
-- Todas corren sobre SQLite; se apoyan en window functions para no traer
-- toda la serie a pandas y calcular variaciones ahí.

-- 1) Serie diaria de una variable, con variación % contra el día hábil anterior.
--    :id_variable, :desde, :hasta son parámetros.
SELECT
    fecha,
    valor,
    valor - LAG(valor) OVER (ORDER BY fecha)                                   AS variacion_absoluta,
    ROUND(
        100.0 * (valor - LAG(valor) OVER (ORDER BY fecha))
        / NULLIF(LAG(valor) OVER (ORDER BY fecha), 0)
    , 2)                                                                       AS variacion_pct
FROM valores
WHERE id_variable = :id_variable
  AND fecha BETWEEN :desde AND :hasta
ORDER BY fecha;

-- 2) Promedio mensual de una variable (útil para series diarias como el
--    tipo de cambio o las reservas, que hay que "bajar" a frecuencia mensual
--    para compararlas con la inflación).
SELECT
    substr(fecha, 1, 7)               AS mes,
    ROUND(AVG(valor), 2)              AS valor_promedio,
    ROUND(MIN(valor), 2)              AS valor_min,
    ROUND(MAX(valor), 2)              AS valor_max
FROM valores
WHERE id_variable = :id_variable
GROUP BY mes
ORDER BY mes;

-- 3) Brecha cambiaria: compara mayorista vs. minorista en la misma fecha
--    (join de la tabla contra sí misma por fecha, cada lado filtrado por
--    variable distinta).
SELECT
    a.fecha,
    a.valor                              AS tipo_cambio_minorista,
    b.valor                              AS tipo_cambio_mayorista,
    ROUND(100.0 * (a.valor - b.valor) / b.valor, 2) AS brecha_pct
FROM valores a
JOIN valores b
  ON a.fecha = b.fecha
WHERE a.id_variable = 4   -- tipo de cambio minorista
  AND b.id_variable = 5   -- tipo de cambio mayorista
ORDER BY a.fecha;

-- 4) Último valor informado de cada variable cargada (para las tarjetas
--    KPI del dashboard) usando una window function en vez de un
--    GROUP BY + subquery correlacionada.
SELECT id_variable, descripcion, unidad, fecha, valor
FROM (
    SELECT
        v.id_variable,
        var.descripcion,
        var.unidad,
        v.fecha,
        v.valor,
        ROW_NUMBER() OVER (PARTITION BY v.id_variable ORDER BY v.fecha DESC) AS rn
    FROM valores v
    JOIN variables var ON var.id_variable = v.id_variable
) ranked
WHERE rn = 1;
