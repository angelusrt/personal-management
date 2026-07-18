WITH base AS (
	SELECT 
		CAST(REPLACE(data_referencia, '-', '') AS INT64) AS data_referencia,
		eh_meta, 
		CAST(quantidade AS FLOAT64) AS quantidade, 
		unidade, 
		alimento
	FROM {{ source('bronze', 'raw_notas_nutricao_enriquecida')}}
), enrich AS (
	SELECT
		data_referencia,
		a.id_alimento,
		b.quantidade,
		a.proteina * (CAST(b.quantidade AS FLOAT64)/a.quantidade_referencia) AS proteina,
		a.gordura * (CAST(b.quantidade AS FLOAT64)/a.quantidade_referencia) AS gordura,
		a.carboidrato * (CAST(b.quantidade AS FLOAT64)/a.quantidade_referencia) AS carboidrato,
		a.caloria * (CAST(b.quantidade AS FLOAT64)/a.quantidade_referencia) AS caloria
	FROM base b
	LEFT JOIN {{ ref('d_alimento') }} a ON a.nome_alimento = b.alimento AND a.unidade_de_medida = b.unidade
)
SELECT * FROM enrich
