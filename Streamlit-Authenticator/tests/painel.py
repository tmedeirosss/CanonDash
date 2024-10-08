import yaml
from yaml.loader import SafeLoader
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
import pyodbc
import pandas as pd
import streamlit_authenticator as stauth
import os
from PIL import Image
import time
import base64

st.set_page_config(
    layout="wide",
    page_title="Canon Dashboard",
    page_icon="Canon-Logo.png",  # Você pode usar um ícone emoji ou uma URL de ícone
    menu_items={  # Esvazia os itens do menu para ocultar a barra de deploy
        'About': None
    }
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




st.markdown("""
    <style>
        .custom-title {
            font-size: 30px; /* Altere o tamanho da fonte conforme necessário */
            color: #333; /* Altere a cor do texto, se desejado */
        }
    </style>
    <h1 class="custom-title">Painel de Administrador</h1>
""", unsafe_allow_html=True)

# Funções de criptografia e descriptografia
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

with st.spinner("Carregando..."):
    
    # Configuração da conexão ao banco de dados
    server = '192.168.41.22'  # Nome ou IP do servidor
    database = 'Db_RPA'  # Nome do banco de dados
    username = 'ndd_viewer'  # Nome de usuário
    password = 'ioas!@#ibusad$%$!@asd3'  # Senha
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

    banco_de_origem = st.selectbox('Selecione o Banco de Dados de Origem', options=["NDD", "IwRemote"])
    if banco_de_origem == "NDD":
        consulta= "SELECT EnterpriseID, EnterpriseName, ModelName, SerialNumber, pb_peq, pb_grande, cor_peq, cor_grande, cor_total, total, data FROM [Db_RPA].[dbo].[vw_NDD]"
    elif banco_de_origem == "IwRemote":
        consulta= """
        SELECT 
        CHECKSUM([Ship To Name]) AS EnterpriseID,
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
    """

    # Conectando ao banco de dados
    # Conectando ao banco de dados
    connection = pyodbc.connect(connection_string)

    # Consulta SQL
    query = consulta

    # Carregar dados no DataFrame do pandas
    df = pd.read_sql(query, connection)

    # Fechar a conexão
    connection.close()

    time.sleep(1)

# Inicializar o estado para a seleção se não estiver definido
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = None

if 'enterprise_id' not in st.session_state:
    st.session_state.enterprise_id = None

# Opções para o selectbox
options = list(df['EnterpriseName'].drop_duplicates())

# Criação do selectbox com chave 'dropdown_selection'
empresa_selecionada = st.selectbox(
    'Escolha uma opção:',
    options=options,
    key='dropdown_selection',  # Armazena o valor selecionado no session_state
    index=options.index(st.session_state.selected_option) if st.session_state.selected_option in options else 0,
    on_change=lambda: st.session_state.update(selected_option=st.session_state.dropdown_selection)  # Chama a função quando a seleção muda
)

# Exibir a seleção atual
st.write(f'Seleção atual: {empresa_selecionada}')

if st.button("Gerar chave de acesso"):
    # Filtra o DataFrame para obter o EnterpriseID
    enterprise_id = df[df['EnterpriseName'] == empresa_selecionada]['EnterpriseID']
    
    # Verifica se o EnterpriseID existe
    if not enterprise_id.empty:
        st.session_state.enterprise_id = enterprise_id.iloc[0]
    else:
        st.write("Empresa não encontrada. Por favor, tente novamente.")

# Verificar se o EnterpriseID está definido e não é None
if st.session_state.enterprise_id is not None:
    # Converte o EnterpriseID para um inteiro
    enterprise_id_int = int(st.session_state.enterprise_id)
    codigo_cliente = str(enterprise_id_int)

    # Criptografia do código do cliente
    if codigo_cliente:
        if banco_de_origem == "NDD":
            codigo_criptografado = encrypt_number(empresa_selecionada)
        elif banco_de_origem == "IwRemote":
            codigo_criptografado = encrypt_number(empresa_selecionada)
        st.write("Chave gerada com sucesso", decrypt_code(codigo_criptografado))

        # Adiciona um botão para baixar o código criptografado
        st.download_button(
            label="Baixar Chave",
            data=codigo_criptografado,
            file_name=f'Chave de Acesso{empresa_selecionada}',
            mime='text/plain'
        )
else:
    st.write("Nenhum código de cliente gerado ainda.")

# Funções para manipular o arquivo YAML
def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.load(file, Loader=yaml.SafeLoader)
    return config

def save_config(file_path, config):
    with open(file_path, 'w') as file:
        yaml.dump(config, file)

def update_user_role(file_path, username, new_role):
    config = load_config(file_path)
    if username in config['credentials']['usernames']:
        config['credentials']['usernames'][username]['role'] = new_role
        save_config(file_path, config)
        st.write(f"Permissão do usuário {username} atualizado para {new_role}.")
    else:
        st.write(f"Usuário {username} não encontrado.")

# Caminho para o arquivo de configuração
file_path = '../config.yaml'

# Carregar a configuração
config = load_config(file_path)

# Obter os nomes dos usuários existentes
usernames = list(config['credentials']['usernames'].keys())

# Selectbox para selecionar o usuário
username = st.selectbox('Selecione um usuário para atualizar a permissão:', usernames)

# Selectbox para selecionar a nova permissão
new_role = st.selectbox('Escolha a nova permissão para o usuário:', ['admin', 'user'])

# Container para os botões
buttons_container = st.container()

with buttons_container:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Atualizar permissão do usuário"):
            if username and new_role:
                update_user_role(file_path, username, new_role)
            else:
                st.write("Por favor, preencha todos os campos.")
    
    with col2:
        if st.button("Gerar chave de administrador"):
            numero_para_criptografar = "8236274157823465"
            numero_criptografado = encrypt_number(numero_para_criptografar)
            st.write(f"Código de administrador gerado com sucesso!")
            st.download_button(
                label="Baixar Chave",
                data=numero_criptografado,
                file_name='Chave de Administrador',
                mime='text/plain'
        )

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