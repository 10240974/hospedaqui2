import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date, datetime
import io
import calendar

# ---------- BANCO DE DADOS ----------
def conectar():
    return sqlite3.connect("hospedagem.db", check_same_thread=False)

def inicializar_db():
    conn = conectar()
    c = conn.cursor()
    # Unidades
    c.execute("""
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            localizacao TEXT,
            capacidade INTEGER,
            status TEXT
        )
    """)
    # Locações
    c.execute("""
        CREATE TABLE IF NOT EXISTS locacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            checkin DATE,
            checkout DATE,
            hospede TEXT,
            valor REAL,
            plataforma TEXT,
            status_pagamento TEXT,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    # Despesas
    c.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            data DATE,
            tipo TEXT,
            valor REAL,
            descricao TEXT,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    # Precificação
    c.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            temporada TEXT,
            preco_base REAL,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

# ---------- FUNÇÕES AUXILIARES ----------
def get_unidades():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM unidades", conn)
    conn.close()
    return df

def get_locacoes():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM locacoes", conn)
    conn.close()
    return df

def get_despesas():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    return df

def get_precos():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM precos", conn)
    conn.close()
    return df

def calcular_repasse(valor):
    taxa = 0.20
    return valor * (1 - taxa)

# ---------- INTERFACE ----------
st.set_page_config(page_title="Controle de Hospedagem", layout="wide")
st.title("🏠 Controle de Hospedagem ")


# Inicio Dash

import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import calendar

# ---------- BANCO DE DADOS ----------
def conectar():
    return sqlite3.connect("hospedagem.db", check_same_thread=False)

def inicializar_db():
    conn = conectar()
    c = conn.cursor()
    # Unidades
    c.execute("""
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            localizacao TEXT,
            capacidade INTEGER,
            status TEXT
        )
    """)
    # Locações
    c.execute("""
        CREATE TABLE IF NOT EXISTS locacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            checkin DATE,
            checkout DATE,
            hospede TEXT,
            valor REAL,
            plataforma TEXT,
            status_pagamento TEXT,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    # Despesas
    c.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            data DATE,
            tipo TEXT,
            valor REAL,
            descricao TEXT,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    # Precificação
    c.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id INTEGER,
            temporada TEXT,
            preco_base REAL,
            FOREIGN KEY(unidade_id) REFERENCES unidades(id)
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

# ---------- FUNÇÕES AUXILIARES ----------
def get_unidades():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM unidades", conn)
    conn.close()
    return df

def get_locacoes():
    conn = conectar()
    df = pd.read_sql("SELECT * FROM locacoes", conn)
    conn.close()
    return df

def calcular_repasse(valor):
    taxa = 0.20
    return valor * (1 - taxa)

# ---------- INTERFACE ----------
st.set_page_config(page_title="Controle de Hospedagem", layout="wide")
#st.title("🏠 Controle de Hospedagem")

# ---------- DASHBOARD DE OCUPAÇÃO ----------
st.title("🏠 Dashboard de Ocupação - Visão Geral")

ano_dash = st.number_input("Ano", min_value=2000, max_value=2100, value=date.today().year)
unidades_dash = get_unidades()
locacoes_dash = get_locacoes()

st.subheader("Filtro de Período")
col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data inicial", value=date.today().replace(day=1))
with col2:
    data_fim = st.date_input("Data final", value=date.today())

dias_periodo = pd.date_range(start=data_inicio, end=data_fim)
dias = [d.strftime("%d/%m") for d in dias_periodo]

unidades_opcoes = list(unidades_dash["nome"])
unidades_selecionadas = st.multiselect("Unidades", unidades_opcoes, default=unidades_opcoes)

# Filtra as unidades para a matriz
if unidades_selecionadas:
    unidades_dash_filtrado = unidades_dash[unidades_dash["nome"].isin(unidades_selecionadas)]
else:
    unidades_dash_filtrado = unidades_dash

# Filtro de plataforma
plataformas_opcoes = ["Todas"] + sorted(locacoes_dash["plataforma"].unique())
plataforma_filtro = st.selectbox("Plataforma", plataformas_opcoes, key="dash_plataforma")

