# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import date
import calendar

# ---------- CONFIGURAÇÃO DA PÁGINA ----------
st.set_page_config(page_title="Controle de Hospedagem", layout="wide")

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

# ---------- MENU LATERAL OTIMIZADO ----------
st.sidebar.title("📌 Menu Principal")

menu_principal = st.sidebar.radio("", [
    "🏠 Dashboard",
    "📊 Relatórios",
    "🗂 Gestão de Dados",
    "⚙️ Configurações"
])

if menu_principal == "🏠 Dashboard":
    aba = "Dashboard de Ocupação"

elif menu_principal == "📊 Relatórios":
    aba = st.sidebar.radio("📈 Tipo de Relatório", [
        "Relatório de Despesas",
        "Análise de Receita e Lucro"
    ])

elif menu_principal == "🗂 Gestão de Dados":
    aba = st.sidebar.radio("📁 Dados Cadastrais", [
        "Cadastro de Unidades",
        "Locações",
        "Despesas",
        "Precificação"
    ])

elif menu_principal == "⚙️ Configurações":
    aba = st.sidebar.radio("🔧 Opções do Sistema", [
        "Parâmetros do Sistema",
        "Exportar/Importar Dados",
        "Sobre o Sistema"
    ])

# =========================
#        DASHBOARD
# =========================
if aba == "Dashboard de Ocupação":
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

    # Faixa de dias do período
    dias_periodo = pd.date_range(start=data_inicio, end=data_fim, freq="D")
    dias_str = [d.strftime("%d/%m") for d in dias_periodo]

    # Filtro de unidades
    unidades_opcoes = unidades_dash["nome"].tolist() if not unidades_dash.empty else []
    unidades_selecionadas = st.multiselect("Unidades", unidades_opcoes, default=unidades_opcoes)

    # Aplica filtro de unidades para exibição
    if unidades_selecionadas:
        unidades_dash_filtrado = unidades_dash[unidades_dash["nome"].isin(unidades_selecionadas)]
    else:
        unidades_dash_filtrado = unidades_dash

    # Filtro de plataforma
    plataformas_opcoes = ["Todas"]
    if not locacoes_dash.empty and "plataforma" in locacoes_dash.columns:
        plataformas_opcoes += sorted([p for p in locacoes_dash["plataforma"].dropna().unique().tolist()])
    plataforma_filtro = st.selectbox("Plataforma", plataformas_opcoes, key="dash_plataforma")

    # Filtro de unidade por nome (para filtrar locações)
    unidade_filtro = st.selectbox("Unidade", ["Todas"] + unidades_dash["nome"].tolist() if not unidades_dash.empty else ["Todas"], key="dash_unidade_filtro")

    # Aplica filtro de unidade nas locações (por ID)
    if unidade_filtro != "Todas" and not unidades_dash.empty and not locacoes_dash.empty:
        unidade_id = unidades_dash.loc[unidades_dash["nome"] == unidade_filtro, "id"].values[0]
        locacoes_dash = locacoes_dash[locacoes_dash["unidade_id"] == unidade_id]

    # Aplica filtro de plataforma nas locações
    if plataforma_filtro != "Todas" and not locacoes_dash.empty:
        locacoes_dash = locacoes_dash[locacoes_dash["plataforma"] == plataforma_filtro]

    # Matrizes base (numéricas para cálculo e visuais para exibição)
    index_nomes = unidades_dash_filtrado["nome"].tolist() + ["Total R$"]
    colunas = dias_str + ["Total R$", "Valor Líquido (-13%)", "Total Administradora (20%)"]

    valores_num = pd.DataFrame(0.0, index=index_nomes, columns=dias_str)  # só dias
    tabela_icon = pd.DataFrame("", index=index_nomes, columns=dias_str)    # só dias

    # Preenche ocupação e valores
    if not unidades_dash_filtrado.empty and not locacoes_dash.empty:
        for _, unidade in unidades_dash_filtrado.iterrows():
            locs = locacoes_dash[locacoes_dash["unidade_id"] == unidade["id"]]
            for _, loc in locs.iterrows():
                # Converte datas
                checkin = pd.to_datetime(loc["checkin"]).date()
                checkout = pd.to_datetime(loc["checkout"]).date()
                valor = float(loc.get("valor", 0) or 0)

                # Se checkin == checkout, não há diárias
                if checkin == checkout:
                    dias_locados = []
                else:
                    # usa to_pydatetime e converte para date (evita erro com .date)
                    dr = pd.date_range(checkin, checkout - pd.Timedelta(days=1), freq="D").to_pydatetime()
                    dias_locados = [d.date() for d in dr]

                valor_dia = (valor / len(dias_locados)) if len(dias_locados) > 0 else 0.0

                # Preenche dias ocupados (🟧) + soma valor
                for d in dias_locados:
                    dia_str = d.strftime("%d/%m")
                    if dia_str in dias_str:
                        tabela_icon.loc[unidade["nome"], dia_str] = "🟧"
                        valores_num.loc[unidade["nome"], dia_str] += valor_dia

                # Marcação de Check-in (🟦)
                if data_inicio <= checkin <= data_fim:
                    dia_checkin = checkin.strftime("%d/%m")
                    if dia_checkin in dias_str:
                        tabela_icon.loc[unidade["nome"], dia_checkin] = "🟦"

                # Marcação de Check-out (◧) — sem somar valor
                if data_inicio <= checkout <= data_fim:
                    dia_checkout = checkout.strftime("%d/%m")
                    if dia_checkout in dias_str:
                        tabela_icon.loc[unidade["nome"], dia_checkout] = "◧"

    # Totais por linha e por coluna
    valores_num.loc["Total R$", dias_str] = valores_num[dias_str].sum(axis=0)
    valores_num["Total R$"] = valores_num[dias_str].sum(axis=1)
    valores_num["Valor Líquido (-13%)"] = valores_num["Total R$"] * 0.87
    valores_num["Total Administradora (20%)"] = valores_num["Total R$"] * 0.20

    # Monta a tabela visual (ícones + valores diários + colunas finais formatadas)
    tabela_visual = tabela_icon.copy()

    # Concatena as colunas extras (inicialmente vazias)
    for extra_col in ["Total R$", "Valor Líquido (-13%)", "Total Administradora (20%)"]:
        if extra_col not in tabela_visual.columns:
            tabela_visual[extra_col] = ""

    # Insere valores nos dias (ícone + valor quando houver)
    for r in tabela_icon.index:
        for c in dias_str:
            v = float(valores_num.loc[r, c])
            icone = tabela_icon.loc[r, c]
            if v > 0:
                tabela_visual.loc[r, c] = f"{icone} {v:,.2f}".strip()
            else:
                tabela_visual.loc[r, c] = icone

    # Formata as colunas de totais
    tabela_visual["Total R$"] = valores_num["Total R$"].map(lambda v: f"{v:,.2f}")
    tabela_visual["Valor Líquido (-13%)"] = valores_num["Valor Líquido (-13%)"].map(lambda v: f"{v:,.2f}")
    tabela_visual["Total Administradora (20%)"] = valores_num["Total Administradora (20%)"].map(lambda v: f"{v:,.2f}")

    # Ordena colunas para exibição
    tabela_visual = tabela_visual[dias_str + ["Total R$", "Valor Líquido (-13%)", "Total Administradora (20%)"]]

    st.markdown(f"**Ocupação Geral ({data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')})**")
    st.dataframe(tabela_visual, use_container_width=True)

    st.markdown("""
**Legenda:**
- 🟧 Ocupado o dia todo (com valor)  
- 🟦 Check-in (após 14h)  
- ◧ Check-out (até 11h — sem valor)
""")

