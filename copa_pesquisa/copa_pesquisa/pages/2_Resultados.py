import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import criar_tabela, carregar_apostas, total_respostas

st.set_page_config(page_title="Resultados da pesquisa", page_icon="📊", layout="wide")

criar_tabela()

st.title("📊 Resultados da pesquisa")

total = total_respostas()
if total == 0:
    st.warning("Ainda não há respostas. Seja o primeiro a apostar!")
    st.page_link("pages/1_Apostar.py", label="Ir para o formulário →")
    st.stop()

df = carregar_apostas()

# --- métricas no topo ---
col1, col2, col3 = st.columns(3)
col1.metric("Total de respostas", total)
col2.metric("Favorito da vez", df["campeao"].mode()[0])
col3.metric("Países representados", df["pais_origem"].dropna().nunique())

st.divider()

# --- campeão mais votado ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 Quem vai ser campeão?")
    campeao_counts = (
        df["campeao"]
        .value_counts()
        .reset_index()
        .rename(columns={"campeao": "Time", "count": "Votos"})
    )
    fig1 = px.bar(
        campeao_counts,
        x="Votos", y="Time",
        orientation="h",
        color="Votos",
        color_continuous_scale="Teal",
        text="Votos"
    )
    fig1.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    fig1.update_traces(textposition="outside")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.subheader("🥧 Distribuição dos votos")
    fig2 = px.pie(
        campeao_counts,
        names="Time",
        values="Votos",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- de onde vieram os votos ---
st.subheader("🌎 De onde são os participantes?")
pais_counts = (
    df["pais_origem"]
    .dropna()
    .value_counts()
    .reset_index()
    .rename(columns={"pais_origem": "País", "count": "Respostas"})
)
if not pais_counts.empty:
    fig3 = px.bar(
        pais_counts,
        x="País", y="Respostas",
        color="Respostas",
        color_continuous_scale="Blues",
        text="Respostas"
    )
    fig3.update_layout(coloraxis_showscale=False)
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Nenhum participante informou o país de origem.")

st.divider()

# --- artilheiros mais citados ---
st.subheader("⚽ Artilheiros mais citados")
artilheiros = (
    df["artilheiro"]
    .dropna()
    .str.strip()
    .loc[lambda s: s != ""]
    .value_counts()
    .head(10)
    .reset_index()
    .rename(columns={"artilheiro": "Jogador", "count": "Citações"})
)
if not artilheiros.empty:
    st.dataframe(artilheiros, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum artilheiro informado ainda.")

st.divider()

# --- respostas ao longo do tempo ---
st.subheader("📅 Respostas ao longo do tempo")
df["criado_em"] = pd.to_datetime(df["criado_em"])
por_dia = df.resample("D", on="criado_em").size().reset_index(name="Respostas")
fig4 = px.line(por_dia, x="criado_em", y="Respostas", markers=True)
fig4.update_layout(xaxis_title="Data", yaxis_title="Respostas por dia")
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# --- exportar dados ---
st.subheader("⬇️ Exportar dados")
col_x, col_y = st.columns(2)

with col_x:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Baixar CSV", csv, "apostas.csv", "text/csv", use_container_width=True)

with col_y:
    st.download_button(
        "Baixar JSON",
        df.to_json(orient="records", force_ascii=False).encode("utf-8"),
        "apostas.json",
        "application/json",
        use_container_width=True
    )

# --- tabela completa ---
with st.expander("Ver todas as respostas"):
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)
