import streamlit as st
from utils.database import criar_tabela, salvar_aposta, TIMES

st.set_page_config(page_title="Deixe sua aposta", page_icon="🗳️")

criar_tabela()

st.title("🗳️ Deixe sua aposta")
st.markdown("Preencha o formulário abaixo. Participação anônima e sem fins lucrativos.")

with st.form("form_aposta", clear_on_submit=True):

    st.subheader("Sobre você (opcional)")
    nome = st.text_input("Seu nome ou apelido", placeholder="Anônimo")
    pais_origem = st.selectbox("De qual país você é?", ["— prefiro não dizer —"] + TIMES)

    st.divider()
    st.subheader("Suas apostas")

    campeao = st.selectbox(
        "🏆 Quem vai ser campeão?",
        TIMES,
        index=0
    )

    vice = st.selectbox(
        "🥈 Quem vai ser vice-campeão?",
        ["— não sei —"] + TIMES,
        index=0
    )

    artilheiro = st.text_input(
        "⚽ Quem vai ser o artilheiro?",
        placeholder="Ex: Vinicius Jr."
    )

    comentario = st.text_area(
        "💬 Algum comentário ou justificativa? (opcional)",
        placeholder="Por que você acha isso?",
        max_chars=300
    )

    enviado = st.form_submit_button("Enviar aposta", use_container_width=True, type="primary")

if enviado:
    if not campeao:
        st.error("Por favor, escolha um campeão.")
    else:
        nome_final = nome.strip() if nome.strip() else "Anônimo"
        pais_final = pais_origem if pais_origem != "— prefiro não dizer —" else None
        vice_final = vice if vice != "— não sei —" else None

        salvar_aposta(nome_final, pais_final, campeao, vice_final, artilheiro, comentario)

        st.success(f"✅ Aposta registrada! Você apostou em **{campeao}** como campeão.")
        st.balloons()
        st.page_link("pages/2_Resultados.py", label="Ver resultados da pesquisa →")
