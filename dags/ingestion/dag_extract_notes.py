import sys
sys.path.append("/opt/airflow")

from pathlib import Path
from datetime import datetime

import pandas as pd
from google.cloud import bigquery
from airflow.decorators import dag, task

from scripts import utils, parser_notes

PROJECT_ID = "airflow-bigquery-prod"
DATASET = "raw"

@task
def extract_notes():
    client = bigquery.Client(project=PROJECT_ID)

    atributos = []
    tarefas = []
    nutricao = []
    introspeccao = []

    for note_path in Path(utils.NOTES_PATH).glob("*.md"):
        try:
            note = parser_notes.parse(note_path)
        except Exception as e:
            print(f"Failed parsing {note_path}: {e}")
            continue

        for key, value in note.labels.items():
            atributos.append({
                "nome_arquivo": note_path.name,
                "data_referencia": note.date,
                "tipo": key,
                "valor": value,
            })

        for n, job in enumerate(note.tasks):
            tarefas.append({
                "nome_arquivo": note_path.name,
                "ordem": n,
                "data_referencia": note.date,
                "foi_feito": job.is_done,
                "categoria": job.category,
                "descricao": job.description,
                "quantidade_esforco": job.effort,
            })

        for n, nutri in enumerate(note.nutri):
            nutricao.append({
                "nome_arquivo": note_path.name,
                "ordem": n,
                "data_referencia": note.date,
                "foi_feito": nutri.is_done,
                "eh_meta": nutri.is_meta,
                "descricao": nutri.description,
            })

        introspeccao.append({
            "nome_arquivo": note_path.name,
            "data_referencia": note.date,
            "descricao": note.introspection,
        })

    tables = {
        "notas_atributos": pd.DataFrame(atributos),
        "notas_tarefas": pd.DataFrame(tarefas),
        "notas_nutricao": pd.DataFrame(nutricao),
        "notas_introspeccao": pd.DataFrame(introspeccao),
    }

    for table, df in tables.items():
        table_id = f"{PROJECT_ID}.{DATASET}.{table}"

        client.query(f"TRUNCATE TABLE `{table_id}`").result()

        job = client.load_table_from_dataframe(df, table_id)
        job.result()

        print(f"Loaded {len(df)} rows into {table}")


@task
def run_dbt():
    import subprocess

    subprocess.run(
        ["dbt", "build", "--select", "stg_notas_tarefas notas_tarefas"],
        check=True,
        cwd="/opt/airflow/dbt"
    )


@dag(
    schedule=None,
    start_date=datetime(2026, 5, 23),
    catchup=False,
    tags=["notes", "ingestion"],
)
def ingest_notes():
    extract_task = extract_notes()
    dbt_task = run_dbt()

    extract_task >> dbt_task


ingest_notes()
