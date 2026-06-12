import streamlit as st
from utils.database import criar_tabela, total_respostas

st.set_page_config(
    page_title="Copa do Mundo — Pesquisa",
    page_icon="⚽",
    layout="centered"
)

criar_tabela()

st.title("⚽ Pesquisa Copa do Mundo")
st.markdown("""
Bem-vindo! Esta é uma pesquisa **sem fins lucrativos** para entender
o que as pessoas acham que vai acontecer na próxima Copa do Mundo.

Seus dados são usados apenas para análise acadêmica.
""")

col1, col2 = st.columns(2)
with col1:
    st.metric("Respostas até agora", total_respostas())

st.divider()

st.markdown("""
### Como participar

- **Deixe sua aposta** na página ao lado
- **Veja os resultados** em tempo real no painel de estatísticas
""")

st.info("Use o menu à esquerda para navegar entre as páginas.")
