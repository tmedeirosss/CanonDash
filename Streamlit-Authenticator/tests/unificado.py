import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError, ForgotError, LoginError, RegisterError, ResetError, UpdateError)
import pyodbc
import pandas as pd

# Configurar o layout como 'wide'
st.set_page_config(layout="wide")

# Loading config file
with open('../config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Creating the authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized'],
    config['credentials']['usernames']
)

# Configuração da conexão com o banco de dados
def get_connection():
    try:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=192.168.41.22;"
            "DATABASE=Db_RPA;"
            "UID=ndd_viewer;"
            "PWD=ioas!@#ibusad$%$!@asd3;"
        )
        connection = pyodbc.connect(connection_string)
        st.success("Conexão com o banco de dados estabelecida com sucesso.")
        return connection
    except pyodbc.Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

def fetch_data(query):
    try:
        connection = get_connection()
        if connection is not None:
            data = pd.read_sql(query, connection)
            data['data'] = pd.to_datetime(data['data']).dt.date  # Convertendo para formato de data
            connection.close()
            if data.empty:
                st.warning("Nenhum dado encontrado para o ID fornecido.")
                return None
            else:
                return data
    except pyodbc.Error as e:
        st.error(f"Erro ao executar a consulta: {e}")
        return None

def tipo_usuario(valor_id):
    user = config['credentials']['usernames']
    role = user[valor_id].get('role', 'user')
    st.write(f"Tipo de usuário: {role}")

# Manter os dados carregados no estado de sessão
if 'data' not in st.session_state:
    query = "SELECT * FROM [Db_RPA].[dbo].[vw_NDD]"
    st.session_state.data = fetch_data(query)

data = st.session_state.data

try:
    authenticator.login()
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Bem vindo *{st.session_state["name"]}*')
    st.write(f'Seu ID de cliente é:  *{st.session_state["username"]}*')
    client_id = st.session_state["username"]

    tipo_usuario(st.session_state["username"])
    
    st.write("Dados carregados com sucesso.")
    
    st.sidebar.title("Opções")
    
    # Utilize st.session_state para armazenar e manter os valores dos filtros
    if 'selected_enterprise' not in st.session_state:
        st.session_state.selected_enterprise = None
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    if 'selected_serial' not in st.session_state:
        st.session_state.selected_serial = None
    if 'selected_date_range' not in st.session_state:
        st.session_state.selected_date_range = None

    # Primeiro filtro: Cliente
    st.session_state.selected_enterprise = st.sidebar.selectbox(
        "Selecione um cliente",
        options=data['EnterpriseName'].unique(),
        index=(list(data['EnterpriseName'].unique()).index(st.session_state.selected_enterprise)
               if st.session_state.selected_enterprise in list(data['EnterpriseName'].unique()) else 0)
    )
    
    # Filtrar os modelos com base no cliente selecionado
    filtered_data = data[data['EnterpriseName'] == st.session_state.selected_enterprise]
    
    # Segundo filtro: Modelo
    st.session_state.selected_model = st.sidebar.selectbox(
        "Selecione um modelo de equipamento",
        options=filtered_data['ModelName'].unique(),
        index=(list(filtered_data['ModelName'].unique()).index(st.session_state.selected_model)
               if st.session_state.selected_model in list(filtered_data['ModelName'].unique()) else 0)
    )
    
    # Filtrar os números de série com base no modelo selecionado
    filtered_data = filtered_data[filtered_data['ModelName'] == st.session_state.selected_model]
    
    # Terceiro filtro: Número de Série
    st.session_state.selected_serial = st.sidebar.selectbox(
        "Selecione um número de série",
        options=filtered_data['SerialNumber'].unique(),
        index=(list(filtered_data['SerialNumber'].unique()).index(st.session_state.selected_serial)
               if st.session_state.selected_serial in list(filtered_data['SerialNumber'].unique()) else 0)
    )

    # Filtrar com base no número de série selecionado
    filtered_data = filtered_data[filtered_data['SerialNumber'] == st.session_state.selected_serial]

    # Quarto filtro: Período de Datas
    min_date = min(filtered_data['data'])
    max_date = max(filtered_data['data'])

    st.session_state.selected_date_range = st.sidebar.date_input(
        "Selecione um período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filtrar os dados com base no período de datas selecionado
    start_date, end_date = st.session_state.selected_date_range
    df_selection = filtered_data[(filtered_data['data'] >= start_date) & (filtered_data['data'] <= end_date)]

    st.dataframe(df_selection)

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

if st.session_state["authentication_status"] is None or st.session_state["authentication_status"] is False:
    try:
        (email_of_registered_user, username_of_registered_user, name_of_registered_user) = authenticator.register_user(pre_authorization=False)
        if email_of_registered_user:
            st.success('User registered successfully')
    except RegisterError as e:
        st.error(e)

    try:
        (username_of_forgotten_password, email_of_forgotten_password, new_random_password) = authenticator.forgot_password()
        if username_of_forgotten_password:
            st.success('New password sent securely')
        elif not username_of_forgotten_password:
            st.error('Username not found')
    except ForgotError as e:
        st.error(e)

    try:
        (username_of_forgotten_username, email_of_forgotten_username) = authenticator.forgot_username()
        if username_of_forgotten_username:
            st.success('Username sent securely')
        elif not username_of_forgotten_username:
            st.error('Email not found')
    except ForgotError as e:
        st.error(e)

    if st.session_state["authentication_status"]:
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                st.success('Entries updated successfully')
        except UpdateError as e:
            st.error(e)

# Saving config file
with open('../config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
