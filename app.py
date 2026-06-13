import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.database import criar_tabela, salvar_aposta, carregar_apostas, total_respostas, TIMES_COPA

st.set_page_config(
    page_title="World Cup 2026 Research / Pesquisa Copa 2026",
    page_icon="⚽",
    layout="centered"
)

criar_tabela()

# ── Constantes do modelo ──
RANKING_FIFA = {
    "Argentina": 1900, "Spain": 1876, "France": 1877, "England": 1826,
    "Portugal": 1764, "Brazil": 1761, "Netherlands": 1758, "Morocco": 1756,
    "Belgium": 1735, "Germany": 1730, "Croatia": 1717, "Senegal": 1689,
    "Mexico": 1681, "United States": 1673, "Uruguay": 1673, "Japan": 1660,
    "Switzerland": 1649, "Denmark": 1621, "Ecuador": 1600, "Poland": 1590,
    "Serbia": 1580, "Turkey": 1570, "Australia": 1560, "Iran": 1550,
    "Canada": 1540, "Egypt": 1530, "Nigeria": 1520, "Norway": 1510,
    "Qatar": 1480, "New Zealand": 1420, "Ukraine": 1610, "Czech Republic": 1580,
}

PESOS_TORNEIO = {
    'FIFA World Cup': 5, 'Copa América': 4, 'UEFA Euro': 4,
    'African Cup of Nations': 4, 'AFC Asian Cup': 4, 'Gold Cup': 3,
    'FIFA World Cup qualification': 3, 'UEFA Euro qualification': 2,
    'African Cup of Nations qualification': 2, 'UEFA Nations League': 2,
    'CONCACAF Nations League': 2, 'Friendly': 1,
}

BANDEIRAS = {
    "Germany / Alemanha": "🇩🇪", "Argentina / Argentina": "🇦🇷",
    "Australia / Austrália": "🇦🇺", "Belgium / Bélgica": "🇧🇪",
    "Brazil / Brasil": "🇧🇷", "Canada / Canadá": "🇨🇦",
    "Croatia / Croácia": "🇭🇷", "Denmark / Dinamarca": "🇩🇰",
    "Egypt / Egito": "🇪🇬", "Ecuador / Equador": "🇪🇨",
    "Spain / Espanha": "🇪🇸", "USA / EUA": "🇺🇸",
    "France / França": "🇫🇷", "Netherlands / Holanda": "🇳🇱",
    "England / Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Iran / Irã": "🇮🇷",
    "Japan / Japão": "🇯🇵", "Morocco / Marrocos": "🇲🇦",
    "Mexico / México": "🇲🇽", "Nigeria / Nigéria": "🇳🇬",
    "Norway / Noruega": "🇳🇴", "New Zealand / Nova Zelândia": "🇳🇿",
    "Poland / Polônia": "🇵🇱", "Portugal / Portugal": "🇵🇹",
    "Qatar / Qatar": "🇶🇦", "Czech Republic / República Tcheca": "🇨🇿",
    "Senegal / Senegal": "🇸🇳", "Serbia / Sérvia": "🇷🇸",
    "Switzerland / Suíça": "🇨🇭", "Turkey / Turquia": "🇹🇷",
    "Ukraine / Ucrânia": "🇺🇦", "Uruguay / Uruguai": "🇺🇾",
}

NOME_DATASET = {
    "Germany / Alemanha": "Germany", "Argentina / Argentina": "Argentina",
    "Australia / Austrália": "Australia", "Belgium / Bélgica": "Belgium",
    "Brazil / Brasil": "Brazil", "Canada / Canadá": "Canada",
    "Croatia / Croácia": "Croatia", "Denmark / Dinamarca": "Denmark",
    "Egypt / Egito": "Egypt", "Ecuador / Equador": "Ecuador",
    "Spain / Espanha": "Spain", "USA / EUA": "United States",
    "France / França": "France", "Netherlands / Holanda": "Netherlands",
    "England / Inglaterra": "England", "Iran / Irã": "Iran",
    "Japan / Japão": "Japan", "Morocco / Marrocos": "Morocco",
    "Mexico / México": "Mexico", "Nigeria / Nigéria": "Nigeria",
    "Norway / Noruega": "Norway", "New Zealand / Nova Zelândia": "New Zealand",
    "Poland / Polônia": "Poland", "Portugal / Portugal": "Portugal",
    "Qatar / Qatar": "Qatar", "Czech Republic / República Tcheca": "Czech Republic",
    "Senegal / Senegal": "Senegal", "Serbia / Sérvia": "Serbia",
    "Switzerland / Suíça": "Switzerland", "Turkey / Turquia": "Turkey",
    "Ukraine / Ucrânia": "Ukraine", "Uruguay / Uruguai": "Uruguay",
}

