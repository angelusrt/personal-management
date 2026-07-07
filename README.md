# Gerenciamento de Dados Pessoais

Nesse projeto, eu construo uma infraestrutura de dados Airflow + DBT + Docker
para organizar meus dados pessoais e gerar insights sobre comportamentos e práticas.

> TODO: fazer banco do Airflow ser persistente

## Build

Para provisionar o BigQuery, necessitarás ir na pasta 
'terraform/modules/bigquery' e rodar:

```{bash}
terraform plan
terraform apply
```

E, então, criar um arquivo '.env' com as seguintes variáveis:
- BQ_CREDENTIAL_FILE
- GOOGLE_APPLICATION_CREDENTIALS
- AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT
- NOTES_FOLDER
- DBT_BIGQUERY_DATASET_NAME
- DBT_BIGQUERY_KEYPATH
- DBT_GCP_PROJECT_NAM
- DBT_GCP_BIGQUERY_LOCATION

Finalmente, rodar o container:

```{bash}
docker compose up
```

Para conseguir a senha admin, rode o comando 
(é necessário esperar um pouco):

```{bash}
docker compose logs
```

## Syntax Highlight

```{bash}
python3 -m venv .venv

source .venv/bin/activate

pip install apache-airflow

pip install -r requirements.txt
```
