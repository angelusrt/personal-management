import unicodedata
import subprocess
from prefect import task


DB_PATH = "warehouse/database.duckdb"
NOTES_PATH = "data/notes"


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