# Filtro de unidade baseado no nome (correto)
unidade_filtro = st.selectbox("Unidade", ["Todas"] + unidades_dash["nome"].tolist(), key="dash_unidade_filtro")

# 🔧 Aplicar filtro de unidade
if unidade_filtro != "Todas":
    # Obtem o ID correspondente ao nome da unidade
    unidade_id = unidades_dash[unidades_dash["nome"] == unidade_filtro]["id"].values[0]
    locacoes_dash = locacoes_dash[locacoes_dash["unidade_id"] == unidade_id]

# 🔧 Aplicar filtro de plataforma
if plataforma_filtro != "Todas":
    locacoes_dash = locacoes_dash[locacoes_dash["plataforma"] == plataforma_filtro]



# Inicializa matrizes
tabela = pd.DataFrame("", index=unidades_dash_filtrado["nome"], columns=dias)
valores = pd.DataFrame(0.0, index=unidades_dash_filtrado["nome"], columns=dias)

# Preenche ocupação e valores
for _, unidade in unidades_dash_filtrado.iterrows():
    locs = locacoes_dash[locacoes_dash["unidade_id"] == unidade["id"]]
    for _, loc in locs.iterrows():
        checkin = pd.to_datetime(loc["checkin"]).date()
        checkout = pd.to_datetime(loc["checkout"]).date()
        valor = loc["valor"]

        # Ajuste: Excluir o dia do checkout para contagem de valor
        if checkin == checkout:
            dias_locados = []  # sem valor
        else:
            dias_locados = pd.date_range(checkin, checkout - pd.Timedelta(days=1)).date

        valor_dia = valor / len(dias_locados) if len(dias_locados) > 0 else 0

        for d in dias_locados:
            dia_str = d.strftime("%d/%m")
            if dia_str in dias:
                tabela.loc[unidade["nome"], dia_str] = "🟧"
                valores.loc[unidade["nome"], dia_str] += valor_dia

        # Marcação de Check-in
        if data_inicio <= checkin <= data_fim:
            dia_checkin = checkin.strftime("%d/%m")
            if dia_checkin in dias:
                tabela.loc[unidade["nome"], dia_checkin] = "🟦"

        # Marcação de Check-out (sem somar valor)
        if data_inicio <= checkout <= data_fim:
            dia_checkout = checkout.strftime("%d/%m")
            if dia_checkout in dias:
                tabela.loc[unidade["nome"], dia_checkout] = "◧"

# Totais
valores.loc["Total R$"] = valores.sum(axis=0)
valores["Total R$"] = valores.sum(axis=1)
tabela.loc["Total R$"] = ""
tabela["Total R$"] = ""

# Cria visualização com ícones + valores
tabela_visual = tabela.copy()
for row in tabela.index:
    for col in tabela.columns:
        val = valores.loc[row, col]
        if val > 0:
            icone = tabela_visual.loc[row, col]
            tabela_visual.loc[row, col] = f"{icone}  {val:,.2f}" if icone else f" {val:,.2f}"

# Tooltips
tooltips = pd.DataFrame("", index=valores.index, columns=valores.columns)
for row in valores.index:
    for col in valores.columns:
        val = valores.loc[row, col]
        if val > 0:
            tooltips.loc[row, col] = f"Valor:  {val:,.2f}"

# Adiciona coluna "Valor Líquido (-13%)" ao final da matriz de valores
valores["Valor Líquido (-13%)"] = valores["Total R$"] * 0.87

# Adiciona coluna "Total Administradora (20%)" ao final da matriz de valores
valores["Total Administradora (20%)"] = valores["Total R$"] * 0.20

# Formata os valores com duas casas decimais
valores = valores.applymap(lambda v: f"{v:,.2f}")

# Adiciona coluna vazia correspondente na matriz de ícones (tabela)
tabela["Valor Líquido (-13%)"] = ""
tabela["Total Administradora (20%)"] = ""

