import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import criar_tabela, salvar_aposta, carregar_apostas, total_respostas, TIMES_COPA

st.set_page_config(
    page_title="World Cup Research / Pesquisa Copa do Mundo",
    page_icon="⚽",
    layout="centered"
)

criar_tabela()

st.title("⚽ World Cup 2026 — Research / Pesquisa")

aba_aposta, aba_resultados = st.tabs(["🗳️ Bet / Apostar", "📊 Results / Resultados"])

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

        nome = st.text_input(
            "Name or nickname / Nome ou apelido",
            placeholder="Anonymous / Anônimo"
        )

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
            ["— select / selecione —"] + vice_opcoes
        )

        comentario = st.text_area(
            "💬 Any comments? / Algum comentário? (optional / opcional)",
            placeholder="Why do you think so? / Por que você acha isso?",
            max_chars=300
        )

        enviado = st.form_submit_button(
            "Submit / Enviar ✅",
            use_container_width=True,
            type="primary"
        )

    if enviado:
        nome_final = nome.strip() if nome.strip() else "Anonymous"
        pais_final = pais_origem if pais_origem != "— select / selecione —" else None
        if campeao == "— select / selecione —" or vice == "— select / selecione —":
            st.error("Please select champion and runner-up. / Por favor selecione campeão e vice.")
        else:
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
    col3.metric("Countries / Países representados", df["pais_origem"].dropna().nunique())

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Champion votes / Votos campeão")
        campeao_counts = (
            df["campeao"]
            .value_counts()
            .reset_index()
            .rename(columns={"campeao": "Team / Time", "count": "Votes / Votos"})
        )
        fig1 = px.bar(
            campeao_counts,
            x="Votes / Votos", y="Team / Time",
            orientation="h",
            color="Votes / Votos",
            color_continuous_scale="Teal",
            text="Votes / Votos"
        )
        fig1.update_layout(showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.subheader("🥧 Distribution / Distribuição")
        fig2 = px.pie(
            campeao_counts,
            names="Team / Time",
            values="Votes / Votos",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader("🌎 Where are participants from? / De onde são os participantes?")
    pais_counts = (
        df["pais_origem"]
        .dropna()
        .str.strip()
        .loc[lambda s: s != ""]
        .value_counts()
        .reset_index()
        .rename(columns={"pais_origem": "Country / País", "count": "Responses / Respostas"})
    )
    if not pais_counts.empty:
        fig3 = px.bar(
            pais_counts,
            x="Country / País", y="Responses / Respostas",
            color="Responses / Respostas",
            color_continuous_scale="Blues",
            text="Responses / Respostas"
        )
        fig3.update_layout(coloraxis_showscale=False)
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No location data yet. / Nenhum dado de localização ainda.")

    st.divider()

    st.subheader("📅 Responses over time / Respostas ao longo do tempo")
    df["criado_em"] = pd.to_datetime(df["criado_em"]).dt.date
    por_dia = df.groupby("criado_em").size().reset_index(name="Responses")
    fig4 = px.line(por_dia, x="criado_em", y="Responses", markers=True)
    fig4.update_layout(xaxis_title="Date / Data", yaxis_title="Responses / Respostas")
    st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    st.subheader("⬇️ Export / Exportar dados")
    col_x, col_y = st.columns(2)
    with col_x:
        st.download_button("📄 Download CSV", df.to_csv(index=False).encode("utf-8"), "apostas.csv", "text/csv", use_container_width=True)
    with col_y:
        st.download_button("📋 Download JSON", df.to_json(orient="records", force_ascii=False).encode("utf-8"), "apostas.json", "application/json", use_container_width=True)

    with st.expander("See all responses / Ver todas as respostas"):
        st.dataframe(df.drop(columns=["id"]), use_container_width=True)
