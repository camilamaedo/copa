import os
import pandas as pd
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 32 países da Copa do Mundo 2026 — PT/EN
TIMES_COPA = sorted([
    "Germany / Alemanha", "Argentina / Argentina", "Australia / Austrália",
    "Belgium / Bélgica", "Brazil / Brasil", "Canada / Canadá",
    "Croatia / Croácia", "Denmark / Dinamarca", "Egypt / Egito",
    "Ecuador / Equador", "Spain / Espanha", "USA / EUA",
    "France / França", "Netherlands / Holanda", "England / Inglaterra",
    "Iran / Irã", "Japan / Japão", "Morocco / Marrocos",
    "Mexico / México", "Nigeria / Nigéria", "Norway / Noruega",
    "New Zealand / Nova Zelândia", "Poland / Polônia", "Portugal / Portugal",
    "Qatar / Qatar", "Czech Republic / República Tcheca", "Senegal / Senegal",
    "Serbia / Sérvia", "Switzerland / Suíça", "Turkey / Turquia",
    "Ukraine / Ucrânia", "Uruguay / Uruguai",
])

def get_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def criar_tabela():
    # A tabela é criada direto no Supabase — nada a fazer aqui
    pass

def salvar_aposta(nome, pais_origem, campeao, vice, comentario):
    client = get_client()
    client.table("apostas").insert({
        "nome": nome,
        "pais_origem": pais_origem,
        "campeao": campeao,
        "vice": vice,
        "comentario": comentario,
    }).execute()

def carregar_apostas() -> pd.DataFrame:
    client = get_client()
    response = client.table("apostas").select("*").order("criado_em", desc=True).execute()
    return pd.DataFrame(response.data)

def total_respostas() -> int:
    client = get_client()
    response = client.table("apostas").select("*", count="exact").execute()
    return response.count or 0
