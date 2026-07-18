{{ config(
    materialized = 'table'
) }}

WITH calendario AS (
    SELECT
        data
    FROM UNNEST(
        GENERATE_DATE_ARRAY(
            DATE('2000-01-01'),
            DATE('2050-12-31'),
            INTERVAL 1 DAY
        )
    ) AS data
)

SELECT
    CAST(FORMAT_DATE('%Y%m%d', data) AS INT64) AS id_calendario,
    data,
    EXTRACT(DAY FROM data) AS dia,
    EXTRACT(MONTH FROM data) AS mes,
    FORMAT_DATE('%B', data) AS mes_nome,
    EXTRACT(YEAR FROM data) AS ano,
    EXTRACT(ISOWEEK FROM data) AS semana_do_ano,
    EXTRACT(QUARTER FROM data) AS trimestre,
    EXTRACT(DAYOFWEEK FROM data) BETWEEN 2 AND 6 AS eh_semana_util
FROM calendario
ORDER BY data
