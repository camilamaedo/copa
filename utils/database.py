import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# Lê a URL do ambiente (configurada no Streamlit Cloud)
DATABASE_URL = os.environ.get("DATABASE_URL")

# 32 países da Copa do Mundo 2026 — PT/EN
TIMES_COPA = sorted([
    "Germany / Alemanha",
    "Argentina / Argentina",
    "Australia / Austrália",
    "Belgium / Bélgica",
    "Brazil / Brasil",
    "Canada / Canadá",
    "Croatia / Croácia",
    "Denmark / Dinamarca",
    "Egypt / Egito",
    "Ecuador / Equador",
    "Spain / Espanha",
    "USA / EUA",
    "France / França",
    "Netherlands / Holanda",
    "England / Inglaterra",
    "Iran / Irã",
    "Japan / Japão",
    "Morocco / Marrocos",
    "Mexico / México",
    "Nigeria / Nigéria",
    "Norway / Noruega",
    "New Zealand / Nova Zelândia",
    "Poland / Polônia",
    "Portugal / Portugal",
    "Qatar / Qatar",
    "Czech Republic / República Tcheca",
    "Senegal / Senegal",
    "Serbia / Sérvia",
    "Switzerland / Suíça",
    "Turkey / Turquia",
    "Ukraine / Ucrânia",
    "Uruguay / Uruguai",
])

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def criar_tabela():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS apostas (
                    id          SERIAL PRIMARY KEY,
                    nome        TEXT,
                    pais_origem TEXT,
                    campeao     TEXT NOT NULL,
                    vice        TEXT NOT NULL,
                    comentario  TEXT,
                    criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()

def salvar_aposta(nome, pais_origem, campeao, vice, comentario):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO apostas (nome, pais_origem, campeao, vice, comentario)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, pais_origem, campeao, vice, comentario))
        conn.commit()

def carregar_apostas() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql("SELECT * FROM apostas ORDER BY criado_em DESC", conn)

def total_respostas() -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM apostas")
            return cur.fetchone()[0]
