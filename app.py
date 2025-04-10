import pandas as pd
import pyodbc
from datetime import datetime
from tqdm import tqdm

# Caminhos
caminho_entrada = r'C:\\NACIONAL\\COMPRAS.XLSX'
caminho_erros = r'C:\\NACIONAL\\erros_importacao.xlsx'
caminho_log = r'C:\\NACIONAL\\log_importacao.txt'

# Mapeamento
mapa_colunas = {
    'Nro. Único': 'nro_unico',
    'Nro. Nota': 'nro_nota',
    'Pendente': 'pendente',
    'Dt. Neg.': 'data_negociacao',
    'Dt. de Alteração': 'data_alteracao',
    'Dt. do Faturamento': 'data_faturamento',
    'Dt. do Movimento': 'data_movimento',
    'Dt. Entrada/Saída': 'data_entrada_saida',
    'Descrição (Tipo de Operação)': 'tipo_operacao',
    'Tipo de Movimento': 'tipo_movimento',
    'Nome Parceiro (Parceiro)': 'nome_parceiro',
    'Descrição (Natureza)': 'natureza',
    'Descrição (Projeto)': 'projeto',
    'Aprovado': 'aprovado',
    'Financeiro': 'financeiro',
    'Nome (Usuário Alteração)': 'usuario_alteracao',
    'Vlr. do Frete': 'valor_frete',
    'Vlr. Nota': 'valor_nota'
}

# Leitura
df = pd.read_excel(caminho_entrada, engine='openpyxl')
df = df.rename(columns=mapa_colunas)
colunas_banco = list(mapa_colunas.values())
df = df[[col for col in colunas_banco if col in df.columns]]

# Validação de datas (com valor padrão 01/01/1900 para campos vazios)
def validar_data(dt):
    try:
        if pd.isnull(dt) or str(dt).strip() == '':
            return datetime(1900, 1, 1)
        if isinstance(dt, str):
            dt = pd.to_datetime(dt, errors='coerce')
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
        if isinstance(dt, datetime):
            if datetime(1900, 1, 1) <= dt <= datetime(2079, 6, 6):
                return dt
    except Exception:
        pass
    return datetime(1900, 1, 1)

colunas_data = [
    'data_negociacao',
    'data_alteracao',
    'data_faturamento',
    'data_movimento',
    'data_entrada_saida'
]

for col in colunas_data:
    if col in df.columns:
        df[col] = df[col].apply(validar_data)

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

# Inserção linha a linha com barra de progresso
erros = []
sucesso = 0

with open(caminho_log, 'a', encoding='utf-8') as log:
    log.write(f"\n\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Início da importação\n")

    for i, row in tqdm(df.iterrows(), total=len(df), desc='Importando dados', unit='linha'):
        try:
            row_dict = row.to_dict()
            for col in colunas_data:
                if col in row_dict and not isinstance(row_dict[col], datetime):
                    row_dict[col] = datetime(1900, 1, 1)

            colunas = ', '.join(row_dict.keys())
            placeholders = ', '.join(['?'] * len(row_dict))
            sql = f"INSERT INTO nacional_compras ({colunas}) VALUES ({placeholders})"

            cursor.execute(sql, tuple(row_dict.values()))
            sucesso += 1

            from tqdm import tqdm
            tqdm.write(f"[Linha {i+2}] Sucesso")
            log.write(f"[Linha {i+2}] Sucesso\n")

        except Exception as e:
            erro_info = row.to_dict()
            erro_info["erro"] = str(e)
            erros.append(erro_info)
            tqdm.write(f"[Linha {i+2}] ERRO: {e}")
            log.write(f"[Linha {i+2}] ERRO: {e}\n")
            continue

conn.commit()

# Verifica total de registros no banco após inserção
cursor.execute("SELECT * FROM nacional_compras")
qtd_registros = len(cursor.fetchall())
print(f"Total de registros na tabela: {qtd_registros}")

cursor.close()
conn.close()

# Exporta erros
if erros:
    pd.DataFrame(erros).to_excel(caminho_erros, index=False)

# Finaliza log
with open(caminho_log, 'a', encoding='utf-8') as log:
    log.write(f"✅ {sucesso} inserções com sucesso\n")
    log.write(f"❌ {len(erros)} erros salvos em erros_importacao.xlsx\n")
    log.write(f"📦 Total atual na tabela nacional_compras: {qtd_registros}\n")

print("✅ Importação finalizada.")
