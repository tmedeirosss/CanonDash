import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError, ForgotError, LoginError, RegisterError, ResetError, UpdateError)
import pyodbc
import pandas as pd
from cryptography.fernet import Fernet
import plotly.express as px
import base64
import smtplib
from email.mime.text import MIMEText

if 'sidebar' not in st.session_state:
    st.session_state.sidebar = 'collapsed'

st.set_page_config(
    layout="wide",
    page_title="Canon Dashboard",
    page_icon="Canon-Logo.png",  # Você pode usar um ícone emoji ou uma URL de ícone
    menu_items={  # Esvazia os itens do menu para ocultar a barra de deploy
        'About': None
    },
    initial_sidebar_state= st.session_state.sidebar
)

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()
    
logo_base64 = get_base64_image("Canon-Logo.png")


with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html= True)



st.markdown(f'''
    <div class="header">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo">
    </div>
''', unsafe_allow_html=True)



# Carregar arquivo de configuração
with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)


if 'role' not in st.session_state:
    st.session_state.role = "user"

# Garantir que todos os usuários tenham o campo 'role'
for username, user_info in config['credentials']['usernames'].items():
    if 'role' not in user_info:
        user_info['role'] = 'user'
        st.session_state.role = user_info['role']

if 'config' not in st.session_state:
    st.session_state.config = None

if 'authenticator' not in st.session_state:
    st.session_state.authenticator = None
# Criar o objeto autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('pre-authorized', {}),
    config['credentials']['usernames']
)

st.session_state.config = config
st.session_state.authenticator = authenticator

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
        #st.success("Conexão com o banco de dados estabelecida com sucesso.")
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
    return role

def encrypt_number(number: str) -> str:
    key = open('secret.key', 'rb').read()
    cipher_suite = Fernet(key)
    encrypted_number = cipher_suite.encrypt(number.encode())
    return encrypted_number.decode()


def decrypt_code(encrypted_code: str) -> str:
    key = open('secret.key', 'rb').read()
    cipher_suite = Fernet(key)
    try:
        decrypted_number = cipher_suite.decrypt(encrypted_code.encode())
        return decrypted_number.decode()
    except InvalidToken:
        return "Código inválido ou chave incorreta"
    
def send_reset_email(email, nova_senha):
    sender = "Canon_Dashboard@cusa.canon.com"
    

    msg = MIMEText(f"Essa é sua nova senha: {nova_senha}")
    msg["Subject"] = "Redefinição de senha"
    msg["From"] = sender
    msg["To"] = email

    with smtplib.SMTP("Melville-app-mail.cusa.canon.com", 25) as server:
        server.sendmail(sender, email, msg.as_string())

# Manter os dados carregados no estado de sessão
if 'data' not in st.session_state:
    query = """SELECT
    'vw_IW_Main' AS tabela,
    [Ship To Name] AS EnterpriseName,
    [Item Code] AS ModelName,
    [Serial#] AS SerialNumber,
    pb_peq,
    pb_grande,
    cor_peq,
    cor_grande,
    cor_total,
    total,
    data
FROM 
    [Db_RPA].[dbo].[vw_IW_Main]

UNION ALL

SELECT
    'vw_NDD' AS tabela,
    EnterpriseName,
    ModelName,
    SerialNumber,
    pb_peq,
    pb_grande,
    cor_peq,
    cor_grande,
    cor_total,
    total,
    data
FROM 
    [Db_RPA].[dbo].[vw_NDD]"""
    st.session_state.data = fetch_data(query)

admin_code = str(8236274157823465)
data = st.session_state.data

colpos1, colpos2, colpos3 = st.columns(3) #define colunas de posição