# Atualiza tabela_visual para incluir as novas colunas
tabela_visual["Valor Líquido (-13%)"] = valores["Valor Líquido (-13%)"]
tabela_visual["Total Administradora (20%)"] = valores["Total Administradora (20%)"]

# Exibição
html_tabela = tabela_visual.style.set_caption(
    f"Ocupação Geral ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})"
).set_tooltips(tooltips).to_html(escape=False)

st.markdown(html_tabela, unsafe_allow_html=True)

st.markdown("""
**Legenda:**
- 🟧 Ocupado o dia todo (com valor)  
- 🟦 Check-in (após 14h)  
- ◧ Check-out (até 11h — sem valor)
""")


#fimmmmmm


aba = st.sidebar.radio("Menu", [
    "Cadastro de Unidades",
    "Locações",
    "Despesas",
    "Precificação",
    "Dashboard de Ocupação",
    "Relatório de Despesas"
])

# ---------- CADASTRO DE UNIDADES ----------
if aba == "Cadastro de Unidades":
    st.header("Cadastro e Controle de Unidades")
    with st.form("cad_unidade"):
        nome = st.text_input("Nome da Unidade")
        localizacao = st.text_input("Localização")
        capacidade = st.number_input("Capacidade", min_value=1, max_value=20, value=4)
        status = st.selectbox("Status", ["Disponível", "Ocupado", "Manutenção"])
        enviar = st.form_submit_button("Cadastrar")
        if enviar and nome:
            conn = conectar()
            conn.execute("INSERT INTO unidades (nome, localizacao, capacidade, status) VALUES (?, ?, ?, ?)",
                         (nome, localizacao, capacidade, status))
            conn.commit()
            conn.close()
            st.success("Unidade cadastrada!")

    st.subheader("Unidades Cadastradas")
    st.dataframe(get_unidades())

# ---------- LOCAÇÕES ----------
elif aba == "Locações":
    st.header("Cadastro e Importação de Locações")
    unidades = get_unidades()
    with st.form("cad_locacao"):
        unidade = st.selectbox("Unidade", unidades["nome"] if not unidades.empty else [])
        checkin = st.date_input("Data Check-in", value=date.today())
        checkout = st.date_input("Data Check-out", value=date.today())
        hospede = st.text_input("Hóspede")
        valor = st.number_input("Valor Total da Reserva", min_value=0.0, format="%.2f")
        plataforma = st.selectbox("Plataforma", ["Airbnb", "Booking", "Direto"])
        status_pagamento = st.selectbox("Status do Pagamento", ["Pendente", "Pago"])
        enviar = st.form_submit_button("Cadastrar Locação")
        if enviar and unidade:
            unidade_id = int(unidades[unidades["nome"] == unidade]["id"].values[0])
            conn = conectar()
            conn.execute(
                "INSERT INTO locacoes (unidade_id, checkin, checkout, hospede, valor, plataforma, status_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (unidade_id, str(checkin), str(checkout), hospede, valor, plataforma, status_pagamento)
            )
            conn.commit()
            conn.close()
            st.success("Locação cadastrada!")

    st.subheader("Importar Locações (CSV)")
    csv_file = st.file_uploader("Importar CSV", type="csv")
    if csv_file:
        df_csv = pd.read_csv(csv_file)
        st.dataframe(df_csv)
        if st.button("Importar para o sistema"):
            conn = conectar()
            for _, row in df_csv.iterrows():
                unidade_id = int(unidades[unidades["nome"] == row["unidade"]]["id"].values[0])
                conn.execute(
                    "INSERT INTO locacoes (unidade_id, checkin, checkout, hospede, valor, plataforma, status_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (unidade_id, row["checkin"], row["checkout"], row["hospede"], row["valor"], row["plataforma"], row["status_pagamento"])
                )
            conn.commit()
            conn.close()
            st.success("Locações importadas!")

    st.subheader("Locações Registradas")

    # Filtro de unidade para locações
    unidades_lista = ["Todas"] + unidades["nome"].tolist()
    unidade_loca_filtro = st.selectbox("Filtrar por unidade", unidades_lista, key="locacoes_unidade_filtro")

    # Filtro de mês
    meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
    mes_loca_filtro = st.selectbox("Filtrar por mês de check-in", meses_lista, key="locacoes_mes_filtro")

    locacoes = get_locacoes().merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))
    if unidade_loca_filtro != "Todas":
        locacoes = locacoes[locacoes["nome"] == unidade_loca_filtro]
    if mes_loca_filtro != "Todos":
        locacoes = locacoes[pd.to_datetime(locacoes["checkin"]).dt.month == int(mes_loca_filtro)]

    # Tabela editável
    edited_df = st.data_editor(
        locacoes[["id", "nome", "checkin", "checkout", "hospede", "valor", "plataforma", "status_pagamento"]],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_locacoes"
    )

    # Botão para salvar alterações
    if st.button("Salvar Alterações nas Locações"):
        conn = conectar()
        for idx, row in edited_df.iterrows():
            conn.execute(
                "UPDATE locacoes SET checkin=?, checkout=?, hospede=?, valor=?, plataforma=?, status_pagamento=? WHERE id=?",
                (row["checkin"], row["checkout"], row["hospede"], row["valor"], row["plataforma"], row["status_pagamento"], row["id"])
            )
        conn.commit()
        conn.close()
        st.success("Alterações salvas! Recarregue a página para ver os dados atualizados.")

    # Botão para excluir locação selecionada
    st.subheader("Excluir Locação")
    id_excluir = st.selectbox("Selecione o ID da locação para excluir", locacoes["id"])
    if st.button("Excluir Locação"):
        conn = conectar()
        conn.execute("DELETE FROM locacoes WHERE id=?", (id_excluir,))
        conn.commit()
        conn.close()
        st.success(f"Locação {id_excluir} excluída!")

