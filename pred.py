import streamlit as st
import pandas as pd
import pyodbc
from io import BytesIO
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# Topo com logo e barra de título
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("logoternium.svg", width=90)  # ajuste o nome/caminho se necessário
with col_titulo:
    st.markdown(
        """
        <div style="background-color:#666666; padding:18px 0 12px 28px; border-radius:6px; margin-bottom:18px;">
            <span style="
                color:white;
                font-size:2.3rem;
                font-weight:700;
                letter-spacing:1px;
                font-family: Arial, Helvetica, sans-serif;
            ">
                TMS - Gestão
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

# Configuração da página
st.set_page_config(page_title="Gestão de Teste de Prontidão", layout="wide")

# Conexão com SQL Server
def conectar_sql():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=TERBRDWHDB03;'
        'DATABASE=DWH_BRASIL;'
        'Trusted_Connection=yes;'
        'UID=Ternium\\10240974'
    )

# Carregar dados
@st.cache_data
def carregar_dados():
    conn = conectar_sql()
    query = """
        SELECT *
        FROM VFBR.REP_TESTE_PRONTIDAO_BR
    """
    return pd.read_sql(query, conn)

st.title("📋 Gestão de Teste de Prontidão – Empregados")

df = carregar_dados()

# Tratamento de colunas
df["DT_ENTRADA"] = pd.to_datetime(df["DT_ENTRADA"], errors='coerce')
df["TESTE_REAL"] = df["TESTE_REAL"].str.upper().str.strip()

# Filtro de período
st.sidebar.subheader("🗓️ Filtro de Período")
opcao_periodo = st.sidebar.selectbox(
    "Selecione o período:",
    ["Exercício Atual", "Exercício Anterior", "Ano Móvel", "Personalizado"]
)

hoje = pd.to_datetime(date.today())
ano = hoje.year
mes = hoje.month

if opcao_periodo == "Exercício Atual":
    if mes >= 7:
        data_inicial = pd.to_datetime(date(ano, 7, 1))
        data_final = pd.to_datetime(date(ano + 1, 6, 30))
    else:
        data_inicial = pd.to_datetime(date(ano - 1, 7, 1))
        data_final = pd.to_datetime(date(ano, 6, 30))
elif opcao_periodo == "Exercício Anterior":
    if mes >= 7:
        data_inicial = pd.to_datetime(date(ano - 1, 7, 1))
        data_final = pd.to_datetime(date(ano, 6, 30))
    else:
        data_inicial = pd.to_datetime(date(ano - 2, 7, 1))
        data_final = pd.to_datetime(date(ano - 1, 6, 30))
elif opcao_periodo == "Ano Móvel":
    data_final = hoje
    data_inicial = hoje - pd.DateOffset(months=12)
else:  # Personalizado
    data_inicial, data_final = st.sidebar.date_input(
        "Selecione o intervalo de datas:",
        value=[hoje - pd.Timedelta(days=7), hoje]
    )

df_dia = df[
    (df["DT_ENTRADA"] >= pd.to_datetime(data_inicial)) &
    (df["DT_ENTRADA"] <= pd.to_datetime(data_final))
]

# Filtros adicionais
col1, col2, col3 = st.columns(3)
with col1:
    nome = st.selectbox("🔍 Filtrar por Nome", ["Todos"] + sorted(df_dia["NOME"].dropna().unique().tolist()))
with col2:
    area = st.selectbox("🏭 Filtrar por Área (DES_N3)", ["Todos"] + sorted(df_dia["DES_N3"].dropna().unique().tolist()))
with col3:
    teste_real = st.multiselect(
        "🧪 Filtrar por Teste Real",
        sorted(df_dia["TESTE_REAL"].dropna().unique().tolist()),
        default=sorted(df_dia["TESTE_REAL"].dropna().unique().tolist())
    )

if nome != "Todos":
    df_dia = df_dia[df_dia["NOME"] == nome]
if area != "Todos":
    df_dia = df_dia[df_dia["DES_N3"] == area]
if teste_real:
    df_dia = df_dia[df_dia["TESTE_REAL"].isin(teste_real)]

# Segmentação
fizeram = df_dia[df_dia["TESTE_REAL"] == "TESTE NO HORÁRIO"]
faltaram = df_dia[df_dia["TESTE_REAL"] == "NÃO REALIZOU"]
tardio = df_dia[df_dia["TESTE_REAL"] == "TESTE TARDIO"]

# Métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("✅ Testes Realizados", len(fizeram))
with col2:
    st.metric("⚠️ Sem Teste Realizado", len(faltaram))
with col3:
    st.metric("⚠️ Teste Tardio", len(tardio))

# Cards por tipo de teste
st.subheader("📦 Resumo por Tipo de Teste")
tipos_teste = df_dia["TESTE_REAL"].value_counts().to_dict()
colunas = st.columns(len(tipos_teste))
for i, (tipo, qtd) in enumerate(tipos_teste.items()):
    with colunas[i]:
        st.markdown(
            f"""
            <div style="border:1px solid #bbb; border-radius:8px; padding:12px; text-align:center; background-color:#fafafa;">
                <div style="font-size:18px; font-weight:bold;">{tipo.title()}</div>
                <div style="font-size:28px; color:#FF6600; font-weight:bold;">{qtd}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Tabela de faltantes
# st.subheader("👷 Empregados sem teste (sujeitos à sanção)")
# st.dataframe(faltaram[["MATRICULA", "NOME", "DES_N1", "DES_N2", "DES_N3", "DES_N4", "DES_N5", "DT_ENTRADA", "TESTE_REAL"]])

# Nova tabela: todos (fizeram e faltaram)
# st.subheader("📑 Todos os empregados (Realizaram e Não Realizaram)")
# st.dataframe(
#     df_dia[["MATRICULA", "NOME", "DES_N1", "DES_N2", "DES_N3", "DES_N4", "DES_N5", "DT_ENTRADA", "TESTE_REAL"]]
# )

# Checkbox para exibir o mapa de calor
mostrar_heatmap = st.checkbox("Exibir Mapa de Calor", value=True)
if mostrar_heatmap:
    st.subheader("📊 Mapa de Calor: Área x Tipo de Teste Realizado")
    heatmap_data = df_dia.pivot_table(
        index="DES_N3",
        columns="TESTE_REAL",
        values="MATRICULA",
        aggfunc="count",
        fill_value=0
    )
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Tipo de Teste", y="Área (DES_N3)", color="Quantidade"),
        color_continuous_scale="YlGnBu",
        aspect="auto",
        title="Mapa de Calor: Área x Tipo de Teste Realizado"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# Checkbox para exibir o gráfico evolutivo
mostrar_evolucao = st.checkbox("Exibir Gráfico Evolutivo", value=True)
if mostrar_evolucao:
    st.subheader("📈 Evolução Diária dos Testes e Aderência")
    df_evolucao = df_dia.copy()
    df_evolucao["Data"] = df_evolucao["DT_ENTRADA"].dt.date

    # Agrupa por data e status
    evolucao = df_evolucao.groupby(["Data", "TESTE_REAL"])["MATRICULA"].count().reset_index()
    pivot = evolucao.pivot(index="Data", columns="TESTE_REAL", values="MATRICULA").fillna(0)

    # Calcula aderência (% de TESTE NO HORÁRIO sobre o total do dia)
    pivot["Total"] = pivot.sum(axis=1)
    if "TESTE NO HORÁRIO" in pivot.columns:
        pivot["Aderência (%)"] = (pivot["TESTE NO HORÁRIO"] / pivot["Total"] * 100).round(1)
    else:
        pivot["Aderência (%)"] = 0
    # Calcula a média móvel de 7 dias da aderência
    pivot["Aderência Móvel (%)"] = pivot["Aderência (%)"].rolling(7, min_periods=1).mean().round(1)

    # Paleta Ternium (ajuste conforme necessário)
    ternium_colors = {
        "TESTE NO HORÁRIO": "#FF6600",   # Laranja Ternium
        "NÃO REALIZOU": "#666666",       # Cinza escuro
        "TESTE TARDIO": "#009640",       # Verde Ternium
        "OUTROS": "#000000"              # Preto (para outros status)
    }

    fig = go.Figure()

    # Barras empilhadas para todos os status (exceto Total e Aderência)
    for status in pivot.columns:
        if status not in ["Total", "Aderência (%)", "Aderência Móvel (%)"]:
            if status == "TESTE NO HORÁRIO":
                color = "#FF6600"  # Laranja Ternium
            elif status == "NÃO REALIZOU":
                color = "#666666"  # Cinza Ternium
            elif status == "TESTE TARDIO":
                color = "#FFD100"  # Amarelo Ternium
            else:
                color = "#BBBBBB"  # Cinza claro para outros
            fig.add_trace(go.Bar(
                x=pivot.index,
                y=pivot[status],
                name=status,
                marker_color=color,
                yaxis="y1"
            ))

    # Linha de aderência (%)
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=pivot["Aderência (%)"],
        mode="lines+markers",
        name="Aderência (%)",
        yaxis="y2",
        line=dict(color="#005288", dash="dash")  # Azul institucional para aderência
    ))

    # Linha da média móvel da aderência
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=pivot["Aderência Móvel (%)"],
        mode="lines",
        name="Média Móvel (7d) Aderência",
        yaxis="y2",
        line=dict(color="#FF6600", width=4, dash="dot")  # Laranja Ternium, linha pontilhada
    ))


    # Barras empilhadas para todos os status (exceto Total e Aderência)
    for status in pivot.columns:
        if status not in ["Total", "Aderência (%)", "Aderência Móvel (%)"]:
            if status == "TESTE NO HORÁRIO":
                color = "#FF6600"  # Laranja Ternium
            elif status == "NÃO REALIZOU":
                color = "#666666"  # Cinza Ternium
            elif status == "TESTE TARDIO":
                color = "#FFD100"  # Amarelo Ternium
            else:
                color = "#BBBBBB"  # Cinza claro para outros
            fig.add_trace(go.Bar(
                x=pivot.index,
                y=pivot[status],
                name=status,
                marker_color=color,
                yaxis="y1"
            ))

    # Linha de aderência (%)
    fig.add_trace(go.Scatter(
        x=pivot.index,
        y=pivot["Aderência (%)"],
        mode="lines+markers",
        name="Aderência (%)",
        yaxis="y2",
        line=dict(color="#005288", dash="dash")  # Azul institucional para aderência
    ))

    # Layout com barras empilhadas e dois eixos y
    fig.update_layout(
        barmode="stack",
        title="Evolução Diária: Status dos Testes (Barras Empilhadas) e Aderência (%)",
        xaxis_title="Data",
        yaxis=dict(title="Quantidade", side="left"),
        yaxis2=dict(title="Aderência (%)", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)


