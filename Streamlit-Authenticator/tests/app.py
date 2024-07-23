import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities.exceptions import UpdateError
import streamlit_authenticator as stauth
import streamlit as st
import pyodbc
import pandas as pd
import plotly.express as px

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


def consulta(valor_id):
    if valor_id:
        # Criação da consulta SQL com base no valor fornecido
        query = f"SELECT * FROM dbo.Sheet1$ WHERE EnterpriseID = {valor_id}"
        data = fetch_data(query)
        if data is not None:
            #st.write(data)  ativar caso queira ver todos dados da base para esse cliente

            
            A4Pb = 0
            A4Cor = 0
            A3Pb = 0
            A3cor =0
            
            informacoes = {
            'Categorias': ['A4Pb', 'A4Cor', 'A3Pb', 'A3cor'],
            'Valores': [A4Pb, A4Cor, A3Pb, A3cor]
            }


            # Criar o gráfico de pizza usando Plotly
            fig = px.bar(informacoes, y= data.start_101, x= data.SerialNumber, title='Total por Equipamento')
            
            data['start_101'] = data['start_101'].fillna("Não localizado")
            data_unique = data.drop_duplicates(subset=['SerialNumber'])

            # Criar o gráfico de barras usando Plotly
            fig = px.bar(data_unique, y='start_101', x='SerialNumber', title='Produção Total por Equipamento')
            st.plotly_chart(fig)

            data['data'] = pd.to_datetime(data['data'])
            data['start_101'] = pd.to_numeric(data['start_101'], errors='coerce')
            data['end_101'] = pd.to_numeric(data['end_101'], errors='coerce')
            
            # Agregar os dados por data para calcular a produção diária
            data_grouped = data.groupby('data').agg({'start_101': 'sum', 'end_101': 'sum'}).reset_index()
            
            # Calcular a produção como a diferença entre end_101 e start_101 (exemplo simplificado)
            data_grouped['production'] = data_grouped['end_101'] - data_grouped['start_101']

            # Criar o gráfico de linha do tempo para mostrar picos e vales de produção
            ig = px.line(data_grouped, x='data', y='production', title='Produção ao Longo do Tempo')

            # Mostrar o gráfico no Streamlit
            st.plotly_chart(ig)
            
            # Usar layout de colunas do Streamlit
            col1, col2 = st.columns(2)

            with col1:
                # Adicionar uma seleção para escolher um SerialNumber
                selected_serial = st.selectbox('Selecione um equipamento para detalhes', data_unique['SerialNumber'])
                
                #st.write(data_unique[['SerialNumber', 'start_101']]) Exibir tabela de totais

                

            # Exibir o gráfico na segunda coluna
            #with col2:
                

                

        # Filtrar os dados para o SerialNumber selecionado
        equipamento_data = data[data['SerialNumber'] == selected_serial]
        equipamento_data = data[data['SerialNumber'] == selected_serial]
        st.write(equipamento_data)



        # # Creating an update user details widget
        if st.session_state["authentication_status"]:
            try:
                if authenticator.update_user_details(st.session_state["username"]):
                    st.success('Entries updated successfully')
            except UpdateError as e:
                st.error(e)

      
    else:
        st.error("Por favor, digite um ID válido.")

            
