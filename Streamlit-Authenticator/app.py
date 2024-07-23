import streamlit as st
import pyodbc
import pandas as pd


# Configuração da conexão com o banco de dados
def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=printersNDD;"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(connection_string)

def fetch_data(query):
    try:
        connection = get_connection()
        data = pd.read_sql(query, connection)
        connection.close()
        return data
    except pyodbc.Error as e:
        st.error(f"Erro ao conectar ou executar a consulta: {e}")
        return None

# Criação da interface Streamlit
st.title("Consultar Linha Específica")

# Entrada de dados do usuário
valor_id = st.text_input("Digite o nome do cliente:")

if st.button("Executar Consulta"):
    if valor_id:
        # Criação da consulta SQL com base no valor fornecido
        query = f"SELECT * FROM dbo.Sheet1$ WHERE EnterpriseName = {valor_id}"
        #data = fetch_data(query)
        if data is not None:
            st.write(data)
    else:
        st.error("Por favor, digite um ID válido.")

        
