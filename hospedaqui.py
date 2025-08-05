# Exemplo de importação no app.py:
import streamlit as st
from views import dashboard, unidades, locacoes, despesas, relatorios

st.title("Controle de Hospedagem")

# Botões quadrados de menu
menu_opcoes = ["Dashboard", "Unidades", "Locações", "Despesas", "Relatórios"]
colunas = st.columns(len(menu_opcoes))
aba = None
for i, nome in enumerate(menu_opcoes):
    if colunas[i].button(nome):
        aba = nome

# Se nenhum botão foi pressionado, mostra Dashboard por padrão
if aba is None:
    aba = "Dashboard"

if aba == "Dashboard":
    dashboard.show()
elif aba == "Unidades":
    unidades.show()
elif aba == "Locações":
    locacoes.show()
elif aba == "Despesas":
    despesas.show()
elif aba == "Relatórios":
    relatorios.show()