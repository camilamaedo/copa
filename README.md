# ⚽ Copa do Mundo — Pesquisa

App Streamlit para pesquisa de opinião sobre a Copa do Mundo.
Coleta palpites, salva em SQLite e exibe um dashboard de resultados.

## Estrutura

```
copa_pesquisa/
├── app.py                  # página inicial
├── pages/
│   ├── 1_Apostar.py        # formulário de palpites
│   └── 2_Resultados.py     # dashboard com gráficos
├── utils/
│   └── database.py         # funções SQLite
├── db/
│   └── apostas.db          # gerado automaticamente
└── requirements.txt
```

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar o app
streamlit run app.py
```

## Campos coletados

| Campo       | Tipo     | Obrigatório |
|-------------|----------|-------------|
| nome        | texto    | não         |
| pais_origem | seleção  | não         |
| campeao     | seleção  | sim         |
| vice        | seleção  | não         |
| artilheiro  | texto    | não         |
| comentario  | texto    | não         |

## Exportar os dados

No dashboard, use os botões **Baixar CSV** ou **Baixar JSON**
para exportar todas as respostas e usar no pipeline de análise.

## Próximos passos

- [ ] Fase 2: conectar com histórico de Copas passadas (Kaggle)
- [ ] Fase 3: modelo preditivo com Scikit-learn
- [ ] Fase 4: agentes IA para atualização automática
