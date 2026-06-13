import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.database import criar_tabela, salvar_aposta, carregar_apostas, total_respostas, TIMES_COPA

st.set_page_config(
    page_title="World Cup 2026 Research / Pesquisa Copa 2026",
    page_icon="⚽",
    layout="centered"
)

criar_tabela()

st.title("⚽ World Cup 2026 — Research / Pesquisa")

aba_aposta, aba_resultados, aba_prob = st.tabs([
    "🗳️ Bet / Apostar",
    "📊 Results / Resultados",
    "🔮 Probability / Probabilidade"
])

# ─────────────────────────────────────────
# ABA 1 — FORMULÁRIO
# ─────────────────────────────────────────
with aba_aposta:
    st.markdown("""
    **EN** — Welcome! This is a non-profit research to understand what people think will happen at the 2026 World Cup. Your data is used for academic analysis only.

    **PT** — Bem-vindo! Esta é uma pesquisa sem fins lucrativos para entender o que as pessoas acham que vai acontecer na Copa do Mundo 2026. Seus dados são usados apenas para análise acadêmica.
    """)

    st.metric("Responses / Respostas", total_respostas())
    st.divider()

    with st.form("form_aposta", clear_on_submit=True):
        st.subheader("About you / Sobre você")
        nome = st.text_input("Name or nickname / Nome ou apelido", placeholder="Anonymous / Anônimo")
        pais_origem = st.selectbox(
            "Where are you from? / De onde você é?",
            ["— select / selecione —"] + TIMES_COPA + ["Other / Outro"]
        )

        st.divider()
        st.subheader("Your bets / Suas apostas")
        campeao = st.selectbox(
            "🏆 Who will be the champion? / Quem vai ser campeão?",
            ["— select / selecione —"] + TIMES_COPA
        )
        vice_opcoes = [t for t in TIMES_COPA if t != campeao]
        vice = st.selectbox(
            "🥈 Who will be the runner-up? / Quem vai ser vice-campeão?",
            ["— select / selecione —"] + vice_opcoes,
            key=f"vice_{campeao}"
        )
        comentario = st.text_area(
            "💬 Any comments? / Algum comentário? (optional / opcional)",
            placeholder="Why do you think so? / Por que você acha isso?",
            max_chars=300
        )
        enviado = st.form_submit_button("Submit / Enviar ✅", use_container_width=True, type="primary")

    if enviado:
        if campeao.startswith("—") or vice.startswith("—"):
            st.error("Please select champion and runner-up. / Por favor selecione campeão e vice.")
        else:
            nome_final = nome.strip() if nome.strip() else "Anonymous"
            pais_final = pais_origem if not pais_origem.startswith("—") else None
            salvar_aposta(nome_final, pais_final, campeao, vice, comentario)
            st.success(f"✅ Bet registered! / Aposta registrada! — **{campeao}** 🏆")
            st.balloons()

