import os

import uuid
import unicodedata
import subprocess
from airflow.decorators import task
from google.cloud import bigquery



INGESTION_BUCKET = os.getenv("GCP_INGESTION_BUCKET")
PROJECT_ID = os.getenv("GCP_PROJECT_NAME")
INGESTION_BUCKET = os.getenv("GCP_INGESTION_BUCKET")

DB_PATH = "warehouse/database.duckdb"
NOTES_PATH = "data/notes/"


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)

    return "".join(
        c for c in normalized
        if not unicodedata.combining(c)
    )


@task
def transform_with_dbt(models: list[str]):
    command = ["dbt", "run"]

    if models: 
        command.extend(["--select", *models])

    result = subprocess.run(
        command,
        cwd="dbt/",
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        raise Exception(result.stderr)


def merge_dataframe(
    client: bigquery.Client,
    dataframe,
    table: str,
    key_columns: list[str],
):
    """
    Performs an UPSERT (MERGE) from a pandas DataFrame into a BigQuery table.

    Parameters
    ----------
    client
        BigQuery client.
    dataframe
        pandas DataFrame.
    table
        Target table in the format 'dataset.table' or
        'project.dataset.table'.
    key_columns
        List of columns that uniquely identify a row.
    """

    if dataframe.empty:
        return

    if table.count(".") == 1:
        project = client.project
        dataset, target = table.split(".")
    elif table.count(".") == 2:
        project, dataset, target = table.split(".")
    else:
        raise ValueError(f"Invalid table name: {table}")

    temp_table = (
        f"{project}.{dataset}._tmp_{target}_{uuid.uuid4().hex[:8]}"
    )

    client.load_table_from_dataframe(
        dataframe,
        temp_table,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
        ),
    ).result()

    columns = dataframe.columns.tolist()

    on_clause = " AND ".join(
        f"T.{c} = S.{c}"
        for c in key_columns
    )

    update_clause = ",\n        ".join(
        f"{c} = S.{c}"
        for c in columns
        if c not in key_columns
    )

    insert_columns = ", ".join(columns)
    insert_values = ", ".join(f"S.{c}" for c in columns)

    sql = f"""
    MERGE `{project}.{dataset}.{target}` T
    USING `{temp_table}` S
    ON {on_clause}

    WHEN MATCHED THEN
        UPDATE SET
        {update_clause}

    WHEN NOT MATCHED THEN
        INSERT ({insert_columns})
        VALUES ({insert_values})
    """

    try:
        client.query(sql).result()
    finally:
        client.delete_table(temp_table, not_found_ok=True)
