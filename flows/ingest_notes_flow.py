import duckdb
from pathlib import Path
from prefect import flow, task
from scripts import utils, parser_notes

DB_PATH = "warehouse/life.duckdb"
NOTES_PATH = "notes"

@task
def create_tables():
    conn = duckdb.connect(utils.DB_PATH)

    conn.execute("""CREATE SCHEMA IF NOT EXISTS raw""")

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

    conn.commit()
    conn.close()


@task
def ingest_notes():
    conn = duckdb.connect(utils.DB_PATH)
    note_paths = Path(utils.NOTES_PATH).glob("*.md")

    try:
        for note_path in note_paths:
            print(f"Extraindo {note_path.name}...")

            try:
                note = parser_notes.parse(note_path)
            except Exception as e:
                print(e)
                continue

            for key, value in note.labels.items():
                conn.execute("""
                    INSERT INTO raw.notas_atributos (
                        nome_arquivo,
                        tipo,
                        data_referencia,
                        valor
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(nome_arquivo, tipo)
                    DO UPDATE SET
                        valor = excluded.valor,
                        data_referencia = excluded.data_referencia,
                        data_extracao = CURRENT_TIMESTAMP
                """, [
                    note_path.name,
                    key,
                    note.date,
                    value,
                ])

            for n, task in enumerate(note.tasks):
                conn.execute("""
                    INSERT INTO raw.notas_tarefas (
                        nome_arquivo,
                        ordem,
                        data_referencia,
                        foi_feito,
                        categoria,
                        descricao,
                        quantidade_esforco
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(nome_arquivo, ordem)
                    DO UPDATE SET
                        data_referencia = excluded.data_referencia,
                        foi_feito = excluded.foi_feito,
                        categoria = excluded.categoria,
                        descricao = excluded.descricao,
                        quantidade_esforco = excluded.quantidade_esforco,
                        data_extracao = CURRENT_TIMESTAMP
                """, [
                    note_path.name,
                    n,
                    note.date,
                    task.is_done,
                    task.category,
                    task.description,
                    task.effort
                ])

            for n, nutri in enumerate(note.nutri):
                conn.execute("""
                    INSERT INTO raw.notas_nutricao (
                        nome_arquivo,
                        ordem,
                        data_referencia,
                        foi_feito,
                        eh_meta,
                        descricao
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(nome_arquivo, ordem)
                    DO UPDATE SET
                        data_referencia = excluded.data_referencia,
                        foi_feito = excluded.foi_feito,
                        eh_meta = excluded.eh_meta,
                        descricao = excluded.descricao,
                        data_extracao = CURRENT_TIMESTAMP
                """, [
                    note_path.name,
                    n,
                    note.date,
                    nutri.is_done,
                    nutri.is_meta,
                    nutri.description,
                ])

            conn.execute("""
                INSERT INTO raw.notas_introspeccao (
                    nome_arquivo,
                    data_referencia,
                    descricao
                )
                VALUES (?, ?, ?)
                ON CONFLICT(nome_arquivo)
                DO UPDATE SET
                    data_referencia = excluded.data_referencia,
                    descricao = excluded.descricao,
                    data_extracao = CURRENT_TIMESTAMP
            """, [
                note_path.name,
                note.date,
                note.introspection,
            ])
    except Exception as e:
        print(e)
    finally:
        conn.commit()
        conn.close()


@flow
def ingest_notes_flow():
    create_tables()
    ingest_notes()

    utils.transform_with_dbt([
        "stg_notas_tarefas",
        "notas_tarefas",
    ])


ingest_notes_flow()
