-- db: personal

SELECT
	* 
FROM raw.notas_tarefas 
LIMIT 1000
;

SELECT  
	data_referencia,
	categoria,
	descricao
FROM raw.notas_tarefas 
WHERE foi_feito = TRUE 
LIMIT 1000
;

---

SELECT  
	data_referencia,
	descricao
FROM raw.notas_nutricao 
WHERE foi_feito = TRUE 
ORDER BY data_referencia DESC
LIMIT 1000
;
