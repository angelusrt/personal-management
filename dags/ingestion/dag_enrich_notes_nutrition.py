import sys
sys.path.append("/opt/airflow")

import os
import io
import pendulum
from datetime import datetime

import pandas as pd
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.decorators import dag, task

INGESTION_BUCKET = os.getenv("GCP_INGESTION_BUCKET")
DATASET = "bronze"

@task
def process_nutrition():
    assert type(INGESTION_BUCKET) is str

    hook = GCSHook(gcp_conn_id="GOOGLE_CLOUD_DEFAULT")

    data = hook.download(
        bucket_name=INGESTION_BUCKET,
        object_name="notas_nutricao/main.parquet",
    )

    df = pd.read_parquet(
        io.BytesIO(data), 
        columns=[
            'nome_arquivo', 
            'ordem', 
            'data_referencia', 
            'foi_feito', 
            'eh_meta',
            'descricao'
       ],
    )

    df = df[df["foi_feito"]][["data_referencia", "eh_meta", "descricao"]]

    # 0. Remove '[]'
    df["descricao"] = df["descricao"].str.replace(r"\[|\]", "", regex=True)

    # 1. Split description by '+' to get each item

    df["itens"] = df["descricao"].str.split("+")
    exploded = df.explode("itens").reset_index(drop=True)
    exploded["itens"] = exploded["itens"].str.strip().fillna("").astype(object)

    # 2. Split it further by 'com' whenever it is followed by a number

    exploded["tem_com_com_digito"] = exploded["itens"].str.contains(r"\s+com\s+\d+", regex=True)

    mask = exploded["tem_com_com_digito"]
    exploded.loc[mask, "itens"] = exploded.loc[mask, "itens"].str.split("com")

    exploded = exploded.explode("itens").reset_index(drop=True)
    exploded["itens"] = exploded["itens"].str.strip()
    
    exploded["tem_com_com_digito"] = exploded["itens"].str.contains(r"\s+com\s+\d+", regex=True)
    exploded = exploded.drop(columns=["tem_com_com_digito"])

    # 3. Divide the text into quantity, unit and food

    full = exploded["itens"].str.extract(
        r"(?P<quantidade>\d+(?:\.\d+)?)\s*"
        r"(?P<unidade>h|g|ml|kg|l|xicara|xicaras|copos|copo|fatias|fatia|scoop)\s+(?:de\s+)?"
        r"(?P<alimento>.+)"
    )

    # 3. Implement fallback for those which do not have an explicit unit

    missing = full["alimento"].isna()
    fallback = exploded.loc[missing, "itens"].str.extract(
        r"(?P<quantidade>\d+(?:\.\d+)?)\s+(?P<alimento>.+)"
    )

    fallback["unidade"] = "un"

    full.loc[missing, ["quantidade", "unidade", "alimento"]] = fallback[
        ["quantidade", "unidade", "alimento"]
    ]

    # 4. Implement fallback for those which do not have an explicit unit and quantity

    missing2 = full["alimento"].isna()

    fallback2 = exploded.loc[missing2, "itens"].str.extract(
        r"(?P<alimento>.+)"
    )
    fallback2["quantidade"] = "1"
    fallback2["unidade"] = "un"

    full.loc[missing2, ["quantidade", "unidade", "alimento"]] = fallback2[
        ["quantidade", "unidade", "alimento"]
    ]

    # 5. Fin

    result = pd.concat([exploded, full], axis=1)
    result = result.drop(columns=["descricao", "itens"])

    run_ts = pendulum.now("UTC").format("YYYYMMDDTHHmmss")

    buffer = io.BytesIO()
    result.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    object_name = f"notas_nutricao_enriquecida/{run_ts}.parquet"

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
    tags=["notes", "enrichment"],
)
def enrich_nutrition():
    process_nutrition()


enrich_nutrition()
