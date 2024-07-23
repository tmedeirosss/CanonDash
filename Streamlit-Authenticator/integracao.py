import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError,
                                                          ForgotError,
                                                          LoginError,
                                                          RegisterError,
                                                          ResetError,
                                                          UpdateError) 

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

# Creating a login widget
try:
    authenticator.login()
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    

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
            data = fetch_data(query)
            if data is not None:
                st.write(data)
        else:
            st.error("Por favor, digite um ID válido.")

        
 











elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# Creating a password reset widget
if st.session_state["authentication_status"]:
    try:
        if authenticator.reset_password(st.session_state["username"]):
            st.success('Password modified successfully')
    except ResetError as e:
        st.error(e)
    except CredentialsError as e:
        st.error(e)

# # Creating a new user registration widget
try:
    (email_of_registered_user,
        username_of_registered_user,
        name_of_registered_user) = authenticator.register_user(pre_authorization=False)
    if email_of_registered_user:
        st.success('User registered successfully')
except RegisterError as e:
    st.error(e)

# # Creating a forgot password widget
try:
    (username_of_forgotten_password,
        email_of_forgotten_password,
        new_random_password) = authenticator.forgot_password()
    if username_of_forgotten_password:
        st.success('New password sent securely')
        # Random password to be transferred to the user securely
    elif not username_of_forgotten_password:
        st.error('Username not found')
except ForgotError as e:
    st.error(e)

# # Creating a forgot username widget
try:
    (username_of_forgotten_username,
        email_of_forgotten_username) = authenticator.forgot_username()
    if username_of_forgotten_username:
        st.success('Username sent securely')
        # Username to be transferred to the user securely
    elif not username_of_forgotten_username:
        st.error('Email not found')
except ForgotError as e:
    st.error(e)

# # Creating an update user details widget
if st.session_state["authentication_status"]:
    try:
        if authenticator.update_user_details(st.session_state["username"]):
            st.success('Entries updated successfully')
    except UpdateError as e:
        st.error(e)

# Saving config file
with open('../config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)


