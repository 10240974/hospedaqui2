import pyodbc

# Dados de conexãop
server = 'terbrdwhdb03'
database = 'dwh_brasil'
driver = '{ODBC Driver 17 for SQL Server}'

# String de conexão usando autenticação do Windows
conn_str = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
)

# Conectando ao banco
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Consulta à tabela
cursor.execute("SELECT TOP 10 * FROM vfbr.rep_despacho")
rows = cursor.fetchall()

# Exibindo os resultados
for row in rows:
    print(row)

# Fechando a conexão
cursor.close()
conn.close()
