import pandas as pd
import pyodbc
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Importação de Compras", layout="wide")

# Logo
st.image("https://raw.githubusercontent.com/seu-usuario/seu-repo/main/logo.png", width=200)

st.title("📦 Visão Geral das Compras")

# Conexão com o banco
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=benu.database.windows.net,1433;'
    'DATABASE=benu;'
    'UID=eduardo.ferraz;'
    'PWD=8h!0+a~jL8]B6~^5s5+v'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Consulta atualizada
query = """
SELECT 
    numero_nf,
    data_negociacao,
    data_faturamento,
    ano_mes,
    ano,
    mes,
    data_entrada,
    cod_parceiro,
    cod_projeto,
    abrev_projeto,
    projeto,
    cnpj,
    parceiro,
    cod_top,
    desc_top,
    movimento,
    cliente,
    fornecedor,
    codigo,
    descricao,
    ncm,
    grupo,
    cfop,
    operacao,
    qtd_negociada,
    qtd_entregue,
    status,
    saldo,
    valor_unitario,
    valor_total,
    valor_icms,
    valor_ipi,
    aprovador,
    data_aprovacao,
    total_geral,
    custo_net
FROM nacional_compras
"""

# Lê a consulta no dataframe
df = pd.read_sql(query, conn)

# Fecha a conexão
cursor.close()
conn.close()

# Converte datas para dd/mm/yyyy
colunas_data = [
    "data_negociacao", "data_faturamento", "data_entrada", "data_aprovacao"
]
for col in colunas_data:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')

# Filtros laterais
with st.sidebar:
    st.header("Filtros")
    parceiro = st.selectbox("Filtrar por parceiro", options=["Todos"] + sorted(df["parceiro"].dropna().unique().tolist()))
    operacao = st.multiselect("Operação", options=sorted(df["operacao"].dropna().unique().tolist()))
    periodo = st.date_input("Período (Data de Entrada)", [])

# Aplica os filtros
if parceiro != "Todos":
    df = df[df["parceiro"] == parceiro]
if operacao:
    df = df[df["operacao"].isin(operacao)]
if len(periodo) == 2:
    df = df[
        (pd.to_datetime(df["data_entrada"], dayfirst=True) >= pd.to_datetime(periodo[0])) &
        (pd.to_datetime(df["data_entrada"], dayfirst=True) <= pd.to_datetime(periodo[1]))
    ]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de registros", len(df))
col2.metric("Valor Total (Nota)", f"R$ {df['valor_total'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Total Geral (Nota + IPI)", f"R$ {df['total_geral'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Custo NET (Total - ICMS - IPI)", f"R$ {df['custo_net'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Exibe tabela completa
st.dataframe(df, use_container_width=True)

# Download em Excel
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name='Compras')
output.seek(0)

st.download_button(
    "📥 Baixar Excel", 
    output.getvalue(), 
    file_name="compras_filtradas.xlsx", 
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
