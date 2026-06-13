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

aba_aposta, aba_resultados, aba_prob, aba_simulacao = st.tabs([
    "🗳️ Bet / Apostar",
    "📊 Results / Resultados",
    "🔮 Probability / Probabilidade",
    "🏆 Simulation / Simulação"
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
        idx_arg = TIMES_COPA.index("Argentina / Argentina")
        t1_label = st.selectbox("Team 1 / Time 1", TIMES_COPA, index=idx_arg)
    with col2:
        t2_opcoes = [t for t in TIMES_COPA if t != t1_label]
        idx_bel = t2_opcoes.index("Belgium / Bélgica") if "Belgium / Bélgica" in t2_opcoes else 0
        t2_label = st.selectbox("Team 2 / Time 2", t2_opcoes, index=idx_bel)

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

# ─────────────────────────────────────────
# ABA 4 — SIMULAÇÃO DA COPA
# ─────────────────────────────────────────
import numpy as np

GRUPOS_COPA = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

RANKING_SIM = {**RANKING_FIFA,
    "South Africa": 1450, "South Korea": 1560, "Bosnia and Herzegovina": 1510,
    "Haiti": 1320, "Scotland": 1530, "Paraguay": 1560, "Ivory Coast": 1560,
    "Curacao": 1280, "Tunisia": 1510, "Sweden": 1590, "Saudi Arabia": 1480,
    "Cape Verde": 1390, "Iraq": 1390, "Algeria": 1530, "Austria": 1600,
    "Jordan": 1360, "Uzbekistan": 1420, "DR Congo": 1400, "Colombia": 1660,
    "Ghana": 1470, "Panama": 1430,
}

def _elo_sim(t1, t2):
    return 1 / (1 + 10 ** (-(RANKING_SIM.get(t1,1500) - RANKING_SIM.get(t2,1500)) / 400))

def _jogo(t1, t2, det):
    p = _elo_sim(t1, t2)
    if det: return t1 if p >= 0.5 else t2
    return t1 if np.random.random() < p else t2

def _grupo(times, det):
    pts = {t: 0 for t in times}
    gd = {t: 0.0 for t in times}
    for i, t1 in enumerate(times):
        for t2 in times[i+1:]:
            p = _elo_sim(t1, t2)
            if det:
                res = (3,0) if p>0.55 else (0,3) if p<0.45 else (1,1)
            else:
                r = np.random.random()
                res = (3,0) if r < p*0.75 else (1,1) if r < p*0.75+0.25 else (0,3)
            pts[t1]+=res[0]; pts[t2]+=res[1]
            diff = (RANKING_SIM.get(t1,1500)-RANKING_SIM.get(t2,1500))/200
            gd[t1]+=diff; gd[t2]-=diff
    cl = sorted(times, key=lambda t:(pts[t],gd[t]), reverse=True)
    return cl[0], cl[1], cl[2], pts

def simular_copa(det=False):
    res = {}
    classificados = {}
    terceiros = []
    for letra, times in GRUPOS_COPA.items():
        p1,p2,p3,pts = _grupo(times, det)
        classificados[letra] = (p1,p2)
        terceiros.append((p3, pts[p3], letra))
    terceiros_cl = [t[0] for t in sorted(terceiros, key=lambda x:x[1], reverse=True)[:8]]
    res['grupos'] = classificados

    r32_pares = [
        (classificados["A"][0], classificados["B"][1]),
        (classificados["C"][0], classificados["D"][1]),
        (classificados["E"][0], classificados["F"][1]),
        (classificados["G"][0], classificados["H"][1]),
        (classificados["I"][0], classificados["J"][1]),
        (classificados["K"][0], classificados["L"][1]),
        (classificados["B"][0], classificados["A"][1]),
        (classificados["D"][0], classificados["C"][1]),
        (classificados["F"][0], classificados["E"][1]),
        (classificados["H"][0], classificados["G"][1]),
        (classificados["J"][0], classificados["I"][1]),
        (classificados["L"][0], classificados["K"][1]),
        (terceiros_cl[0], terceiros_cl[1]),
        (terceiros_cl[2], terceiros_cl[3]),
        (terceiros_cl[4], terceiros_cl[5]),
        (terceiros_cl[6], terceiros_cl[7]),
    ]
    r32v = [_jogo(t1,t2,det) for t1,t2 in r32_pares]
    res['round32'] = list(zip([f"{a} vs {b}" for a,b in r32_pares], r32v))

    r16p = [(r32v[i],r32v[i+1]) for i in range(0,16,2)]
    r16v = [_jogo(t1,t2,det) for t1,t2 in r16p]
    res['round16'] = list(zip([f"{a} vs {b}" for a,b in r16p], r16v))

    qfp = [(r16v[i],r16v[i+1]) for i in range(0,8,2)]
    qfv = [_jogo(t1,t2,det) for t1,t2 in qfp]
    res['quartas'] = list(zip([f"{a} vs {b}" for a,b in qfp], qfv))

    sfp = [(qfv[0],qfv[1]),(qfv[2],qfv[3])]
    sfv = [_jogo(t1,t2,det) for t1,t2 in sfp]
    res['semis'] = list(zip([f"{a} vs {b}" for a,b in sfp], sfv))

    final_par = (sfv[0],sfv[1])
    campeao = _jogo(final_par[0],final_par[1],det)
    res['final'] = (f"{final_par[0]} vs {final_par[1]}", campeao)
    res['campeao'] = campeao
    return res

with aba_simulacao:
    st.subheader("🏆 World Cup 2026 Simulation / Simulação da Copa 2026")
    st.markdown("""
    **EN** — Based on FIFA Rankings and historical data, simulate the entire tournament or see the most likely outcome.

    **PT** — Baseado no Ranking FIFA e histórico, simule o torneio inteiro ou veja o resultado mais provável.
    """)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        simular_btn = st.button("🎲 Simulate! / Simular!", use_container_width=True, type="primary")
    with col_b2:
        provavel_btn = st.button("📊 Most likely / Mais provável", use_container_width=True)

    if 'sim_result' not in st.session_state:
        st.session_state.sim_result = None
        st.session_state.sim_det = False

    if simular_btn:
        st.session_state.sim_result = simular_copa(det=False)
        st.session_state.sim_det = False
    elif provavel_btn:
        st.session_state.sim_result = simular_copa(det=True)
        st.session_state.sim_det = True

    if st.session_state.sim_result:
        r = st.session_state.sim_result
        det = st.session_state.sim_det

        label = "📊 Most likely result / Resultado mais provável" if det else "🎲 Random simulation / Simulação aleatória"
        st.info(label)

        # Campeão em destaque
        st.markdown(f"## 🏆 Champion / Campeão: **{r['campeao']}**")
        st.markdown(f"### 🥈 Final: {r['final'][0]}")

        st.divider()

        # Grupos
        with st.expander("👥 Group stage / Fase de grupos"):
            cols = st.columns(3)
            for i, (letra, (p1, p2)) in enumerate(r['grupos'].items()):
                with cols[i % 3]:
                    st.markdown(f"**Grupo {letra}**")
                    st.write(f"🥇 {p1}")
                    st.write(f"🥈 {p2}")

        st.divider()

        # Eliminatórias
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⚔️ Semifinals / Semifinais")
            for jogo, venc in r['semis']:
                st.markdown(f"- {jogo} → **{venc}** ✅")

            st.subheader("🏟️ Quarterfinals / Quartas")
            for jogo, venc in r['quartas']:
                st.markdown(f"- {jogo} → **{venc}**")

        with col2:
            st.subheader("🔟 Round of 16")
            for jogo, venc in r['round16']:
                st.markdown(f"- {jogo} → **{venc}**")

        with st.expander("🔢 Round of 32"):
            for jogo, venc in r['round32']:
                st.markdown(f"- {jogo} → **{venc}**")

        st.caption("⚖️ Model: FIFA Ranking Elo system · Deterministic = always picks favourite · Random = weighted probability draw")