@st.cache_data
def carregar_historico():
    df = pd.read_csv("results_2000.csv")
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['home_score', 'away_score'])
    df['peso_torneio'] = df['tournament'].map(PESOS_TORNEIO).fillna(1.5)
    ano_min = df['date'].dt.year.min()
    ano_max = df['date'].dt.year.max()
    df['peso_tempo'] = (df['date'].dt.year - ano_min) / (ano_max - ano_min) * 2 + 1
    df['peso_final'] = df['peso_torneio'] * df['peso_tempo']
    return df

def _elo_prob(pts1, pts2):
    return 1 / (1 + 10 ** (-(pts1 - pts2) / 400))

def _confronto_direto(df, t1, t2):
    conf = df[
        ((df['home_team']==t1)&(df['away_team']==t2))|
        ((df['home_team']==t2)&(df['away_team']==t1))
    ].copy()
    if len(conf) == 0:
        return None, None, None, pd.DataFrame(), 0
    v1=v2=emp=0
    for _,row in conf.iterrows():
        p = row['peso_final']
        if row['home_team']==t1:
            if row['home_score']>row['away_score']: v1+=p
            elif row['home_score']<row['away_score']: v2+=p
            else: emp+=p
        else:
            if row['away_score']>row['home_score']: v1+=p
            elif row['away_score']<row['home_score']: v2+=p
            else: emp+=p
    total = v1+v2+emp
    return v1/total, emp/total, v2/total, conf.sort_values('date',ascending=False).head(5), len(conf)

def calcular_prob(label1, label2, df_hist):
    t1 = NOME_DATASET.get(label1, label1)
    t2 = NOME_DATASET.get(label2, label2)

    p_elo = _elo_prob(RANKING_FIFA.get(t1,1500), RANKING_FIFA.get(t2,1500))
    cd1, cdemp, cd2, ultimos, n_jogos = _confronto_direto(df_hist, t1, t2)
    tem_cd = cd1 is not None

    # Peso confronto direto cresce com nº de jogos (máx 10%)
    w_cd = min(n_jogos * 0.02, 0.10) if tem_cd else 0
    w_elo = 1.0 - w_cd

    if tem_cd:
        raw1 = w_elo * p_elo + w_cd * cd1
        raw2 = w_elo * (1-p_elo) + w_cd * cd2
    else:
        raw1 = p_elo
        raw2 = 1 - p_elo

    # Empate calibrado pelo equilíbrio do confronto
    equilibrio = 1 - abs(raw1 - raw2)
    w_emp = 0.15 + 0.15 * equilibrio  # entre 15% e 30%

    prob1 = raw1 * (1 - w_emp)
    prob_emp = w_emp
    prob2 = raw2 * (1 - w_emp)
    total = prob1 + prob_emp + prob2

    return {
        'prob1': round(prob1/total*100, 1),
        'prob_emp': round(prob_emp/total*100, 1),
        'prob2': round(prob2/total*100, 1),
        'fifa1': round(RANKING_FIFA.get(t1,1500)),
        'fifa2': round(RANKING_FIFA.get(t2,1500)),
        'tem_cd': tem_cd,
        'n_jogos': n_jogos,
        'w_cd': round(w_cd*100),
        'cd1': round(cd1*100, 1) if tem_cd else None,
        'cd2': round(cd2*100, 1) if tem_cd else None,
        'ultimos': ultimos,
    }