# =========================
#   CADASTRO DE UNIDADES
# =========================
elif aba == "Cadastro de Unidades":
    st.header("Cadastro e Controle de Unidades")
    with st.form("cad_unidade"):
        nome = st.text_input("Nome da Unidade")
        localizacao = st.text_input("Localização")
        capacidade = st.number_input("Capacidade", min_value=1, max_value=20, value=4)
        status = st.selectbox("Status", ["Disponível", "Ocupado", "Manutenção"])
        enviar = st.form_submit_button("Cadastrar")
        if enviar and nome:
            conn = conectar()
            conn.execute(
                "INSERT INTO unidades (nome, localizacao, capacidade, status) VALUES (?, ?, ?, ?)",
                (nome, localizacao, capacidade, status)
            )
            conn.commit()
            conn.close()
            st.success("Unidade cadastrada!")

    st.subheader("Unidades Cadastradas")
    st.dataframe(get_unidades(), use_container_width=True)

# =========================
#         LOCAÇÕES
# =========================
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
            unidade_id = int(unidades.loc[unidades["nome"] == unidade, "id"].values[0])
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
    if csv_file is not None:
        df_csv = pd.read_csv(csv_file)
        st.dataframe(df_csv, use_container_width=True)
        if st.button("Importar para o sistema"):
            conn = conectar()
            for _, row in df_csv.iterrows():
                unidade_id = int(unidades.loc[unidades["nome"] == row["unidade"], "id"].values[0])
                conn.execute(
                    "INSERT INTO locacoes (unidade_id, checkin, checkout, hospede, valor, plataforma, status_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (unidade_id, row["checkin"], row["checkout"], row["hospede"], row["valor"], row["plataforma"], row["status_pagamento"])
                )
            conn.commit()
            conn.close()
            st.success("Locações importadas!")

    st.subheader("Locações Registradas")

    # Filtros
    unidades_lista = ["Todas"] + (unidades["nome"].tolist() if not unidades.empty else [])
    unidade_loca_filtro = st.selectbox("Filtrar por unidade", unidades_lista, key="locacoes_unidade_filtro")

    meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
    mes_loca_filtro = st.selectbox("Filtrar por mês de check-in", meses_lista, key="locacoes_mes_filtro")

    locacoes = get_locacoes()
    if not locacoes.empty and not unidades.empty:
        locacoes = locacoes.merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))

        if unidade_loca_filtro != "Todas":
            locacoes = locacoes[locacoes["nome"] == unidade_loca_filtro]
        if mes_loca_filtro != "Todos":
            locacoes = locacoes[pd.to_datetime(locacoes["checkin"]).dt.month == int(mes_loca_filtro)]

        edited_df = st.data_editor(
            locacoes[["id", "nome", "checkin", "checkout", "hospede", "valor", "plataforma", "status_pagamento"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_locacoes"
        )

        if st.button("Salvar Alterações nas Locações"):
            conn = conectar()
            for _, row in edited_df.iterrows():
                conn.execute(
                    "UPDATE locacoes SET checkin=?, checkout=?, hospede=?, valor=?, plataforma=?, status_pagamento=? WHERE id=?",
                    (row["checkin"], row["checkout"], row["hospede"], row["valor"], row["plataforma"], row["status_pagamento"], row["id"])
                )
            conn.commit()
            conn.close()
            st.success("Alterações salvas! Recarregue a página para ver os dados atualizados.")

        st.subheader("Excluir Locação")
        id_excluir = st.selectbox("Selecione o ID da locação para excluir", locacoes["id"])
        if st.button("Excluir Locação"):
            conn = conectar()
            conn.execute("DELETE FROM locacoes WHERE id=?", (int(id_excluir),))
            conn.commit()
            conn.close()
            st.success(f"Locação {id_excluir} excluída!")

    else:
        st.info("Cadastre unidades e locações para visualizar e editar aqui.")

# =========================
#         DESPESAS
# =========================
elif aba == "Despesas":
    st.header("Registro de Despesas")
    unidades = get_unidades()

    with st.form("cad_despesa"):
        unidade = st.selectbox("Unidade", unidades["nome"] if not unidades.empty else [])
        data_desp = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Prestação", "Condominio", "Luz", "Internet", "Gás", "Administradora", "Limpeza", "Manutenção", "Insumos", "Outros"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        enviar = st.form_submit_button("Registrar Despesa")
        if enviar and unidade:
            unidade_id = int(unidades.loc[unidades["nome"] == unidade, "id"].values[0])
            conn = conectar()
            conn.execute(
                "INSERT INTO despesas (unidade_id, data, tipo, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                (unidade_id, str(data_desp), tipo, valor, descricao)
            )
            conn.commit()
            conn.close()
            st.success("Despesa registrada!")

    st.subheader("Despesas Registradas")
    despesas = get_despesas()
    if not despesas.empty and not unidades.empty:
        despesas = despesas.merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))

        # Filtros
        unidades_opcoes = unidades["nome"].tolist()
        unidade_filtro = st.selectbox("Filtrar por unidade", ["Todas"] + unidades_opcoes, key="despesa_unidade_filtro")
        meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
        mes_filtro = st.selectbox("Filtrar por mês", meses_lista, key="despesa_mes_filtro")

        despesas_filtradas = despesas.copy()
        if unidade_filtro != "Todas":
            despesas_filtradas = despesas_filtradas[despesas_filtradas["nome"] == unidade_filtro]
        if mes_filtro != "Todos":
            despesas_filtradas = despesas_filtradas[pd.to_datetime(despesas_filtradas["data"]).dt.month == int(mes_filtro)]

        edited_df = st.data_editor(
            despesas_filtradas[["id", "nome", "data", "tipo", "valor", "descricao"]],
            num_rows="dynamic",
            use_container_width=True,
            key="editor_despesas"
        )

        if st.button("Salvar Alterações nas Despesas"):
            conn = conectar()
            for _, row in edited_df.iterrows():
                conn.execute(
                    "UPDATE despesas SET data=?, tipo=?, valor=?, descricao=? WHERE id=?",
                    (row["data"], row["tipo"], float(row["valor"]), row["descricao"], int(row["id"]))
                )
            conn.commit()
            conn.close()
            st.success("Alterações salvas! Recarregue a página para ver os dados atualizados.")

        st.subheader("Excluir Despesa")
        if not despesas_filtradas.empty:
            id_excluir = st.selectbox("Selecione o ID da despesa para excluir", despesas_filtradas["id"], key="excluir_despesa")
            if st.button("Excluir Despesa"):
                conn = conectar()
                conn.execute("DELETE FROM despesas WHERE id=?", (int(id_excluir),))
                conn.commit()
                conn.close()
                st.success(f"Despesa {id_excluir} excluída!")

        st.subheader("Copiar Despesa")
        if not despesas_filtradas.empty:
            id_copiar = st.selectbox("Selecione o ID da despesa para copiar", despesas_filtradas["id"], key="copiar_despesa")
            if st.button("Copiar Despesa"):
                despesa_copiar = despesas_filtradas.loc[despesas_filtradas["id"] == id_copiar].iloc[0]
                conn = conectar()
                conn.execute(
                    "INSERT INTO despesas (unidade_id, data, tipo, valor, descricao) VALUES (?, ?, ?, ?, ?)",
                    (int(despesa_copiar["unidade_id"]), despesa_copiar["data"], despesa_copiar["tipo"], float(despesa_copiar["valor"]), despesa_copiar["descricao"])
                )
                conn.commit()
                conn.close()
                st.success(f"Despesa {id_copiar} copiada!")
    else:
        st.info("Cadastre unidades e despesas para visualizar e editar aqui.")

