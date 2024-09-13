import pyodbc
import sqlite3

# Configurações de conexão com o SQL Server
sql_server_connection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.41.22;DATABASE=Db_RPA;UID=ndd_viewer;PWD=ioas!@#ibusad$%$!@asd3')
sql_server_cursor = sql_server_connection.cursor()

# Conexão com o banco de dados SQLite (será criado um novo arquivo SQLite)
sqlite_connection = sqlite3.connect('Db_RPA.sqlite')
sqlite_cursor = sqlite_connection.cursor()

# Obtendo todas as tabelas do SQL Server
sql_server_cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
tables = sql_server_cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"Convertendo tabela {table_name}...")

    # Criando a tabela no SQLite
    sql_server_cursor.execute(f"SELECT * FROM {table_name} WHERE 1=0")
    columns = [column[0] for column in sql_server_cursor.description]
    create_table_sql = f"CREATE TABLE {table_name} ({', '.join([f'{col} TEXT' for col in columns])})"
    sqlite_cursor.execute(create_table_sql)

    # Inserindo dados na tabela do SQLite
    sql_server_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sql_server_cursor.fetchall()
    for row in rows:
        placeholders = ', '.join('?' * len(row))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        sqlite_cursor.execute(insert_sql, row)

# Fechando conexões e salvando o banco de dados SQLite
sqlite_connection.commit()
sqlite_connection.close()
sql_server_connection.close()

print("Conversão concluída com sucesso!")
