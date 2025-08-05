import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Conexão com SQLite
def conectar_sqlite():
    conn = sqlite3.connect("financeiro.db")
    return conn

# Inicializa tabela se não existir
def inicializar_db():
    conn = conectar_sqlite()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            categoria TEXT,
            valor REAL,
            descricao TEXT
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

st.title("💰 Controle Financeiro")

# Formulário para nova transação
with st.form("nova_transacao"):
    data = st.date_input("Data", value=date.today())
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    categoria = st.text_input("Categoria")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    descricao = st.text_input("Descrição")
    enviar = st.form_submit_button("Adicionar")

    if enviar:
        conn = conectar_sqlite()
        conn.execute(
            "INSERT INTO transacoes (data, tipo, categoria, valor, descricao) VALUES (?, ?, ?, ?, ?)",
            (str(data), tipo, categoria, valor, descricao)
        )
        conn.commit()
        conn.close()
        st.success("Transação adicionada!")

# Consulta e exibição dos dados
conn = conectar_sqlite()
df = pd.read_sql_query("SELECT * FROM transacoes ORDER BY data DESC", conn)
conn.close()

st.subheader("Transações")
st.dataframe(df)

# Resumo financeiro
receitas = df[df["tipo"] == "Receita"]["valor"].sum()
despesas = df[df["tipo"] == "Despesa"]["valor"].sum()
saldo = receitas - despesas

st.metric("Receitas", f"R$ {receitas:,.2f}")
st.metric("Despesas", f"R$ {despesas:,.2f}")
st.metric("Saldo", f"R$ {saldo:,.2f}")

# Gráfico de barras por categoria
st.subheader("Despesas por Categoria")
if not df[df["tipo"] == "Despesa"].empty:
    graf = df[df["tipo"] == "Despesa"].groupby("categoria")["valor"].sum().reset_index()
    st.bar_chart(graf, x="categoria", y="valor")