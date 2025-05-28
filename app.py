import pandas as pd
import cx_Oracle
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Importação de Compras", layout="wide")

# Logo
st.image("https://raw.githubusercontent.com/seu-usuario/seu-repo/main/logo.png", width=200)

st.title("📦 Visão Geral das Compras")

# Conexão com Oracle
dsn_tns = cx_Oracle.makedsn('oracle_host', '1521', service_name='your_service')
conn = cx_Oracle.connect(user='your_user', password='your_password', dsn=dsn_tns)

# Consulta atualizada
query = """
SELECT DISTINCT
       NF.NUMNOTA AS "NUMERO NF",
       TO_CHAR(NF.DTNEG, 'DD/MM/YYYY') AS "DATA DE NEGOCIACAO",
       TO_CHAR(NF.DTFATUR, 'DD/MM/YYYY') AS "DATA DE FATURAMENTO",
       TO_CHAR(NF.DTENTSAI, 'YYYY-MM') AS "ANO-MES",
       TO_CHAR(NF.DTENTSAI, 'YYYY') AS "ANO",
       TO_CHAR(NF.DTENTSAI, 'MM') AS "MES",
       TO_CHAR(NF.DTENTSAI, 'DD/MM/YYYY') AS "DATA DE ENTRADA",
       NF.CODPARC AS "COD. PARCEIRO",
       NF.CODPROJ AS "COD. PROJETO",
       PROJETO.ABREVIATURA AS "ABREV. PROJETO",
       PROJETO.IDENTIFICACAO AS "PROJETO",
       PARCEIRO.CGC_CPF AS "CNPJ",
       PARCEIRO.NOMEPARC AS "PARCEIRO",
       NF.CODTIPOPER AS "COD. TOP",
       TOP.DESCROPER AS "TOP",
       NF.TIPMOV AS "MOVIMENTO",
       PARCEIRO.CLIENTE AS "CLIENTE",
       PARCEIRO.FORNECEDOR AS "FORNECEDOR",
       NF_LINHA.CODPROD AS "CODIGO",
       PRODUTO.DESCRPROD AS "DESCRICAO",
       PRODUTO.NCM AS "NCM",
       GRUPO.DESCRGRUPOPROD AS "GRUPO",
       NF_LINHA.CODCFO AS "CFOP",
       CASE 
           WHEN NF_LINHA.CODCFO IN (1101, 1102, 2101, 2102) THEN 'COMPRA'
           WHEN NF_LINHA.CODCFO IN (1124, 2124, 2923, 1923) THEN 'INDUSTRIALIZACAO'
           WHEN NF_LINHA.CODCFO = 0 THEN 'SERVICO'
           ELSE 'OUTROS'
       END AS "OPERACAO",
       NF_LINHA.QTDNEG AS "QTD NEGOCIADA",
       NF_LINHA.QTDENTREGUE AS "QTD ENTREGUE",
       NF_LINHA.PENDENTE AS "STATUS",
       (NF_LINHA.QTDNEG - NF_LINHA.QTDENTREGUE) AS "SALDO",
       NF_LINHA.VLRUNIT AS "VALOR UNITARIO",
       NF_LINHA.VLRTOT AS "VALOR TOTAL",
       NF_LINHA.VLRICMS AS "VALOR ICMS",
       NF_LINHA.VLRIPI AS "VALOR IPI",
       COALESCE(USU.NOMEUSU, 'Sem aprovador') AS "APROVADOR",
       TO_CHAR(LIB.DHLIB, 'DD/MM/YYYY HH24:MI') AS "DATA APROVACAO",
       (NVL(NF_LINHA.VLRTOT, 0) + NVL(NF_LINHA.VLRIPI, 0)) AS "TOTAL GERAL",
       (NVL(NF_LINHA.VLRTOT, 0) - NVL(NF_LINHA.VLRICMS, 0) - NVL(NF_LINHA.VLRIPI, 0)) AS "CUSTO NET"
FROM TGFCAB  NF
     JOIN TGFITE  NF_LINHA  ON NF.NUNOTA = NF_LINHA.NUNOTA
     JOIN TGFTOP  TOP       ON TOP.CODTIPOPER = NF.CODTIPOPER
     JOIN TGFPAR  PARCEIRO  ON NF.CODPARC = PARCEIRO.CODPARC
     JOIN TGFPRO  PRODUTO   ON NF_LINHA.CODPROD = PRODUTO.CODPROD
     JOIN TGFGRU  GRUPO     ON PRODUTO.CODGRUPOPROD = GRUPO.CODGRUPOPROD
     JOIN TCSPRJ  PROJETO   ON PROJETO.CODPROJ = NF.CODPROJ
     LEFT JOIN VSILIB LIB   ON LIB.NUNOTA = NF.NUNOTA
     LEFT JOIN TSIUSU USU   ON USU.CODUSU = LIB.CODUSULIB
WHERE NF.TIPMOV = 'C'
  AND TOP.ATUALFIN = '-1'
  AND NF.NUMNOTA > 0
ORDER BY NF.NUMNOTA ASC
"""

# Lê a consulta no dataframe
df = pd.read_sql(query, conn)

# Fecha a conexão
conn.close()

# Converte datas para dd/mm/yyyy
colunas_data = [
    "DATA DE NEGOCIACAO", "DATA DE FATURAMENTO", "DATA DE ENTRADA", "DATA APROVACAO"
]
for col in colunas_data:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%Y')

# Filtros laterais
with st.sidebar:
    st.header("Filtros")
    parceiro = st.selectbox("Filtrar por parceiro", options=["Todos"] + sorted(df["PARCEIRO"].dropna().unique().tolist()))
    operacao = st.multiselect("Operação", options=sorted(df["OPERACAO"].dropna().unique().tolist()))
    periodo = st.date_input("Período (Data de Entrada)", [])

# Aplica os filtros
if parceiro != "Todos":
    df = df[df["PARCEIRO"] == parceiro]
if operacao:
    df = df[df["OPERACAO"].isin(operacao)]
if len(periodo) == 2:
    df = df[
        (pd.to_datetime(df["DATA DE ENTRADA"], dayfirst=True) >= pd.to_datetime(periodo[0])) &
        (pd.to_datetime(df["DATA DE ENTRADA"], dayfirst=True) <= pd.to_datetime(periodo[1]))
    ]

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de registros", len(df))
col2.metric("Valor Total (Nota)", f"R$ {df['VALOR TOTAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Total Geral (Nota + IPI)", f"R$ {df['TOTAL GERAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Custo NET (Total - ICMS - IPI)", f"R$ {df['CUSTO NET'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