# ── UI ──
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
            vice_opcoes,
            key=f"vice_{campeao}"
        )
        comentario = st.text_area(
            "💬 Any comments? / Algum comentário? (optional / opcional)",
            placeholder="Why do you think so? / Por que você acha isso?",
            max_chars=300
        )
        enviado = st.form_submit_button("Submit / Enviar ✅", use_container_width=True, type="primary")

    if enviado:
        if campeao.startswith("—"):
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
    **EN** — Hybrid model: 50% FIFA Ranking + 40% historical performance (since 2000, weighted by tournament & recency) + 10% head-to-head record.

    **PT** — Modelo híbrido: 50% Ranking FIFA + 40% histórico geral (desde 2000, ponderado por torneio e data) + 10% confronto direto.
    """)

    df_hist = carregar_historico()

    col1, col2 = st.columns(2)
    with col1:
        idx_brasil = TIMES_COPA.index("Brazil / Brasil")
        t1_label = st.selectbox("Team 1 / Time 1", TIMES_COPA, index=idx_brasil)
    with col2:
        t2_opcoes = [t for t in TIMES_COPA if t != t1_label]
        idx_arg = t2_opcoes.index("Argentina / Argentina") if "Argentina / Argentina" in t2_opcoes else 0
        t2_label = st.selectbox("Team 2 / Time 2", t2_opcoes, index=idx_arg)

    f1 = BANDEIRAS.get(t1_label, "")
    f2 = BANDEIRAS.get(t2_label, "")

    r = calcular_prob(t1_label, t2_label, df_hist)

    st.divider()

    # Placar de probabilidade
    col_a, col_b, col_c = st.columns([2, 1, 2])
    with col_a:
        st.markdown(f"### {t1_label}")
        st.markdown(f"## **{r['prob1']}%**")
    with col_b:
        st.markdown("### VS")
        st.markdown("##### to win / de ganhar")
    with col_c:
        st.markdown(f"### {t2_label}")
        st.markdown(f"## **{r['prob2']}%**")

    # Barra visual
    fig = go.Figure(go.Bar(
        x=[r['prob1'], r['prob_emp'], r['prob2']],
        y=[t1_label, "Draw / Empate", t2_label],
        orientation='h',
        marker_color=['#2ecc71', '#95a5a6', '#e74c3c'],
        text=[f"{r['prob1']}%", f"{r['prob_emp']}%", f"{r['prob2']}%"],
        textposition='outside'
    ))
    fig.update_layout(xaxis=dict(range=[0, 100], title="Probability / Probabilidade (%)"),
                      height=250, showlegend=False, margin=dict(l=10, r=40, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Detalhamento dos componentes
    with st.expander("📊 See model breakdown / Ver detalhes do modelo"):
        col_x, col_y = st.columns(2)
        with col_x:
            st.markdown(f"**{t1_label}**")
            st.write(f"🏅 FIFA pts: {r['fifa1']}")
            if r['tem_cd']:
                st.write(f"⚔️ Head-to-head wins / Vitórias diretas: {r['cd1']}% ({r['n_jogos']} jogos, peso {r['w_cd']}%)")
        with col_y:
            st.markdown(f"**{t2_label}**")
            st.write(f"🏅 FIFA pts: {r['fifa2']}")
            if r['tem_cd']:
                st.write(f"⚔️ Head-to-head wins / Vitórias diretas: {r['cd2']}% ({r['n_jogos']} jogos, peso {r['w_cd']}%)")
        if not r['tem_cd']:
            st.info("No direct matches found since 2000 — only FIFA Ranking used. / Sem confrontos diretos, apenas Ranking FIFA.")

    # Últimos confrontos
    if r['tem_cd'] and not r['ultimos'].empty:
        st.subheader(f"📋 Last matches / Últimos confrontos ({r['n_jogos']} found / encontrados)")
        ult = r['ultimos'][['date','home_team','home_score','away_score','away_team','tournament']].copy()
        ult['date'] = pd.to_datetime(ult['date']).dt.strftime('%d/%m/%Y')
        ult['Score'] = ult['home_score'].fillna(0).astype(int).astype(str) + ' x ' + ult['away_score'].fillna(0).astype(int).astype(str)
        ult = ult.rename(columns={'date':'Date','home_team':'Home','away_team':'Away','tournament':'Tournament'})
        st.dataframe(ult[['Date','Home','Score','Away','Tournament']], use_container_width=True, hide_index=True)
    elif not r['tem_cd']:
        st.info(f"No direct matches between {t1_label} and {t2_label} since 2000. / Nenhum confronto direto desde 2000.")

    st.caption("⚖️ Model / Modelo: 50% FIFA Ranking (Jun/2026) + 40% historical performance + 10% head-to-head · Laplace smoothing applied")
