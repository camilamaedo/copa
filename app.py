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

# ── Constantes ──
RANKING_FIFA = {
    "Argentina": 1900, "Spain": 1876, "France": 1877, "England": 1826,
    "Portugal": 1764, "Brazil": 1761, "Netherlands": 1758, "Morocco": 1756,
    "Belgium": 1735, "Germany": 1730, "Croatia": 1717, "Senegal": 1689,
    "Mexico": 1681, "United States": 1673, "Uruguay": 1673, "Japan": 1660,
    "Switzerland": 1649, "Denmark": 1621, "Ecuador": 1600, "Poland": 1590,
    "Serbia": 1580, "Turkey": 1570, "Australia": 1560, "Iran": 1550,
    "Canada": 1540, "Egypt": 1530, "Nigeria": 1520, "Norway": 1510,
    "Qatar": 1480, "New Zealand": 1420, "Ukraine": 1610, "Czech Republic": 1580,
    "South Africa": 1450, "South Korea": 1560, "Bosnia and Herzegovina": 1510,
    "Haiti": 1320, "Scotland": 1530, "Paraguay": 1560, "Ivory Coast": 1560,
    "Curacao": 1280, "Tunisia": 1510, "Sweden": 1590, "Saudi Arabia": 1480,
    "Cape Verde": 1390, "Iraq": 1390, "Algeria": 1530, "Austria": 1600,
    "Jordan": 1360, "Uzbekistan": 1420, "DR Congo": 1400, "Colombia": 1660,
    "Ghana": 1470, "Panama": 1430,
}

