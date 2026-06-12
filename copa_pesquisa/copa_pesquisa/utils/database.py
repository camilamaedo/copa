import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "apostas.db"

TIMES = [
    "Brasil", "Argentina", "França", "Alemanha", "Espanha",
    "Inglaterra", "Portugal", "Holanda", "Itália", "Uruguai",
    "Colômbia", "México", "EUA", "Japão", "Marrocos", "Outro"
]

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def criar_tabela():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS apostas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nome        TEXT,
                pais_origem TEXT,
                campeao     TEXT NOT NULL,
                vice        TEXT,
                artilheiro  TEXT,
                comentario  TEXT,
                criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def salvar_aposta(nome, pais_origem, campeao, vice, artilheiro, comentario):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO apostas (nome, pais_origem, campeao, vice, artilheiro, comentario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, pais_origem, campeao, vice, artilheiro, comentario))
        conn.commit()

def carregar_apostas() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM apostas ORDER BY criado_em DESC", conn)

def total_respostas() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM apostas").fetchone()[0]
