import sys
sys.path.append("/opt/airflow")

import os
import io
import pendulum
from pathlib import Path
from datetime import datetime

import pandas as pd
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.decorators import dag, task

from scripts import utils, parser_notes

PROJECT_ID = os.getenv("DBT_GCP_PROJECT_NAME")
INGESTION_BUCKET = os.getenv("GCP_INGESTION_BUCKET")
DATASET = "bronze"

@task
def extract_notes():
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

    hook = GCSHook(gcp_conn_id="GOOGLE_CLOUD_DEFAULT")
    #run_ts = pendulum.now("UTC").format("YYYYMMDDTHHmmss")

    for table, df in tables.items():
        if df.empty:
            print(f"Skipping {table}: no rows parsed this run")
            continue

        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        buffer.seek(0)

        object_name = f"{table}/main.parquet"

        hook.upload(
            bucket_name=INGESTION_BUCKET,
            object_name=object_name,
            data=buffer.getvalue(),
            mime_type="application/octet-stream",
        )

        print(f"Uploaded {len(df)} rows to gs://{INGESTION_BUCKET}/{object_name}")


@dag(
    schedule=None,
    start_date=datetime(2026, 5, 23),
    catchup=False,
    tags=["notes", "ingestion"],
)
def ingest_notes():
    extract_task = extract_notes()

    extract_task


ingest_notes()
