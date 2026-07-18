SELECT 
	*
FROM (
    SELECT
        data_referencia,
        tipo,
        valor
    FROM {{ source('bronze', 'raw_notas_atributos') }}
)
PIVOT (
    MAX(valor)
    FOR tipo IN ('peso', 'satisfacao')
)