# =========================
#       PRECIFICAÇÃO
# =========================
elif aba == "Precificação":
    st.header("Cadastro de Preços Base por Unidade e Temporada")
    unidades = get_unidades()

    with st.form("cad_preco"):
        unidade = st.selectbox("Unidade", unidades["nome"] if not unidades.empty else [])
        temporada = st.selectbox("Temporada", ["Baixa", "Média", "Alta"])
        preco_base = st.number_input("Preço Base", min_value=0.0, format="%.2f")
        enviar = st.form_submit_button("Cadastrar Preço")
        if enviar and unidade:
            unidade_id = int(unidades.loc[unidades["nome"] == unidade, "id"].values[0])
            conn = conectar()
            conn.execute(
                "INSERT INTO precos (unidade_id, temporada, preco_base) VALUES (?, ?, ?)",
                (unidade_id, temporada, preco_base)
            )
            conn.commit()
            conn.close()
            st.success("Preço cadastrado!")

    st.subheader("Preços Base Cadastrados")
    precos = get_precos()
    if not precos.empty and not unidades.empty:
        precos = precos.merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))
        st.dataframe(precos[["nome", "temporada", "preco_base"]], use_container_width=True)
    else:
        st.info("Cadastre unidades e preços para visualizar aqui.")

    st.subheader("Simulação de Valor de Locação")
    unidade_sim = st.selectbox("Unidade para Simulação", unidades["nome"] if not unidades.empty else [], key="simul")
    temporada_sim = st.selectbox("Temporada para Simulação", ["Baixa", "Média", "Alta"], key="simul2")
    ocupacao = st.slider("Taxa de Ocupação (%)", 0, 100, 70)
    if unidade_sim and not precos.empty:
        preco = precos[(precos["nome"] == unidade_sim) & (precos["temporada"] == temporada_sim)]["preco_base"]
        if not preco.empty:
            valor_sim = float(preco.values[0]) * (ocupacao / 100)
            st.info(f"Valor simulado para {unidade_sim} ({temporada_sim}): R$ {valor_sim:,.2f}")
        else:
            st.warning("Não há preço base cadastrado para essa combinação.")

