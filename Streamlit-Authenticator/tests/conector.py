import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities.exceptions import UpdateError
import streamlit_authenticator as stauth
import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px
from io import BytesIO


# Loading config file
with open('../config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# Configuração da conexão com o banco de dados
def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=192.168.41.22;"
        "DATABASE=Db_RPA;"
        "UID=ndd_viewer;"
        "PWD=ioas!@#ibusad$%$!@asd3;"
    )
    return pyodbc.connect(connection_string)

def fetch_data(query):
    try:
        connection = get_connection()
        data = pd.read_sql(query, connection)
        #connection.close()
        return data
    except pyodbc.Error as e:
        st.error(f"Erro ao conectar ou executar a consulta: {e}")
        return None

# Criação da interface Streamlit
st.title("Consultar Linha Específica")

# Entrada de dados do usuário


def consulta(valor_id):
    if valor_id:
        # Criação da consulta SQL com base no valor fornecido
        query = f"SELECT * FROM [Db_RPA].[dbo].[vw_NDD] WHERE EnterpriseID = {valor_id}"
        data = fetch_data(query)
        if data is not None:
            st.write(data) # ativar caso queira ver todos dados da base para esse cliente

            
            A4Pb = 0
            A4Cor = 0
            A3Pb = 0
            A3cor =0
            
            informacoes = {
            'Categorias': ['A4Pb', 'A4Cor', 'A3Pb', 'A3cor'],
            'Valores': [A4Pb, A4Cor, A3Pb, A3cor]
            }