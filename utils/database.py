import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "db" / "apostas.db"

# 32 países da Copa do Mundo 2026
TIMES_COPA = [
    "Argentina", "Austrália", "Bélgica", "Brasil", "Canadá",
    "Croácia", "Dinamarca", "Egito", "Equador", "Espanha",
    "EUA", "França", "Holanda", "Inglaterra", "Irã",
    "Japão", "Marrocos", "México", "Nigéria", "Noruega",
    "Nova Zelândia", "Polônia", "Portugal", "Qatar", "República Tcheca",
    "Senegal", "Sérvia", "Suíça", "Turquia", "Ucrânia",
    "Uruguai", "Alemanha"
]
TIMES_COPA = sorted(TIMES_COPA)

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
                vice        TEXT NOT NULL,
                comentario  TEXT,
                criado_em   DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def salvar_aposta(nome, pais_origem, campeao, vice, comentario):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO apostas (nome, pais_origem, campeao, vice, comentario)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, pais_origem, campeao, vice, comentario))
        conn.commit()

def carregar_apostas() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM apostas ORDER BY criado_em DESC", conn)

def total_respostas() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM apostas").fetchone()[0]