# =========================
#  RELATÓRIO DE DESPESAS
# =========================
elif aba == "Relatório de Despesas":
    st.header("Relatório de Receita e Despesa por Unidade e Mês (Detalhado por Tipo de Despesa)")

    unidades = get_unidades()
    despesas = get_despesas()
    locacoes = get_locacoes()

    if unidades.empty:
        st.info("Cadastre unidades para gerar o relatório.")
    else:
        # Merge básicos
        if not locacoes.empty:
            locacoes = locacoes.merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))
        if not despesas.empty:
            despesas = despesas.merge(unidades, left_on="unidade_id", right_on="id", suffixes=("", "_unidade"))

        # Filtros
        unidades_opcoes = unidades["nome"].tolist()
        unidades_sel = st.multiselect("Unidades", unidades_opcoes, default=unidades_opcoes, key="desp_relat_unidades")
        meses_lista = ["Todos"] + [str(m).zfill(2) for m in range(1, 13)]
        mes_filtro = st.selectbox("Filtrar por mês", meses_lista, key="desp_relat_mes")
        tipos_opcoes = ["Todos"] + (sorted(despesas["tipo"].unique()) if not despesas.empty else [])
        tipo_filtro = st.selectbox("Filtrar por tipo de despesa", tipos_opcoes, key="desp_relat_tipo")

        # Preparação de dados
        if not locacoes.empty:
            locacoes["mes"] = pd.to_datetime(locacoes["checkin"]).dt.month
            locacoes["ano"] = pd.to_datetime(locacoes["checkin"]).dt.year
            if unidades_sel:
                locacoes = locacoes[locacoes["nome"].isin(unidades_sel)]
            if mes_filtro != "Todos":
                locacoes = locacoes[locacoes["mes"] == int(mes_filtro)]
        else:
            locacoes = pd.DataFrame(columns=["nome", "ano", "mes", "valor"])

        if not despesas.empty:
            despesas["mes"] = pd.to_datetime(despesas["data"]).dt.month
            despesas["ano"] = pd.to_datetime(despesas["data"]).dt.year
            if unidades_sel:
                despesas = despesas[despesas["nome"].isin(unidades_sel)]
            if mes_filtro != "Todos":
                despesas = despesas[despesas["mes"] == int(mes_filtro)]
        else:
            despesas = pd.DataFrame(columns=["nome", "ano", "mes", "tipo", "valor"])

        # Agrupamentos
        receita = pd.DataFrame(columns=["nome", "ano", "mes", "Receita Bruta"])
        if not locacoes.empty:
            receita = locacoes.groupby(["nome", "ano", "mes"])["valor"].sum().reset_index()
            receita = receita.rename(columns={"valor": "Receita Bruta"})

        despesa = pd.DataFrame(columns=["nome", "ano", "mes", "tipo", "Despesa"])
        if not despesas.empty:
            despesa = despesas.groupby(["nome", "ano", "mes", "tipo"])["valor"].sum().reset_index()
            despesa = despesa.rename(columns={"valor": "Despesa"})

        # Chaves (todas combinações existentes)
        chaves = pd.concat([
            receita[["nome", "ano", "mes"]],
            despesa[["nome", "ano", "mes"]].drop_duplicates()
        ], ignore_index=True).drop_duplicates()

        if chaves.empty:
            st.info("Não há dados para o período/filtros selecionados.")
        else:
            relatorio = chaves.copy()

            # Junta receita
            relatorio = relatorio.merge(receita, on=["nome", "ano", "mes"], how="left")
            relatorio["Receita Bruta"] = relatorio["Receita Bruta"].fillna(0.0)

            # Junta despesas por tipo
            tipos_despesa = despesa["tipo"].unique().tolist() if not despesa.empty else []
            for tipo in tipos_despesa:
                filtro = despesa[despesa["tipo"] == tipo]
                coluna = filtro.groupby(["nome", "ano", "mes"])["Despesa"].sum().reset_index()
                coluna = coluna.rename(columns={"Despesa": tipo})
                relatorio = relatorio.merge(coluna, on=["nome", "ano", "mes"], how="left")

            relatorio.fillna(0.0, inplace=True)

            # Totais e lucro
            relatorio["Total Despesas"] = relatorio[tipos_despesa].sum(axis=1) if tipos_despesa else 0.0
            relatorio["Lucro Líquido"] = relatorio["Receita Bruta"] - relatorio["Total Despesas"]

            # Seleciona colunas a exibir
            if tipo_filtro != "Todos" and tipo_filtro in relatorio.columns:
                colunas = ["nome", "ano", "mes", "Receita Bruta", tipo_filtro, "Total Despesas", "Lucro Líquido"]
            else:
                colunas = ["nome", "ano", "mes", "Receita Bruta"] + tipos_despesa + ["Total Despesas", "Lucro Líquido"]

            # Formatação de moeda para exibição
            relatorio_fmt = relatorio.copy()
            for col in colunas[3:]:
                relatorio_fmt[col] = relatorio_fmt[col].map(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            # Totais gerais (numérico a partir do relatorio original)
            total_receita = relatorio["Receita Bruta"].sum()
            total_despesas = relatorio["Total Despesas"].sum() if "Total Despesas" in relatorio.columns else 0.0
            total_lucro = relatorio["Lucro Líquido"].sum() if "Lucro Líquido" in relatorio.columns else 0.0

            totais_tipos = {}
            for tipo in tipos_despesa:
                totais_tipos[tipo] = relatorio[tipo].sum()

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

            relatorio_total = pd.concat([relatorio_fmt[colunas], pd.DataFrame([linha_total])], ignore_index=True)
            st.dataframe(relatorio_total, use_container_width=True)

            # ---- GRÁFICOS (somente nesta aba) ----
            st.subheader("Gráficos Comparativos de Receita, Despesa e Lucro")

            relatorio_numerico = relatorio.copy()  # dados numéricos

            # Garante colunas numéricas
            for col in ["Receita Bruta", "Total Despesas", "Lucro Líquido"]:
                if col in relatorio_numerico.columns:
                    relatorio_numerico[col] = pd.to_numeric(relatorio_numerico[col], errors="coerce").fillna(0.0)

            # Recalcula total e lucro líquido por segurança
            if tipos_despesa:
                relatorio_numerico["Total Despesas"] = relatorio_numerico[tipos_despesa].sum(axis=1)
            else:
                relatorio_numerico["Total Despesas"] = 0.0
            relatorio_numerico["Lucro Líquido"] = relatorio_numerico["Receita Bruta"] - relatorio_numerico["Total Despesas"]

            # Opções de agrupamento
            agrupamento = st.selectbox("Agrupar gráficos por", ["Unidade", "Mês", "Unidade e Mês"], key="grafico_agrupamento")

            # Criação da chave de agrupamento
            if agrupamento == "Unidade":
                relatorio_numerico["Chave"] = relatorio_numerico["nome"]
            elif agrupamento == "Mês":
                relatorio_numerico["Chave"] = relatorio_numerico["mes"].astype(str).str.zfill(2) + "/" + relatorio_numerico["ano"].astype(str)
            else:  # "Unidade e Mês"
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
            if tipos_despesa:
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
            else:
                st.info("Não há despesas por tipo para compor o gráfico de pizza.")

elif aba == "Parâmetros do Sistema":
    st.info("Em breve: configurações gerais do sistema.")
elif aba == "Exportar/Importar Dados":
    st.info("Em breve: funcionalidade de exportar e importar dados.")

elif aba == "Sobre o Sistema":
    st.markdown("""
    ## 🛠 Sobre o Sistema  
    Desenvolvido por **Alex Oliveira**.  
    Versão: **1.0**  
    Aplicação para gestão completa de hospedagens.
    """)
