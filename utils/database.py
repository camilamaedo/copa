import os
import pandas as pd
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 48 países da Copa do Mundo 2026 — PT/EN
TIMES_COPA = sorted([
    "Germany / Alemanha", "Argentina / Argentina", "Australia / Austrália",
    "Algeria / Argélia", "Austria / Áustria", "Saudi Arabia / Arábia Saudita",
    "Belgium / Bélgica", "Brazil / Brasil", "Canada / Canadá",
    "Cape Verde / Cabo Verde", "Colombia / Colômbia", "South Korea / Coreia do Sul",
    "Croatia / Croácia", "Curacao / Curaçao", "DR Congo / Congo RD",
    "Ecuador / Equador", "Egypt / Egito", "Scotland / Escócia",
    "Spain / Espanha", "USA / EUA", "France / França",
    "Ghana / Gana", "Haiti / Haiti", "Netherlands / Holanda",
    "England / Inglaterra", "Iran / Irã", "Iraq / Iraque",
    "Ivory Coast / Costa do Marfim", "Japan / Japão", "Jordan / Jordânia",
    "Morocco / Marrocos", "Mexico / México", "New Zealand / Nova Zelândia",
    "Norway / Noruega", "Panama / Panamá", "Paraguay / Paraguai",
    "Portugal / Portugal", "Qatar / Qatar", "Czech Republic / República Tcheca",
    "Senegal / Senegal", "Switzerland / Suíça", "Sweden / Suécia",
    "South Africa / África do Sul", "Tunisia / Tunísia", "Turkey / Turquia",
    "Uruguay / Uruguai", "Uzbekistan / Uzbequistão",
    "Bosnia and Herzegovina / Bósnia e Herzegovina",
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
