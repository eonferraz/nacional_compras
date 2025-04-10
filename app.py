import pandas as pd
import pyodbc
from datetime import datetime

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

# Consulta os dados de compras com campos renomeados conforme esperado
query = """
SELECT 
    [Nro. Único] AS nro_unico,
    [Nro. Nota] AS nro_nota,
    [Pendente] AS pendente,
    [Dt. Neg.] AS data_negociacao,
    [Dt. de Alteração] AS data_alteracao,
    [Dt. do Faturamento] AS data_faturamento,
    [Dt. do Movimento] AS data_movimento,
    [Dt. Entrada/Saída] AS data_entrada_saida,
    [Descrição (Tipo de Operação)] AS tipo_operacao,
    [Tipo de Movimento] AS tipo_movimento,
    [Nome Parceiro (Parceiro)] AS nome_parceiro,
    [Descrição (Natureza)] AS natureza,
    [Descrição (Projeto)] AS projeto,
    [Aprovado] AS aprovado,
    [Financeiro] AS financeiro,
    [Nome (Usuário Alteração)] AS usuario_alteracao,
    [Vlr. do Frete] AS valor_frete,
    [Vlr. Nota] AS valor_nota
FROM nacional_compras
"""

# Lê a consulta no dataframe
df = pd.read_sql(query, conn)

# Fecha a conexão
cursor.close()
conn.close()

# Exibe o dataframe
print(df.head())
