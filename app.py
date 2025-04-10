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

# Exibe o dataframe
print(df.head())