# ---------- DESPESAS ----------
elif aba == "Despesas":
    st.header("Registro de Despesas")
    unidades = get_unidades()
    with st.form("cad_despesa"):
        unidade = st.selectbox("Unidade", unidades["nome"] if not unidades.empty else [])
        data_desp = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Prestação", "Condominio","Luz","Internet","Gás","Administradora","Limpeza", "Manutenção", "Insumos", "Outros"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        enviar = st.form_submit_button("Registrar Despesa")
        if enviar and unidade:
            unidade_id = int(unidades[unidades["nome"] == unidade]["id"].values[0])
            conn = conectar()
            conn.execute(
                "INSERT INTO despesas (unidade_id, data, tipo, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                (unidade_id, str(data_desp), tipo, valor, descricao)
            )
            conn.commit()
            conn.close()
            st.success("Despesa registrada!")

    st.subheader("Despesas Registradas")
    despesas = get_despesas().merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))

    # Filtros de unidade e mês
    unidades_opcoes = list(unidades["nome"])
    unidade_filtro = st.selectbox("Filtrar por unidade", ["Todas"] + unidades_opcoes, key="despesa_unidade_filtro")
    meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
    mes_filtro = st.selectbox("Filtrar por mês", meses_lista, key="despesa_mes_filtro")

    despesas_filtradas = despesas.copy()
    if unidade_filtro != "Todas":
        despesas_filtradas = despesas_filtradas[despesas_filtradas["nome"] == unidade_filtro]
    if mes_filtro != "Todos":
        despesas_filtradas = despesas_filtradas[pd.to_datetime(despesas_filtradas["data"]).dt.month == int(mes_filtro)]

    # Tabela editável
    edited_df = st.data_editor(
        despesas_filtradas[["id", "nome", "data", "tipo", "valor", "descricao"]],
        num_rows="dynamic",
        use_container_width=True,
        key="editor_despesas"
    )

    # Botão para salvar alterações
    if st.button("Salvar Alterações nas Despesas"):
        conn = conectar()
        for idx, row in edited_df.iterrows():
            conn.execute(
                "UPDATE despesas SET data=?, tipo=?, valor=?, descricao=? WHERE id=?",
                (row["data"], row["tipo"], row["valor"], row["descricao"], row["id"])
            )
        conn.commit()
        conn.close()
        st.success("Alterações salvas! Recarregue a página para ver os dados atualizados.")

    # Botão para excluir despesa selecionada
    st.subheader("Excluir Despesa")
    id_excluir = st.selectbox("Selecione o ID da despesa para excluir", despesas_filtradas["id"])
    if st.button("Excluir Despesa"):
        conn = conectar()
        conn.execute("DELETE FROM despesas WHERE id=?", (id_excluir,))
        conn.commit()
        conn.close()
        st.success(f"Despesa {id_excluir} excluída!")

    # Botão para copiar despesa selecionada
    st.subheader("Copiar Despesa")
    id_copiar = st.selectbox("Selecione o ID da despesa para copiar", despesas_filtradas["id"], key="copiar_despesa")
    if st.button("Copiar Despesa"):
        despesa_copiar = despesas_filtradas[despesas_filtradas["id"] == id_copiar].iloc[0]
        conn = conectar()
        conn.execute(
            "INSERT INTO despesas (unidade_id, data, tipo, valor, descricao) VALUES (?, ?, ?, ?, ?)",
            (despesa_copiar["unidade_id"], despesa_copiar["data"], despesa_copiar["tipo"], despesa_copiar["valor"], despesa_copiar["descricao"])
        )
        conn.commit()
        conn.close()
        st.success(f"Despesa {id_copiar} copiada!")

