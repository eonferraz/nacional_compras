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

# Consulta os dados com nomes de colunas padronizados
query = """
SELECT 
    nro_unico,
    nro_nota,
    pendente,
    data_negociacao,
    data_alteracao,
    data_faturamento,
    data_movimento,
    data_entrada_saida,
    tipo_operacao,
    tipo_movimento,
    nome_parceiro,
    natureza,
    projeto,
    aprovado,
    financeiro,
    usuario_alteracao,
    valor_frete,
    valor_nota
FROM nacional_compras
"""

# Lê a consulta no dataframe
df = pd.read_sql(query, conn)

# Fecha a conexão
cursor.close()
conn.close()

# Converte datas para dd/mm/yyyy
colunas_data = [
    "data_negociacao", "data_alteracao", "data_faturamento",
    "data_movimento", "data_entrada_saida"
]
for col in colunas_data:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')

# Filtros laterais
with st.sidebar:
    st.header("Filtros")
    parceiro = st.selectbox("Filtrar por parceiro", options=["Todos"] + sorted(df["nome_parceiro"].dropna().unique().tolist()))
    tipo_mov = st.multiselect("Tipo de movimento", options=sorted(df["tipo_movimento"].dropna().unique().tolist()))
    periodo = st.date_input("Período (Data do Movimento)", [])

# Aplica os filtros
if parceiro != "Todos":
    df = df[df["nome_parceiro"] == parceiro]
if tipo_mov:
    df = df[df["tipo_movimento"].isin(tipo_mov)]
if len(periodo) == 2:
    df = df[(pd.to_datetime(df["data_movimento"], dayfirst=True) >= pd.to_datetime(periodo[0])) &
            (pd.to_datetime(df["data_movimento"], dayfirst=True) <= pd.to_datetime(periodo[1]))]

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("Total de registros", len(df))
col2.metric("Total da nota", f"R$ {df['valor_nota'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Total do frete", f"R$ {df['valor_frete'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
