{{ config(
    materialized='incremental',
    unique_key=['nome_alimento', 'unidade_observada']
) }}

WITH base AS (
    SELECT
        alimento,
        unidade,
        COUNT(*) AS quantidade
    FROM {{ source('bronze', 'raw_notas_nutricao_enriquecida') }}
    GROUP BY alimento, unidade
), ranked AS (
    SELECT
        alimento,
        unidade,
        quantidade,
        ROW_NUMBER() OVER (
            PARTITION BY alimento
            ORDER BY quantidade DESC
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY alimento
        ) AS n_unidades
    FROM base
)

SELECT
    FARM_FINGERPRINT(CONCAT(alimento, '|', unidade)) AS id_alimento_dlq,
    alimento AS nome_alimento,
    unidade AS unidade_observada,
    quantidade,
    'Unidade Alternativa' AS motivo,
    CURRENT_TIMESTAMP() AS created_at
FROM ranked
WHERE
    n_unidades > 1
    AND rn > 1

{% if is_incremental() %}
AND NOT EXISTS (
    SELECT 1
    FROM {{ this }} d
    WHERE d.nome_alimento = ranked.alimento
      AND d.unidade_observada = ranked.unidade
)
{% endif %}