# ---------- PRECIFICAÇÃO ----------
elif aba == "Precificação":
    st.header("Cadastro de Preços Base por Unidade e Temporada")
    unidades = get_unidades()
    with st.form("cad_preco"):
        unidade = st.selectbox("Unidade", unidades["nome"] if not unidades.empty else [])
        temporada = st.selectbox("Temporada", ["Baixa", "Média", "Alta"])
        preco_base = st.number_input("Preço Base", min_value=0.0, format="%.2f")
        enviar = st.form_submit_button("Cadastrar Preço")
        if enviar and unidade:
            unidade_id = int(unidades[unidades["nome"] == unidade]["id"].values[0])
            conn = conectar()
            conn.execute(
                "INSERT INTO precos (unidade_id, temporada, preco_base) VALUES (?, ?, ?)",
                (unidade_id, temporada, preco_base)
            )
            conn.commit()
            conn.close()
            st.success("Preço cadastrado!")

    st.subheader("Preços Base Cadastrados")
    precos = get_precos().merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))
    st.dataframe(precos[["nome", "temporada", "preco_base"]])

    st.subheader("Simulação de Valor de Locação")
    unidade_sim = st.selectbox("Unidade para Simulação", unidades["nome"] if not unidades.empty else [], key="simul")
    temporada_sim = st.selectbox("Temporada para Simulação", ["Baixa", "Média", "Alta"], key="simul2")
    ocupacao = st.slider("Taxa de Ocupação (%)", 0, 100, 70)
    if unidade_sim:
        preco = precos[(precos["nome"] == unidade_sim) & (precos["temporada"] == temporada_sim)]["preco_base"]
        if not preco.empty:
            valor_sim = preco.values[0] * (ocupacao / 100)
            st.info(f"Valor simulado para {unidade_sim} ({temporada_sim}): R$ {valor_sim:,.2f}")



