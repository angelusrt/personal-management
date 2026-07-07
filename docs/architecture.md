# Arquitetura

> TODO: Desenhar diagrama de arquitetura

A atual arquitetura consiste em um Data Lakehouse com: On Premise + GCS + BigQuery.

Com essa arquitetura, conseguimos usar o 'external tables' do GCP para fazer 
consultas direto nos arquivos - desacoplando ingestão de transformação. 

