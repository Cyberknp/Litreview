import os 

import psycopg
from psycopg.rows import dict_row

DATABASE_URL=os.environ.get("DATABASE_URL", "postgresql://rag_user:local_dev_password@localhost:5433/papers_db")

def get_connection():
    return psycopg.connect(DATABASE_URL,row_factory=dict_row)

def initialize_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    year INTEGER NOT NULL
                )
            """)
            cur.executemany(
                """
                INSERT INTO papers (id, title, year)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, year = EXCLUDED.year
                """,
                [
                    (
                        1,
                        "Large Language Models in Medical Diagnosis",
                        2025,
                    ),
                    (
                        2,
                        "Retrieval-Augmented Generation (RAG) for Research",
                        2024,
                    ),
                    (
                        3,
                        "Deep Learning for Medical Image Analysis",
                        2023,
                    ),
                    (
                        4,
                        "RAG Systems for Scientific Discovery",
                        2025,
                    ),
                ],
            )