# ---------- RELATÓRIO DE DESPESAS ----------
if aba == "Relatório de Despesas":
    st.header("Relatório de Receita e Despesa por Unidade e Mês (Detalhado por Tipo de Despesa)")

    unidades = get_unidades()
    despesas = get_despesas().merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))
    locacoes = get_locacoes().merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))

    # Filtros
    unidades_opcoes = list(unidades["nome"])
    unidades_selecionadas = st.multiselect("Unidades", unidades_opcoes, default=unidades_opcoes, key="desp_relat_unidades")
    meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
    mes_filtro = st.selectbox("Filtrar por mês", meses_lista, key="desp_relat_mes")
    tipos_opcoes = ["Todos"] + sorted(despesas["tipo"].unique())
    tipo_filtro = st.selectbox("Filtrar por tipo de despesa", tipos_opcoes, key="desp_relat_tipo")

    # Prepara dados
    locacoes["mes"] = pd.to_datetime(locacoes["checkin"]).dt.month
    locacoes["ano"] = pd.to_datetime(locacoes["checkin"]).dt.year
    despesas["mes"] = pd.to_datetime(despesas["data"]).dt.month
    despesas["ano"] = pd.to_datetime(despesas["data"]).dt.year

    # Aplica filtros
    if unidades_selecionadas:
        locacoes = locacoes[locacoes["nome"].isin(unidades_selecionadas)]
        despesas = despesas[despesas["nome"].isin(unidades_selecionadas)]
    if mes_filtro != "Todos":
        locacoes = locacoes[locacoes["mes"] == int(mes_filtro)]
        despesas = despesas[despesas["mes"] == int(mes_filtro)]

    # Agrupamentos
    receita = locacoes.groupby(["nome", "ano", "mes"])["valor"].sum().reset_index()
    receita = receita.rename(columns={"valor": "Receita Bruta"})

    despesa = despesas.groupby(["nome", "ano", "mes", "tipo"])["valor"].sum().reset_index()
    despesa = despesa.rename(columns={"valor": "Despesa"})

    # Combina todas as chaves possíveis
    chaves = pd.concat([
        receita[["nome", "ano", "mes"]],
        despesa[["nome", "ano", "mes"]].drop_duplicates()
    ]).drop_duplicates().reset_index(drop=True)

    relatorio = chaves.copy()

    # Junta receita
    relatorio = relatorio.merge(receita, on=["nome", "ano", "mes"], how="left")
    relatorio["Receita Bruta"] = relatorio["Receita Bruta"].fillna(0)

    # Junta despesas por tipo
    tipos_despesa = despesa["tipo"].unique()
    for tipo in tipos_despesa:
        filtro = despesa[despesa["tipo"] == tipo]
        coluna = filtro.groupby(["nome", "ano", "mes"])["Despesa"].sum().reset_index()
        coluna = coluna.rename(columns={"Despesa": tipo})
        relatorio = relatorio.merge(coluna, on=["nome", "ano", "mes"], how="left")

    relatorio.fillna(0, inplace=True)

    # Totais e lucro
    relatorio["Total Despesas"] = relatorio[list(tipos_despesa)].sum(axis=1)
    relatorio["Lucro Líquido"] = relatorio["Receita Bruta"] - relatorio["Total Despesas"]

    # Seleciona colunas a exibir
    if tipo_filtro != "Todos" and tipo_filtro in relatorio.columns:
        colunas = ["nome", "ano", "mes", "Receita Bruta", tipo_filtro, "Total Despesas", "Lucro Líquido"]
    else:
        colunas = ["nome", "ano", "mes", "Receita Bruta"] + list(tipos_despesa) + ["Total Despesas", "Lucro Líquido"]

    # Formata os valores
    for col in colunas[3:]:
        relatorio[col] = relatorio[col].map(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # ------ TOTAIS GERAIS ------
    # Função auxiliar para limpar e converter valores
    def limpar_valor(col):
        return (
            relatorio[col]
            .str.replace("R\$", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

    total_receita = limpar_valor("Receita Bruta").sum()
    total_despesas = limpar_valor("Total Despesas").sum()
    total_lucro = limpar_valor("Lucro Líquido").sum()

    # Totais por tipo de despesa
    totais_tipos = {}
    for tipo in tipos_despesa:
        if tipo in relatorio.columns:
            totais_tipos[tipo] = limpar_valor(tipo).sum()

    # Cria linha de total
    linha_total = {colunas[0]: "TOTAL", colunas[1]: "", colunas[2]: ""}
    for col in colunas[3:]:
        if col == "Receita Bruta":
            linha_total[col] = f"R$ {total_receita:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif col == "Total Despesas":
            linha_total[col] = f"R$ {total_despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif col == "Lucro Líquido":
            linha_total[col] = f"R$ {total_lucro:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        elif col in totais_tipos:
            total = totais_tipos[col]
            linha_total[col] = f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Junta com o DataFrame final
    relatorio_total = pd.concat([relatorio[colunas], pd.DataFrame([linha_total])], ignore_index=True)

    st.dataframe(relatorio_total, use_container_width=True)

#Fim relatorio de despesas



# ---- GRÁFICOS COMPARATIVOS E INTERATIVOS ----
st.subheader("Gráficos Comparativos de Receita, Despesa e Lucro")

relatorio_numerico = relatorio.copy()

# Converte colunas principais de moeda para float
for col in ["Receita Bruta", "Total Despesas", "Lucro Líquido"]:
    if col in relatorio_numerico.columns and relatorio_numerico[col].dtype == object:
        relatorio_numerico[col] = (
            relatorio_numerico[col]
            .astype(str)
            .str.replace("R\$", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

# Converte tipos de despesa
for col in tipos_despesa:
    if relatorio_numerico[col].dtype == object:
        relatorio_numerico[col] = (
            relatorio_numerico[col]
            .astype(str)
            .str.replace("R\$", "", regex=True)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

# Recalcula total e lucro líquido
relatorio_numerico["Total Despesas"] = relatorio_numerico[list(tipos_despesa)].sum(axis=1)
relatorio_numerico["Lucro Líquido"] = relatorio_numerico["Receita Bruta"] - relatorio_numerico["Total Despesas"]

# Opções de agrupamento
agrupamento = st.selectbox("Agrupar gráficos por", ["Unidade", "Mês", "Unidade e Mês"], key="grafico_agrupamento")

# Criação da chave de agrupamento
if agrupamento == "Unidade":
    relatorio_numerico["Chave"] = relatorio_numerico["nome"]
elif agrupamento == "Mês":
    relatorio_numerico["Chave"] = relatorio_numerico["mes"].astype(str).str.zfill(2) + "/" + relatorio_numerico["ano"].astype(str)
elif agrupamento == "Unidade e Mês":
    relatorio_numerico["Chave"] = (
        relatorio_numerico["nome"] + " - " +
        relatorio_numerico["mes"].astype(str).str.zfill(2) + "/" +
        relatorio_numerico["ano"].astype(str)
    )

# Agrupamento principal
grafico_df = relatorio_numerico.groupby("Chave")[["Receita Bruta", "Total Despesas", "Lucro Líquido"]].sum().reset_index()

# Gráfico de Barras: Receita x Despesas x Lucro
grafico_meltado = grafico_df.melt(
    id_vars="Chave",
    value_vars=["Receita Bruta", "Total Despesas", "Lucro Líquido"],
    var_name="Categoria",
    value_name="Valor"
)

fig = px.bar(
    grafico_meltado,
    x="Chave",
    y="Valor",
    color="Categoria",
    barmode="group",
    title="Receita x Despesas x Lucro"
)
fig.update_layout(xaxis_title=agrupamento, yaxis_title="Valor (R$)", xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# Gráfico de Percentual de Lucro
st.subheader("Margem de Lucro (%)")
grafico_df["Margem (%)"] = grafico_df.apply(
    lambda row: (row["Lucro Líquido"] / row["Receita Bruta"] * 100) if row["Receita Bruta"] > 0 else 0,
    axis=1
)

fig_margem = px.bar(
    grafico_df,
    x="Chave",
    y="Margem (%)",
    text="Margem (%)",
    title="Percentual de Lucro por " + agrupamento,
    labels={"Chave": agrupamento}
)
fig_margem.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
fig_margem.update_layout(yaxis_title="Margem (%)", xaxis_tickangle=-45)
st.plotly_chart(fig_margem, use_container_width=True)

# Gráfico de Pizza: Composição dos Tipos de Despesa
st.subheader("Composição dos Tipos de Despesa")
despesas_totais_por_tipo = relatorio_numerico[tipos_despesa].sum().sort_values(ascending=False)
df_pizza = pd.DataFrame({
    "Tipo": despesas_totais_por_tipo.index,
    "Valor": despesas_totais_por_tipo.values
})

fig_pizza = px.pie(
    df_pizza,
    names="Tipo",
    values="Valor",
    title="Distribuição das Despesas por Tipo",
    hole=0.4
)
st.plotly_chart(fig_pizza, use_container_width=True)