try:
    with colpos2:
        authenticator.login(fields={
            'Form name': 'Login',
            'Username': 'Nome de Usuário',
            'Password': 'Senha',
            'Login': 'Entrar'
        })
        
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout(button_name= 'Sair')
    if st.session_state["name"] is None:
        st.write('Aguarde...')
        st.session_state.sidebar = 'collapsed'
        st.experimental_rerun()
        st.stop()
    else:
        st.session_state.sidebar = 'expanded'
        pg = st.navigation([st.Page("Início.py"), st.Page("Dashboard.py"), st.Page("Faturas.py"), st.Page("Chamados.py")])
        pg.run()

    client_id = st.session_state["username"]

    # Verificar se o código do cliente está presente
    client_info = config['credentials']['usernames'][client_id]
    if 'client_code' not in client_info or not client_info['client_code']:
        st.info("Clique no botão 'Browse files' para adicionar a chave de acesso.")
        arquivo_carregado = st.file_uploader('Carregue o arquivo de Chave', label_visibility="collapsed", help='Arraste sua chave de cliente para esse espaço, o clique em "Browse files" para localiza-la')
        if not arquivo_carregado:
            st.warning('A chave de acesso garante a segurança de suas informações e será solicitada somente no primeiro acesso.')
            st.stop()
        st.success("Chave adicionada com sucesso!")
                   
        client_code_input = arquivo_carregado.read().decode("utf-8")
        client_code_input_decript = decrypt_code(client_code_input)
        if st.button("Salvar"):
            client_code = client_code_input_decript
            if client_code in data['EnterpriseName'].values or client_code == admin_code:
                config['credentials']['usernames'][client_id]['client_code'] = client_code

                # Salvar as informações atualizadas no arquivo YAML
                with open('config.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False)

                st.success("Código do cliente atualizado com sucesso.")
                st.experimental_rerun()
            else:
                st.error("Código do cliente não encontrado na base de dados.")
                st.write(client_code, type(client_code), admin_code, type(admin_code))
    else:
        # Código do cliente já está presente, verifique se está na base de dados
        tipo_usuario(client_id)
        role = tipo_usuario(client_id)
        st.session_state.role = role
        

        # Rodapé com HTML e CSS
        footer = """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 3px;
            font-size: 14px;
            color: #555;
            height: 30px;  /* Ajusta a altura do rodapé */
        }
        </style>
        <div class="footer">
            <p>© 2024 Canon do Brasil. Todos os direitos reservados.</p>
        </div>
        """

        st.markdown(footer, unsafe_allow_html=True)

            #st.dataframe(df_selection)
            


elif st.session_state["authentication_status"] is False:
    with colpos2:
        st.error('Usuário/Senha incorreta')
elif st.session_state["authentication_status"] is None:
    with colpos2:
        st.warning('Por favor, insira seu nome de usuário e senha')

if st.session_state["authentication_status"] is None or st.session_state["authentication_status"] is False:
    try:
        with colpos2:
            with st.expander('Criar uma conta'):
                (email_of_registered_user, username_of_registered_user, name_of_registered_user) = authenticator.register_user(fields={
                    
                'Form name': 'Cadastrar',
                'Name': 'Nome Completo',
                'Email':'Email',
                'Username': 'Nome de Usuário',
                'Password': 'Senha',
                'Repeat password': 'Repita a Senha',
                'Register': 'Registrar',
            
                },pre_authorization=False)
                if email_of_registered_user:
                    st.success('Usuário registrado com sucesso!')
    except RegisterError as e:
        with colpos2:
            st.error(e)

    try:
        with colpos2:
            with st.expander('Esqueceu a senha?'):
                (username_of_forgotten_password, email_of_forgotten_password, new_random_password) = authenticator.forgot_password(fields={
                    'Form name': 'Esqueci a senha',
                    'Username': 'Usuário',
                    'Submit': 'Recuperar',
                })
                if username_of_forgotten_password:
                    send_reset_email(email_of_forgotten_password, new_random_password)
                    
                    # Salvar as informações atualizadas no arquivo YAML
                    with open('config.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    st.success('Nova senha enviada')
                elif not username_of_forgotten_password:
                    st.error('Nome de usuário não localizado')
    except ForgotError as e:
        with colpos2:
            st.error(e)

    try:
        with colpos2:
            with st.expander('Esqueceu o usuário?'):
                (username_of_forgotten_username, email_of_forgotten_username) = authenticator.forgot_username(fields={
                    'Form name': 'Esqueci o Usuário',
                    'Email': 'Email',
                    'Submit': 'Recuperar',
                })
                if username_of_forgotten_username:
                    st.success('Nome de usuário enviado')
                elif not username_of_forgotten_username:
                    st.error('Email não localizado')
    except ForgotError as e:
        with colpos2:
            st.error(e)

    if st.session_state["authentication_status"]:
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                st.success('Entries updated successfully')
        except UpdateError as e:
            st.error(e)

# Salvar as informações atualizadas no arquivo YAML
with open('config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)