# ─────────────────────────────────────────
# ABA 2 — DASHBOARD
# ─────────────────────────────────────────
with aba_resultados:
    st.subheader("📊 Results / Resultados")
    total = total_respostas()

    if total == 0:
        st.warning("No responses yet. Be the first! / Ainda não há respostas. Seja o primeiro!")
        st.stop()

    df = carregar_apostas()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total responses / Respostas", total)
    col2.metric("Favourite / Favorito 🏆", df["campeao"].mode()[0])
    col3.metric("Countries / Países", df["pais_origem"].dropna().nunique())

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Champion votes / Votos campeão")
        campeao_counts = (
            df["campeao"].value_counts().reset_index()
            .rename(columns={"campeao": "Team / Time", "count": "Votes / Votos"})
        )
        fig1 = px.bar(campeao_counts, x="Votes / Votos", y="Team / Time", orientation="h",
                      color="Votes / Votos", color_continuous_scale="Teal", text="Votes / Votos")
        fig1.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.subheader("🥧 Distribution / Distribuição")
        fig2 = px.pie(campeao_counts, names="Team / Time", values="Votes / Votos", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("🌎 Where are participants from? / De onde são os participantes?")
    pais_counts = (
        df["pais_origem"].dropna().str.strip()
        .loc[lambda s: s != ""]
        .value_counts().reset_index()
        .rename(columns={"pais_origem": "Country / País", "count": "Responses / Respostas"})
    )
    if not pais_counts.empty:
        fig3 = px.bar(pais_counts, x="Country / País", y="Responses / Respostas",
                      color="Responses / Respostas", color_continuous_scale="Blues", text="Responses / Respostas")
        fig3.update_layout(coloraxis_showscale=False)
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No location data yet. / Nenhum dado de localização ainda.")

    st.divider()
    st.subheader("📅 Responses over time / Respostas ao longo do tempo")
    df["data"] = pd.to_datetime(df["criado_em"]).dt.date
    por_dia = df.groupby("data").size().reset_index(name="Responses")
    fig4 = px.line(por_dia, x="data", y="Responses", markers=True)
    fig4.update_layout(xaxis_title="Date / Data", yaxis_title="Responses / Respostas")
    st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("⬇️ Export / Exportar dados")
    col_x, col_y = st.columns(2)
    with col_x:
        st.download_button("📄 Download CSV", df.to_csv(index=False).encode("utf-8"),
                           "apostas.csv", "text/csv", use_container_width=True)
    with col_y:
        st.download_button("📋 Download JSON",
                           df.to_json(orient="records", force_ascii=False, date_format="iso").encode("utf-8"),
                           "apostas.json", "application/json", use_container_width=True)

    with st.expander("See all responses / Ver todas as respostas"):
        colunas = [c for c in df.columns if c != "id"]
        st.dataframe(df[colunas], use_container_width=True)

# ─────────────────────────────────────────
# ABA 3 — PROBABILIDADE
# ─────────────────────────────────────────
with aba_prob:
    st.subheader("🔮 Head-to-Head Probability / Probabilidade de Confronto")
    st.markdown("""
    **EN** — Based on historical international matches since 2000, weighted by tournament importance and recency.

    **PT** — Baseado em jogos internacionais desde 2000, com peso por importância do torneio e data do jogo.
    """)

    # Pesos por torneio
    PESOS_TORNEIO = {
        'FIFA World Cup': 5,
        'Copa América': 4,
        'UEFA Euro': 4,
        'African Cup of Nations': 4,
        'AFC Asian Cup': 4,
        'Gold Cup': 3,
        'FIFA World Cup qualification': 3,
        'UEFA Euro qualification': 2,
        'African Cup of Nations qualification': 2,
        'UEFA Nations League': 2,
        'CONCACAF Nations League': 2,
        'Friendly': 1,
    }

    # Mapa PT/EN → nome no dataset
    NOME_DATASET = {
        "Germany / Alemanha": "Germany",
        "Argentina / Argentina": "Argentina",
        "Australia / Austrália": "Australia",
        "Belgium / Bélgica": "Belgium",
        "Brazil / Brasil": "Brazil",
        "Canada / Canadá": "Canada",
        "Croatia / Croácia": "Croatia",
        "Denmark / Dinamarca": "Denmark",
        "Egypt / Egito": "Egypt",
        "Ecuador / Equador": "Ecuador",
        "Spain / Espanha": "Spain",
        "USA / EUA": "United States",
        "France / França": "France",
        "Netherlands / Holanda": "Netherlands",
        "England / Inglaterra": "England",
        "Iran / Irã": "Iran",
        "Japan / Japão": "Japan",
        "Morocco / Marrocos": "Morocco",
        "Mexico / México": "Mexico",
        "Nigeria / Nigéria": "Nigeria",
        "Norway / Noruega": "Norway",
        "New Zealand / Nova Zelândia": "New Zealand",
        "Poland / Polônia": "Poland",
        "Portugal / Portugal": "Portugal",
        "Qatar / Qatar": "Qatar",
        "Czech Republic / República Tcheca": "Czech Republic",
        "Senegal / Senegal": "Senegal",
        "Serbia / Sérvia": "Serbia",
        "Switzerland / Suíça": "Switzerland",
        "Turkey / Turquia": "Turkey",
        "Ukraine / Ucrânia": "Ukraine",
        "Uruguay / Uruguai": "Uruguay",
    }

    @st.cache_data
    def carregar_historico():
        df = pd.read_csv("results_2000.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['peso_torneio'] = df['tournament'].map(PESOS_TORNEIO).fillna(1.5)
        ano_min = df['date'].dt.year.min()
        ano_max = df['date'].dt.year.max()
        df['peso_tempo'] = (df['date'].dt.year - ano_min) / (ano_max - ano_min) * 2 + 1
        df['peso_final'] = df['peso_torneio'] * df['peso_tempo']
        return df

    def calcular_prob(time1, time2, df_hist):
        confrontos = df_hist[
            ((df_hist['home_team'] == time1) & (df_hist['away_team'] == time2)) |
            ((df_hist['home_team'] == time2) & (df_hist['away_team'] == time1))
        ].copy()

        if len(confrontos) == 0:
            return None

        v1 = v2 = emp = 0
        for _, row in confrontos.iterrows():
            peso = row['peso_final']
            if row['home_team'] == time1:
                if row['home_score'] > row['away_score']: v1 += peso
                elif row['home_score'] < row['away_score']: v2 += peso
                else: emp += peso
            else:
                if row['away_score'] > row['home_score']: v1 += peso
                elif row['away_score'] < row['home_score']: v2 += peso
                else: emp += peso

        total = v1 + v2 + emp
        return {
            'jogos': len(confrontos),
            'v1': round(v1 / total * 100, 1),
            'emp': round(emp / total * 100, 1),
            'v2': round(v2 / total * 100, 1),
            'confrontos': confrontos.sort_values('date', ascending=False).head(5)
        }

    df_hist = carregar_historico()

    col1, col2 = st.columns(2)
    with col1:
        time1_label = st.selectbox("🏠 Team 1 / Time 1", TIMES_COPA, index=TIMES_COPA.index("Brazil / Brasil"))
    with col2:
        time2_opcoes = [t for t in TIMES_COPA if t != time1_label]
        time2_label = st.selectbox("✈️ Team 2 / Time 2", time2_opcoes, index=time2_opcoes.index("Argentina / Argentina"))

    time1 = NOME_DATASET.get(time1_label, time1_label)
    time2 = NOME_DATASET.get(time2_label, time2_label)

    resultado = calcular_prob(time1, time2, df_hist)

    if resultado is None:
        st.warning(f"No historical matches found between {time1_label} and {time2_label} since 2000. / Nenhum confronto encontrado desde 2000.")
    else:
        st.divider()
        st.markdown(f"### Based on **{resultado['jogos']}** matches / jogos")

        fig = go.Figure(go.Bar(
            x=[resultado['v1'], resultado['emp'], resultado['v2']],
            y=[time1_label, "Draw / Empate", time2_label],
            orientation='h',
            marker_color=['#2ecc71', '#95a5a6', '#e74c3c'],
            text=[f"{resultado['v1']}%", f"{resultado['emp']}%", f"{resultado['v2']}%"],
            textposition='outside'
        ))
        fig.update_layout(
            xaxis=dict(range=[0, 100], title="Probability / Probabilidade (%)"),
            height=250,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Últimos confrontos
        st.subheader("📋 Last matches / Últimos confrontos")
        ult = resultado['confrontos'][['date', 'home_team', 'home_score', 'away_score', 'away_team', 'tournament']].copy()
        ult['date'] = ult['date'].dt.strftime('%d/%m/%Y')
        ult['Score'] = ult['home_score'].astype(int).astype(str) + ' x ' + ult['away_score'].astype(int).astype(str)
        ult = ult.rename(columns={'date': 'Date', 'home_team': 'Home', 'away_team': 'Away', 'tournament': 'Tournament'})
        st.dataframe(ult[['Date', 'Home', 'Score', 'Away', 'Tournament']], use_container_width=True, hide_index=True)

        st.caption("⚖️ Weights / Pesos: FIFA World Cup ×5 · Major tournaments ×4 · Qualifiers ×2-3 · Friendly ×1 · Recent matches weighted higher / Jogos recentes com maior peso")
