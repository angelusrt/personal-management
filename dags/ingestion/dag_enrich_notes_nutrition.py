import sys
sys.path.append("/opt/airflow")

import io
from datetime import datetime

import pandas as pd
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from airflow.decorators import dag, task

from scripts import utils


@task
def process_nutrition():
    assert type(utils.INGESTION_BUCKET) is str

    hook = GCSHook(gcp_conn_id="GOOGLE_CLOUD_DEFAULT")

    data = hook.download(
        bucket_name=utils.INGESTION_BUCKET,
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

    # 1. Convert plural to singular

    repmap = {
        "aes$": "ao",
        "oes$": "ao",
        "ens$": "em",
        "ies$": "ie",
        "eis$": "el",
        "ps$": "p",
        "as$": "a",
        "os$": "o",
        "es$": "e",

        "aes ": "ao ",
        "oes ": "ao ",
        "ens ": "em ",
        "ies ": "ie ",
        "eis ": "el ",
        "ps ": "p ",
        "as ": "a ",
        "os ": "o ",
        "es ": "e ",
    }

    df["descricao"] = df["descricao"].replace(repmap, regex=True)

    # 2. Split description by '+' to get each item

    df["itens"] = df["descricao"].str.split("+")
    exploded = df.explode("itens").reset_index(drop=True)
    exploded["itens"] = exploded["itens"].str.strip().fillna("").astype(object)

    # 3. Split it further by 'com' whenever it is followed by a number

    exploded["tem_com_com_digito"] = exploded["itens"].str.contains(r"\s+com\s+\d+", regex=True)

    mask = exploded["tem_com_com_digito"]
    exploded.loc[mask, "itens"] = exploded.loc[mask, "itens"].str.split("com")

    exploded = exploded.explode("itens").reset_index(drop=True)
    exploded["itens"] = exploded["itens"].str.strip()

    # 4. Divide the text into quantity, unit and food

    full = exploded["itens"].str.extract(
        r"(?P<quantidade>\d+(?:\.\d+)?)\s*"
        r"(?P<unidade>h|min|g|ml|kg|l|xicara|copo|fatia|scoop|pratinho|prato)\s+(?:de|com)?\s*"
        r"(?P<alimento>.+)"
    )

    # 5. Implement fallback for those which do not have an explicit unit

    missing = full["alimento"].isna()
    fallback = exploded.loc[missing, "itens"].str.extract(
        r"(?P<quantidade>\d+(?:\.\d+)?)\s+(?P<alimento>.+)"
    )

    fallback["unidade"] = "un"

    full.loc[missing, ["quantidade", "unidade", "alimento"]] = fallback[
        ["quantidade", "unidade", "alimento"]
    ]

    # 6. Implement fallback for special ones with this format '[food] - [quantity][unit]'

    missing2 = full["alimento"].isna()
    fallback2 = exploded.loc[missing2, "itens"].str.extract(
        r"(?P<alimento>.+)\s*-\s*"
        r"(?P<quantidade>\d+(?:\.\d+)?)\s*"
        r"(?P<unidade>h|min|g|ml|kg|l|xicara|copo|fatia|scoop)?"
    )

    full.loc[missing2, ["quantidade", "unidade", "alimento"]] = fallback2[
        ["quantidade", "unidade", "alimento"]
    ]

    # 7. Implement fallback for those which do not have an explicit unit and quantity

    missing3 = full["alimento"].isna()

    fallback3 = exploded.loc[missing3, "itens"].str.extract(
        r"(?P<alimento>.+)"
    )
    fallback3["quantidade"] = "1"
    fallback3["unidade"] = "un"

    full.loc[missing3, ["quantidade", "unidade", "alimento"]] = fallback3[
        ["quantidade", "unidade", "alimento"]
    ]

    # 8. Convert some units

    mask = full["unidade"].isin(["copo", "xicara"])
    full.loc[mask, "unidade"] = "ml"
    full.loc[mask, "quantidade"] = (full.loc[mask, "quantidade"].astype("int32") * 200).astype("str")

    mask = full["unidade"] == "pratinho"
    full.loc[mask, "unidade"] = "g"
    full.loc[mask, "quantidade"] = (full.loc[mask, "quantidade"].astype("int32") * 250).astype("str")

    mask = full["unidade"] == "prato"
    full.loc[mask, "unidade"] = "g"
    full.loc[mask, "quantidade"] = (full.loc[mask, "quantidade"].astype("int32") * 500).astype("str")

    mask = full["unidade"] == "scoop"
    full.loc[mask, "unidade"] = "g"
    full.loc[mask, "quantidade"] = (full.loc[mask, "quantidade"].astype("int32") * 15).astype("str")

    mask = full["unidade"] == "min"
    full.loc[mask, "unidade"] = "h"
    full.loc[mask, "quantidade"] = (
        full.loc[mask, "quantidade"]
        .astype(float)
        .div(60)
        .map("{:.2f}".format)
    )

    # 10. Normalize units

    units_map = {
        "h": "hora",
        "g": "grama",
        "ml": "mililitro",
        "un": "unidade",
    }

    full["unidade"] = full["unidade"].replace(units_map, regex=True)

    # 11. Fin

    full["quantidade"] = full["quantidade"].astype(float)
    full["alimento"] = full["alimento"].str.strip()
    result = pd.concat([exploded, full], axis=1)
    result = result.drop(columns=["descricao", "itens"])

    # Uploading

    buffer = io.BytesIO()
    result.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    object_name = "notas_nutricao_enriquecida/main.parquet"

    hook.upload(
        bucket_name=utils.INGESTION_BUCKET,
        object_name=object_name,
        data=buffer.getvalue(),
        mime_type="application/octet-stream",
    )

    print(f"Uploaded {len(df)} rows to gs://{utils.INGESTION_BUCKET}/{object_name}")


@dag(
    schedule=None,
    start_date=datetime(2026, 5, 23),
    catchup=False,
    tags=["notes", "enrichment"],
)
def enrich_nutrition():
    process_nutrition()


enrich_nutrition()