PESOS_TORNEIO = {
    'FIFA World Cup': 5, 'Copa América': 3, 'UEFA Euro': 4,
    'African Cup of Nations': 3, 'AFC Asian Cup': 3, 'Gold Cup': 2,
    'FIFA World Cup qualification': 3, 'UEFA Euro qualification': 2,
    'African Cup of Nations qualification': 2, 'UEFA Nations League': 2,
    'CONCACAF Nations League': 2, 'Friendly': 1,
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

# ── Histórico ──
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

@st.cache_data
def calcular_notas_historicas():
    df = carregar_historico()
    todos = set()
    for times in GRUPOS_COPA.values():
        todos.update(times)
    for v in NOME_DATASET.values():
        todos.add(v)

    notas = {}
    for time in todos:
        jogos = df[(df['home_team']==time)|(df['away_team']==time)]
        if len(jogos) == 0:
            notas[time] = 0.5
            continue
        score = total_peso = 0
        for _, row in jogos.iterrows():
            oponente = row['away_team'] if row['home_team']==time else row['home_team']
            peso_oponente = RANKING_FIFA.get(oponente, 1500) / 1500
            peso = row['peso_final'] * peso_oponente
            if row['home_team'] == time:
                if row['home_score'] > row['away_score']: score += peso
                elif row['home_score'] == row['away_score']: score += peso * 0.4
            else:
                if row['away_score'] > row['home_score']: score += peso
                elif row['away_score'] == row['home_score']: score += peso * 0.4
            total_peso += peso
        notas[time] = score / total_peso if total_peso > 0 else 0.5
    return notas

def prob_hibrida(t1, t2, notas):
    pts1 = RANKING_FIFA.get(t1, 1500)
    pts2 = RANKING_FIFA.get(t2, 1500)
    elo = 1 / (1 + 10 ** (-(pts1 - pts2) / 400))
    n1 = notas.get(t1, 0.5)
    n2 = notas.get(t2, 0.5)
    hist = n1 / (n1 + n2) if (n1 + n2) > 0 else 0.5
    return 0.55 * elo + 0.35 * hist + 0.10 * 0.5

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

def calcular_prob_head2head(label1, label2, df_hist, notas):
    t1 = NOME_DATASET.get(label1, label1)
    t2 = NOME_DATASET.get(label2, label2)
    p_elo = 1/(1+10**(-(RANKING_FIFA.get(t1,1500)-RANKING_FIFA.get(t2,1500))/400))
    n1 = notas.get(t1, 0.5)
    n2 = notas.get(t2, 0.5)
    hist = n1/(n1+n2) if (n1+n2)>0 else 0.5
    cd1, cdemp, cd2, ultimos, n_jogos = _confronto_direto(df_hist, t1, t2)
    tem_cd = cd1 is not None
    w_cd = min(n_jogos * 0.02, 0.10) if tem_cd else 0
    if tem_cd:
        raw1 = (0.55-w_cd/2)*p_elo + (0.35-w_cd/2)*hist + w_cd*cd1
        raw2 = (0.55-w_cd/2)*(1-p_elo) + (0.35-w_cd/2)*(1-hist) + w_cd*cd2
    else:
        raw1 = 0.55*p_elo + 0.35*hist + 0.10*0.5
        raw2 = 0.55*(1-p_elo) + 0.35*(1-hist) + 0.10*0.5
    equilibrio = 1 - abs(raw1-raw2)
    w_emp = 0.15 + 0.15*equilibrio
    prob1 = raw1*(1-w_emp); prob_emp = w_emp; prob2 = raw2*(1-w_emp)
    total = prob1+prob_emp+prob2
    return {
        'prob1': round(prob1/total*100,1), 'prob_emp': round(prob_emp/total*100,1),
        'prob2': round(prob2/total*100,1),
        'fifa1': RANKING_FIFA.get(t1,1500), 'fifa2': RANKING_FIFA.get(t2,1500),
        'tem_cd': tem_cd, 'n_jogos': n_jogos,
        'cd1': round(cd1*100,1) if tem_cd else None,
        'cd2': round(cd2*100,1) if tem_cd else None,
        'ultimos': ultimos,
    }

def _jogo_sim(t1, t2, notas):
    return t1 if np.random.random() < prob_hibrida(t1, t2, notas) else t2

def simular_copa(notas, det=False):
    cl = {}
    for letra, times in GRUPOS_COPA.items():
        pts = {t:0 for t in times}
        gd = {t:0.0 for t in times}
        for i,t1 in enumerate(times):
            for t2 in times[i+1:]:
                p = prob_hibrida(t1,t2,notas)
                if det:
                    res = (3,0) if p>0.55 else (0,3) if p<0.45 else (1,1)
                else:
                    r = np.random.random()
                    res = (3,0) if r<p*0.72 else (1,1) if r<p*0.72+0.28 else (0,3)
                pts[t1]+=res[0]; pts[t2]+=res[1]
                diff=(RANKING_FIFA.get(t1,1500)-RANKING_FIFA.get(t2,1500))/200
                gd[t1]+=diff; gd[t2]-=diff
        cl[letra]=tuple(sorted(times,key=lambda t:(pts[t],gd[t]),reverse=True)[:2])

    terceiros_raw = []
    for letra, times in GRUPOS_COPA.items():
        pts = {t:0 for t in times}
        for i,t1 in enumerate(times):
            for t2 in times[i+1:]:
                p = prob_hibrida(t1,t2,notas)
                r = np.random.random() if not det else (0.4 if p>0.55 else 0.6)
                res = (3,0) if r<p*0.72 else (1,1) if r<p*0.72+0.28 else (0,3)
                pts[t1]+=res[0]; pts[t2]+=res[1]
        terceiro = sorted(times,key=lambda t:pts[t],reverse=True)[2]
        terceiros_raw.append((terceiro, pts[terceiro]))
    terceiros = [t for t,_ in sorted(terceiros_raw,key=lambda x:x[1],reverse=True)[:8]]

    r32p = [
        (cl["A"][0],cl["B"][1]),(cl["C"][0],cl["D"][1]),
        (cl["E"][0],cl["F"][1]),(cl["G"][0],cl["H"][1]),
        (cl["I"][0],cl["J"][1]),(cl["K"][0],cl["L"][1]),
        (cl["B"][0],cl["A"][1]),(cl["D"][0],cl["C"][1]),
        (cl["F"][0],cl["E"][1]),(cl["H"][0],cl["G"][1]),
        (cl["J"][0],cl["I"][1]),(cl["L"][0],cl["K"][1]),
        (terceiros[0],terceiros[1]),(terceiros[2],terceiros[3]),
        (terceiros[4],terceiros[5]),(terceiros[6],terceiros[7]),
    ]
    r32v = [_jogo_sim(a,b,notas) if not det else (a if prob_hibrida(a,b,notas)>=0.5 else b) for a,b in r32p]
    r16p = [(r32v[i],r32v[i+1]) for i in range(0,16,2)]
    r16v = [_jogo_sim(a,b,notas) if not det else (a if prob_hibrida(a,b,notas)>=0.5 else b) for a,b in r16p]
    qfp = [(r16v[i],r16v[i+1]) for i in range(0,8,2)]
    qfv = [_jogo_sim(a,b,notas) if not det else (a if prob_hibrida(a,b,notas)>=0.5 else b) for a,b in qfp]
    sfp = [(qfv[0],qfv[1]),(qfv[2],qfv[3])]
    sfv = [_jogo_sim(a,b,notas) if not det else (a if prob_hibrida(a,b,notas)>=0.5 else b) for a,b in sfp]
    campeao = _jogo_sim(sfv[0],sfv[1],notas) if not det else (sfv[0] if prob_hibrida(sfv[0],sfv[1],notas)>=0.5 else sfv[1])
    return {
        'grupos': cl, 'round32': list(zip([f"{a} vs {b}" for a,b in r32p],r32v)),
        'round16': list(zip([f"{a} vs {b}" for a,b in r16p],r16v)),
        'quartas': list(zip([f"{a} vs {b}" for a,b in qfp],qfv)),
        'semis': list(zip([f"{a} vs {b}" for a,b in sfp],sfv)),
        'final': (f"{sfv[0]} vs {sfv[1]}", campeao), 'campeao': campeao,
    }

# ── UI ──
st.title("⚽ World Cup 2026 — Research / Pesquisa")

aba_aposta, aba_resultados, aba_prob, aba_simulacao = st.tabs([
    "🗳️ Bet / Apostar",
    "📊 Results / Resultados",
    "🔮 Probability / Probabilidade",
    "🏆 Simulation / Simulação"
])

# ── ABA 1 ──
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
        pais_origem = st.selectbox("Where are you from? / De onde você é?",
            ["— select / selecione —"] + TIMES_COPA + ["Other / Outro"])
        st.divider()
        st.subheader("Your bets / Suas apostas")
        campeao = st.selectbox("🏆 Who will be the champion? / Quem vai ser campeão?",
            ["— select / selecione —"] + TIMES_COPA)
        vice_opcoes = [t for t in TIMES_COPA if t != campeao]
        vice = st.selectbox("🥈 Who will be the runner-up? / Quem vai ser vice-campeão?",
            vice_opcoes, key=f"vice_{campeao}")
        comentario = st.text_area("💬 Any comments? / Algum comentário? (optional / opcional)",
            placeholder="Why do you think so? / Por que você acha isso?", max_chars=300)
        enviado = st.form_submit_button("Submit / Enviar ✅", use_container_width=True, type="primary")
    if enviado:
        if campeao.startswith("—"):
            st.error("Please select champion. / Por favor selecione o campeão.")
        else:
            nome_final = nome.strip() if nome.strip() else "Anonymous"
            pais_final = pais_origem if not pais_origem.startswith("—") else None
            salvar_aposta(nome_final, pais_final, campeao, vice, comentario)
            st.success(f"✅ Bet registered! / Aposta registrada! — **{campeao}** 🏆")
            st.balloons()

# ── ABA 2 ──
with aba_resultados:
    st.subheader("📊 Results / Resultados")
    total = total_respostas()
    if total == 0:
        st.warning("No responses yet. / Ainda não há respostas.")
        st.stop()
    df_ap = carregar_apostas()
    col1,col2,col3 = st.columns(3)
    col1.metric("Total responses / Respostas", total)
    col2.metric("Favourite / Favorito 🏆", df_ap["campeao"].mode()[0])
    col3.metric("Countries / Países", df_ap["pais_origem"].dropna().nunique())
    st.divider()
    col_a,col_b = st.columns(2)
    with col_a:
        st.subheader("🏆 Champion votes / Votos campeão")
        cc = df_ap["campeao"].value_counts().reset_index().rename(columns={"campeao":"Team","count":"Votes"})
        fig1 = px.bar(cc, x="Votes", y="Team", orientation="h", color="Votes",
                      color_continuous_scale="Teal", text="Votes")
        fig1.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        st.subheader("🥧 Distribution / Distribuição")
        fig2 = px.pie(cc, names="Team", values="Votes", hole=0.4,
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    st.subheader("🌎 Where are participants from? / De onde são os participantes?")
    pc = (df_ap["pais_origem"].dropna().str.strip().loc[lambda s: s!=""]
          .value_counts().reset_index()
          .rename(columns={"pais_origem":"Country","count":"Responses"}))
    if not pc.empty:
        fig3 = px.bar(pc, x="Country", y="Responses", color="Responses",
                      color_continuous_scale="Blues", text="Responses")
        fig3.update_layout(coloraxis_showscale=False)
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No location data yet. / Nenhum dado de localização ainda.")
    st.divider()
    st.subheader("📅 Responses over time / Respostas ao longo do tempo")
    df_ap["data"] = pd.to_datetime(df_ap["criado_em"]).dt.date
    por_dia = df_ap.groupby("data").size().reset_index(name="Responses")
    fig4 = px.line(por_dia, x="data", y="Responses", markers=True)
    st.plotly_chart(fig4, use_container_width=True)
    st.divider()
    st.subheader("⬇️ Export / Exportar dados")
    cx,cy = st.columns(2)
    with cx:
        st.download_button("📄 CSV", df_ap.to_csv(index=False).encode("utf-8"),
                           "apostas.csv","text/csv",use_container_width=True)
    with cy:
        st.download_button("📋 JSON",
                           df_ap.to_json(orient="records",force_ascii=False,date_format="iso").encode("utf-8"),
                           "apostas.json","application/json",use_container_width=True)
    with st.expander("See all / Ver todas"):
        st.dataframe(df_ap[[c for c in df_ap.columns if c!="id"]], use_container_width=True)

# ── ABA 3 ──
with aba_prob:
    st.subheader("🔮 Head-to-Head Probability / Probabilidade de Confronto")
    st.markdown("""
    **EN** — Hybrid model: 55% FIFA Ranking + 35% historical performance (adjusted by opponent strength, since 2000) + 10% randomness.

    **PT** — Modelo híbrido: 55% Ranking FIFA + 35% histórico (ajustado pela força do adversário, desde 2000) + 10% aleatoriedade.
    """)
    df_hist = carregar_historico()
    notas = calcular_notas_historicas()
    c1,c2 = st.columns(2)
    with c1:
        idx_arg = TIMES_COPA.index("Argentina / Argentina")
        t1_label = st.selectbox("Team 1 / Time 1", TIMES_COPA, index=idx_arg)
    with c2:
        t2_opcoes = [t for t in TIMES_COPA if t != t1_label]
        idx_bel = t2_opcoes.index("Belgium / Bélgica") if "Belgium / Bélgica" in t2_opcoes else 0
        t2_label = st.selectbox("Team 2 / Time 2", t2_opcoes, index=idx_bel)
    r = calcular_prob_head2head(t1_label, t2_label, df_hist, notas)
    st.divider()
    ca,cb,cc_ = st.columns([2,1,2])
    with ca:
        st.markdown(f"### {t1_label}")
        st.markdown(f"## **{r['prob1']}%**")
    with cb:
        st.markdown("### VS")
        st.markdown("##### to win / de ganhar")
    with cc_:
        st.markdown(f"### {t2_label}")
        st.markdown(f"## **{r['prob2']}%**")
    fig = go.Figure(go.Bar(
        x=[r['prob1'], r['prob_emp'], r['prob2']],
        y=[t1_label, "Draw / Empate", t2_label],
        orientation='h',
        marker_color=['#2ecc71','#95a5a6','#e74c3c'],
        text=[f"{r['prob1']}%", f"{r['prob_emp']}%", f"{r['prob2']}%"],
        textposition='outside'
    ))
    fig.update_layout(xaxis=dict(range=[0,100],title="Probability %"),
                      height=250, showlegend=False, margin=dict(l=10,r=40,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("📊 Model breakdown / Detalhes do modelo"):
        cx2,cy2 = st.columns(2)
        with cx2:
            st.markdown(f"**{t1_label}**")
            st.write(f"🏅 FIFA pts: {r['fifa1']}")
            if r['tem_cd']:
                st.write(f"⚔️ Head-to-head: {r['cd1']}% ({r['n_jogos']} jogos)")
        with cy2:
            st.markdown(f"**{t2_label}**")
            st.write(f"🏅 FIFA pts: {r['fifa2']}")
            if r['tem_cd']:
                st.write(f"⚔️ Head-to-head: {r['cd2']}% ({r['n_jogos']} jogos)")
        if not r['tem_cd']:
            st.info("No direct matches since 2000. / Sem confrontos diretos desde 2000.")
    if r['tem_cd'] and not r['ultimos'].empty:
        st.subheader(f"📋 Last {r['n_jogos']} matches / Últimos confrontos")
        ult = r['ultimos'][['date','home_team','home_score','away_score','away_team','tournament']].copy()
        ult['date'] = pd.to_datetime(ult['date']).dt.strftime('%d/%m/%Y')
        ult['Score'] = ult['home_score'].fillna(0).astype(int).astype(str) + ' x ' + ult['away_score'].fillna(0).astype(int).astype(str)
        ult = ult.rename(columns={'date':'Date','home_team':'Home','away_team':'Away','tournament':'Tournament'})
        st.dataframe(ult[['Date','Home','Score','Away','Tournament']], use_container_width=True, hide_index=True)
    st.caption("⚖️ 55% FIFA Ranking (Jun/2026) + 35% historical adjusted by opponent strength + 10% randomness")

# ── ABA 4 ──
with aba_simulacao:
    st.subheader("🏆 World Cup 2026 Simulation / Simulação da Copa 2026")
    st.markdown("""
    **EN** — Simulate the entire tournament using our hybrid model. Each click gives a different result!

    **PT** — Simule o torneio inteiro usando nosso modelo híbrido. Cada clique dá um resultado diferente!
    """)
    notas_sim = calcular_notas_historicas()
    cb1,cb2 = st.columns(2)
    with cb1:
        sim_btn = st.button("🎲 Simulate! / Simular!", use_container_width=True, type="primary")
    with cb2:
        prov_btn = st.button("📊 Most likely / Mais provável", use_container_width=True)
    if 'sim_result' not in st.session_state:
        st.session_state.sim_result = None
        st.session_state.sim_det = False
    if sim_btn:
        st.session_state.sim_result = simular_copa(notas_sim, det=False)
        st.session_state.sim_det = False
    elif prov_btn:
        st.session_state.sim_result = simular_copa(notas_sim, det=True)
        st.session_state.sim_det = True
    if st.session_state.sim_result:
        r = st.session_state.sim_result
        det = st.session_state.sim_det
        st.info("📊 Most likely / Mais provável" if det else "🎲 Random simulation / Simulação aleatória")
        st.markdown(f"## 🏆 **{r['campeao']}**")
        st.markdown(f"### 🥈 Final: {r['final'][0]}")
        st.divider()
        with st.expander("👥 Group stage / Fase de grupos"):
            cols = st.columns(3)
            for i,(letra,(p1,p2)) in enumerate(r['grupos'].items()):
                with cols[i%3]:
                    st.markdown(f"**Grupo {letra}**")
                    st.write(f"🥇 {p1}")
                    st.write(f"🥈 {p2}")
        st.divider()
        c1,c2 = st.columns(2)
        with c1:
            st.subheader("⚔️ Semifinals / Semifinais")
            for j,v in r['semis']:
                st.markdown(f"- {j} → **{v}** ✅")
            st.subheader("🏟️ Quarterfinals / Quartas")
            for j,v in r['quartas']:
                st.markdown(f"- {j} → **{v}**")
        with c2:
            st.subheader("🔟 Round of 16")
            for j,v in r['round16']:
                st.markdown(f"- {j} → **{v}**")
        with st.expander("🔢 Round of 32"):
            for j,v in r['round32']:
                st.markdown(f"- {j} → **{v}**")
        st.caption("⚖️ Model: 55% FIFA Ranking + 35% historical (adjusted by opponent strength) + 10% randomness")
