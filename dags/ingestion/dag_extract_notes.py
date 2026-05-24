import sys
sys.path.append("/opt/airflow")

import duckdb
from pathlib import Path
from airflow.decorators import dag, task
from scripts import utils, parser_notes
from datetime import datetime


@task
def create_tables():
    conn = duckdb.connect(utils.DB_PATH)
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.notas_atributos (
            nome_arquivo TEXT,
            data_referencia DATE,
            tipo TEXT,
            valor TEXT,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (nome_arquivo, tipo)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.notas_tarefas (
            nome_arquivo TEXT,
            ordem INTEGER,
            data_referencia DATE,
            foi_feito BOOLEAN,
            categoria TEXT,
            descricao TEXT,
            quantidade_esforco INTEGER,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (nome_arquivo, ordem)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.notas_nutricao (
            nome_arquivo TEXT,
            ordem INTEGER,
            data_referencia DATE,
            foi_feito BOOLEAN,
            eh_meta BOOLEAN,
            descricao TEXT,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (nome_arquivo, ordem)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw.notas_introspeccao (
            nome_arquivo TEXT PRIMARY KEY,
            data_referencia DATE,
            descricao TEXT,
            data_extracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.close()


@task
def extract_notes():
    conn = duckdb.connect(utils.DB_PATH)
    note_paths = list(Path(utils.NOTES_PATH).glob("*.md"))

    print(utils.NOTES_PATH)
    print(note_paths)

    for note_path in note_paths:
        try:
            note = parser_notes.parse(note_path)
        except Exception as e:
            print(f"Failed parsing {note_path}: {e}")
            continue

        for key, value in note.labels.items():
            conn.execute("""
                INSERT INTO raw.notas_atributos (
                    nome_arquivo, tipo, data_referencia, valor
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(nome_arquivo, tipo)
                DO UPDATE SET
                    valor = excluded.valor,
                    data_referencia = excluded.data_referencia,
                    data_extracao = NOW()
            """, [note_path.name, key, note.date, value])

        for n, task in enumerate(note.tasks):
            conn.execute("""
                INSERT INTO raw.notas_tarefas (
                    nome_arquivo, ordem, data_referencia,
                    foi_feito, categoria, descricao, quantidade_esforco
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(nome_arquivo, ordem)
                DO UPDATE SET
                    data_referencia = excluded.data_referencia,
                    foi_feito = excluded.foi_feito,
                    categoria = excluded.categoria,
                    descricao = excluded.descricao,
                    quantidade_esforco = excluded.quantidade_esforco,
                    data_extracao = NOW()
            """, [
                note_path.name, n, note.date,
                task.is_done, task.category, task.description, task.effort
            ])

        for n, nutri in enumerate(note.nutri):
            conn.execute("""
                INSERT INTO raw.notas_nutricao (
                    nome_arquivo, ordem, data_referencia,
                    foi_feito, eh_meta, descricao
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(nome_arquivo, ordem)
                DO UPDATE SET
                    data_referencia = excluded.data_referencia,
                    foi_feito = excluded.foi_feito,
                    eh_meta = excluded.eh_meta,
                    descricao = excluded.descricao,
                    data_extracao = NOW()
            """, [
                note_path.name, n, note.date,
                nutri.is_done, nutri.is_meta, nutri.description
            ])

        conn.execute("""
            INSERT INTO raw.notas_introspeccao (
                nome_arquivo, data_referencia, descricao
            )
            VALUES (?, ?, ?)
            ON CONFLICT(nome_arquivo)
            DO UPDATE SET
                data_referencia = excluded.data_referencia,
                descricao = excluded.descricao,
                data_extracao = NOW()
        """, [
            note_path.name, note.date, note.introspection
        ])

    conn.commit()
    conn.close()


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
    tags=["notes", "ingestion"]
)
def ingest_notes():
    create_tables_task = create_tables()
    extract_task = extract_notes()
    dbt_task = run_dbt()

    create_tables_task >> extract_task >> dbt_task


ingest_notes()
