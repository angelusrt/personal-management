WITH base AS (
	SELECT 
		CAST(data_referencia AS INT64) AS data_referencia,
		idade,
		peso,
		altura,
		caloria_basal
	FROM {{ source('bronze', 'raw_notas_atributos_enriquecido') }}
), exercises AS (
	SELECT
		data_referencia,
		ABS(SUM(caloria)) AS caloria_exercicio
	FROM {{ ref('f_dieta_diaria') }}
	WHERE caloria < 0
	GROUP BY 1
), gym AS (
	SELECT
		data_referencia,
		SUM(quantidade) AS horas_academia,
	FROM {{ ref('f_dieta_diaria') }}
	WHERE id_alimento = 6797609047196057310
	GROUP BY 1
), consumed AS (
	SELECT
		data_referencia,
		ABS(SUM(caloria)) AS caloria_consumida,
		ABS(SUM(proteina)) AS proteina_consumida
	FROM {{ ref('f_dieta_diaria') }}
	WHERE caloria > 0
	GROUP BY 1
)
SELECT 
	b.data_referencia,
	b.idade,
	ROUND(b.peso, 2) AS peso,
	b.altura,
	ROUND(b.caloria_basal, 2) AS caloria_basal,
	ROUND(COALESCE(c.caloria_consumida, 0), 2) AS caloria_consumida,
	ROUND(b.caloria_basal + COALESCE(e.caloria_exercicio, 0), 2) AS caloria_total,
	ROUND(COALESCE(c.caloria_consumida, 0) - (b.caloria_basal + COALESCE(e.caloria_exercicio, 0)), 2) AS caloria_superavit,
	ROUND(g.horas_academia, 2) AS horas_academia,
	ROUND(COALESCE(c.proteina_consumida, 0), 2) AS proteina_consumida,
	ROUND(b.peso * 1.8, 2) AS meta_proteina
FROM base b
LEFT JOIN exercises e ON 
	e.data_referencia = b.data_referencia
LEFT JOIN consumed c ON 
	c.data_referencia = b.data_referencia
LEFT JOIN gym g ON 
	g.data_referencia = b.data_referencia
