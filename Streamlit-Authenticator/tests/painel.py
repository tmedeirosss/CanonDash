import yaml
from yaml.loader import SafeLoader
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
import pyodbc
import pandas as pd
import streamlit_authenticator as stauth

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

# Configuração da conexão ao banco de dados
server = '192.168.41.22'  # Nome ou IP do servidor
database = 'Db_RPA'  # Nome do banco de dados
username = 'ndd_viewer'  # Nome de usuário
password = 'ioas!@#ibusad$%$!@asd3'  # Senha
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Conectando ao banco de dados
connection = pyodbc.connect(connection_string)

# Consulta SQL
query = 'SELECT EnterpriseName, EnterpriseID FROM [Db_RPA].[dbo].[vw_NDD]'

# Carregar dados no DataFrame do pandas
df = pd.read_sql(query, connection)

# Fechar a conexão
connection.close()

# Inicializar o estado para a seleção se não estiver definido
if 'selected_option' not in st.session_state:
    st.session_state.selected_option = None

if 'enterprise_id' not in st.session_state:
    st.session_state.enterprise_id = None

# Opções para o selectbox
options = list(df['EnterpriseName'].unique())

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

if st.button("Clique para gerar o código do cliente"):
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
        codigo_criptografado = encrypt_number(codigo_cliente)
        st.write(f"Código do cliente: {codigo_criptografado}")

        # Adiciona um botão para baixar o código criptografado
        st.download_button(
            label="Gerar arquivo",
            data=codigo_criptografado,
            file_name='codigo_cliente.txt',
            mime='text/plain'
        )
else:
    st.write("Nenhum código de cliente gerado ainda.")
    
# Input para testar a descriptografia
#testar_codigo = st.text_input('Digite o código criptografado para testar a descriptografia: ')

# Descriptografia do código
#if testar_codigo:
#    codigo_decriptografado = decrypt_code(testar_codigo)
#    st.write(f"Código descriptografado: {codigo_decriptografado}")
