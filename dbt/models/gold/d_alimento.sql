WITH base AS (
    SELECT
        alimento,
        unidade,
        COUNT(*) AS quantidade
    FROM {{ source('bronze', 'raw_notas_nutricao_enriquecida') }}
    GROUP BY alimento, unidade
	{% if is_incremental() %}
		WHERE NOT EXISTS (
			SELECT 1
			FROM {{ this }} t
			WHERE t.nome_alimento = s.alimento
		)
    {% endif %}
),
canonical_form AS (
    SELECT
        alimento,
        unidade
    FROM (
        SELECT
            b.*,
            ROW_NUMBER() OVER (
                PARTITION BY b.alimento
                ORDER BY b.quantidade DESC
            ) AS rn
        FROM base b
    )
    WHERE rn = 1
)
SELECT
    FARM_FINGERPRINT(alimento) AS id_alimento,
    alimento AS nome_alimento,
    unidade AS unidade_de_medida,
    CASE
        WHEN unidade IN ('unidade', 'hora', 'fatia') THEN 1
        WHEN unidade IN ('grama', 'mililitro') THEN 100
        ELSE NULL
    END AS quantidade_referencia,
    'PENDENTE' AS status,
    CAST(NULL AS STRING) AS categoria_alimento,
    CAST(NULL AS STRING) AS fonte,
    CAST(NULL AS STRING) AS imprecisao,
    CAST(NULL AS INT64) AS proteina,
    CAST(NULL AS INT64) AS gordura,
    CAST(NULL AS INT64) AS carboidrato,
    CAST(NULL AS INT64) AS caloria
FROM canonical_form
