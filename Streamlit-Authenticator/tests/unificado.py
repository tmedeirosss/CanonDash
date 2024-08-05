import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError, ForgotError, LoginError, RegisterError, ResetError, UpdateError)
import pyodbc
import pandas as pd
from cryptography.fernet import Fernet
from PIL import Image
import plotly.express as px


# Configurar o layout como 'wide'
st.set_page_config(layout="wide")

# Carregar a imagem
image_path = "Canon-Logo.png"
image = Image.open(image_path)

# Redimensionar a imagem
new_size = (225, 150)  # (width, height)
resized_image = image.resize(new_size)

# Exibir a imagem redimensionada
st.image(resized_image)

# Título estilizado usando HTML e CSS


# Carregar arquivo de configuração
with open('../config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)



# Garantir que todos os usuários tenham o campo 'role'
for username, user_info in config['credentials']['usernames'].items():
    if 'role' not in user_info:
        user_info['role'] = 'user'

# Criar o objeto autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config.get('pre-authorized', {}),
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
    
# Manter os dados carregados no estado de sessão
if 'data' not in st.session_state:
    query = "SELECT EnterpriseID, EnterpriseName, ModelName, SerialNumber, pb_peq, pb_grande, cor_peq, cor_grande, cor_total, total, data FROM [Db_RPA].[dbo].[vw_NDD]"
    st.session_state.data = fetch_data(query)

admin_code = 8236274157823465
data = st.session_state.data


try:
    authenticator.login(fields={
        'Form name': 'Entrar no Sistema',
        'Username': 'Nome de Usuário',
        'Password': 'Senha',
        'Login': 'Entrar'
    })
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout(button_name= 'Sair')
    st.write(f'Bem vindo *{st.session_state["name"]}*')
    st.write('Esse é o seu Dashboard')
    client_id = st.session_state["username"]

    # Verificar se o código do cliente está presente
    client_info = config['credentials']['usernames'][client_id]
    if 'client_code' not in client_info or not client_info['client_code']:
        st.warning("Por favor, insira o código do cliente para continuar.")
        client_code_input = st.text_input("Insira o código do cliente:")
        client_code_input_decript = decrypt_code(client_code_input)
        if st.button("Salvar Código do Cliente"):
            client_code = int(client_code_input_decript)
            if client_code in data['EnterpriseID'].values or client_code == admin_code:
                config['credentials']['usernames'][client_id]['client_code'] = client_code

                # Salvar as informações atualizadas no arquivo YAML
                with open('../config.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False)

                st.success("Código do cliente atualizado com sucesso.")
                st.experimental_rerun()
            else:
                st.error("Código do cliente não encontrado na base de dados.")
    else:
        # Código do cliente já está presente, verifique se está na base de dados
        tipo_usuario(client_id)
        role = tipo_usuario(client_id)
        if role == 'admin': #Bloco de dashboard do administrador

            st.write("Dados carregados com sucesso.")
            
            
            st.sidebar.title("Opções")

            # Campo de entrada para o código do cliente na barra lateral
            st.sidebar.header("Atualizar Código do Cliente")
            client_code_input = st.sidebar.text_input(
                "Insira o código do cliente (se necessário):",
                value=config['credentials']['usernames'][client_id].get('client_code', ""),
                type='password',
                help="Caso seja necessário atualizar seu código de cliente, um novo será fornecido pela Canon"
            )

            if st.sidebar.button("Salvar Código do Cliente"):
                client_code_input = decrypt_code(client_code_input)
                # Atualizar a configuração do cliente
                config['credentials']['usernames'][client_id]['client_code'] = int(client_code_input)

                # Salvar as informações atualizadas no arquivo YAML
                with open('../config.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False)
                
                st.sidebar.success("Código do cliente atualizado com sucesso.")

            # Utilize st.session_state para armazenar e manter os valores dos filtros
            if 'selected_enterprise' not in st.session_state:
                st.session_state.selected_enterprise = "Todos"
            if 'selected_model' not in st.session_state:
                st.session_state.selected_model = "Todos"
            if 'selected_serial' not in st.session_state:
                st.session_state.selected_serial = "Todos"
            if 'selected_date_range' not in st.session_state:
                st.session_state.selected_date_range = None

            # Primeiro filtro: Cliente
            enterprise_options = ["Todos"] + list(data['EnterpriseName'].unique())
            st.session_state.selected_enterprise = st.sidebar.selectbox(
                "Selecione o nome da empresa",
                options=enterprise_options,
                index=enterprise_options.index(st.session_state.selected_enterprise)
            )
            
            # Filtrar os modelos com base no cliente selecionado
            if st.session_state.selected_enterprise == "Todos":
                filtered_data = data
            else:
                filtered_data = data[data['EnterpriseName'] == st.session_state.selected_enterprise]
            
            # Segundo filtro: Modelo
            model_options = ["Todos"] + list(filtered_data['ModelName'].unique())
            st.session_state.selected_model = st.sidebar.selectbox(
                "Selecione um modelo de equipamento",
                options=model_options,
                index=model_options.index(st.session_state.selected_model)
            )
            
            # Filtrar os números de série com base no modelo selecionado
            if st.session_state.selected_model == "Todos":
                filtered_data = filtered_data
            else:
                filtered_data = filtered_data[filtered_data['ModelName'] == st.session_state.selected_model]
            
            # Terceiro filtro: Número de Série
            serial_options = ["Todos"] + list(filtered_data['SerialNumber'].unique())
            st.session_state.selected_serial = st.sidebar.selectbox(
                "Selecione um número de série",
                options=serial_options,
                index=serial_options.index(st.session_state.selected_serial)
            )

            # Filtrar com base no número de série selecionado
            if st.session_state.selected_serial == "Todos":
                filtered_data = filtered_data
            else:
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


        else:  #Bloco de dashboard do cliente
            st.write('Você possui acesso somente as suas informações')

            st.sidebar.title("Opções")

            # Campo de entrada para o código do cliente na barra lateral
            st.sidebar.header("Atualizar Código do Cliente")
            client_code_input_encrypted = st.sidebar.text_input(
                "Insira o código do cliente (se necessário):",
                value=config['credentials']['usernames'][client_id].get('client_code', ""),
                type='password',
                help="Caso seja necessário atualizar seu código de cliente, um novo será fornecido pela Canon"
            )
            
            
            if st.sidebar.button("Salvar Código do Cliente"):
                # Atualizar a configuração do cliente
                client_code_input_decript = decrypt_code(client_code_input_encrypted)
                
                st.write(client_code_input_decript)
                config['credentials']['usernames'][client_id]['client_code'] = int(client_code_input_decript)

                # Salvar as informações atualizadas no arquivo YAML
                with open('../config.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(config, file, default_flow_style=False)
                
                st.sidebar.success("Código do cliente atualizado com sucesso.")

            # Utilize st.session_state para armazenar e manter os valores dos filtros
            if 'selected_enterprise' not in st.session_state:
                st.session_state.selected_enterprise = "Todos"
            if 'selected_model' not in st.session_state:
                st.session_state.selected_model = "Todos"
            if 'selected_serial' not in st.session_state:
                st.session_state.selected_serial = "Todos"
            if 'selected_date_range' not in st.session_state:
                st.session_state.selected_date_range = None

            # Primeiro filtro: Cliente
            enterprise_names = data[data['EnterpriseID'] == config['credentials']['usernames'][client_id]['client_code']]['EnterpriseName']
            enterprise_options = list(enterprise_names.unique())  # Convertendo para lista depois de aplicar .unique()

            st.session_state.selected_enterprise = st.sidebar.selectbox(
            "Selecione o nome da empresa",
            options=enterprise_options,
            index=enterprise_options.index(st.session_state.selected_enterprise) if st.session_state.selected_enterprise in enterprise_options else 0
            )
            
            # Filtrar os modelos com base no cliente selecionado
            if st.session_state.selected_enterprise == "Todos":
                filtered_data = data
            else:
                filtered_data = data[data['EnterpriseName'] == st.session_state.selected_enterprise]
            
            # Segundo filtro: Modelo
            model_options = ["Todos"] + list(filtered_data['ModelName'].unique())
            st.session_state.selected_model = st.sidebar.selectbox(
                "Selecione um modelo de equipamento",
                options=model_options,
                index=model_options.index(st.session_state.selected_model)
            )
            
            # Filtrar os números de série com base no modelo selecionado
            if st.session_state.selected_model == "Todos":
                filtered_data = filtered_data
            else:
                filtered_data = filtered_data[filtered_data['ModelName'] == st.session_state.selected_model]
            
            # Terceiro filtro: Número de Série
            serial_options = ["Todos"] + list(filtered_data['SerialNumber'].unique())
            st.session_state.selected_serial = st.sidebar.selectbox(
                "Selecione um número de série",
                options=serial_options,
                index=serial_options.index(st.session_state.selected_serial)
            )

            # Filtrar com base no número de série selecionado
            if st.session_state.selected_serial == "Todos":
                filtered_data = filtered_data
            else:
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


            #Início do blobo de gráficos
            A4Pb = df_selection['pb_peq'].sum()
            A4Cor = df_selection['cor_peq'].sum()
            A3Pb = df_selection['pb_grande'].sum()
            A3Cor = df_selection['cor_grande'].sum()
            total = df_selection['total'].sum()
            equipamentos = df_selection['SerialNumber']
            cores = ['#1f77b4', '#ff7f0e']
            st.title("Total por formato/cor")
            col1, col2 = st.columns(2)

            
            st.title("Total por equipamento")
            bar1 = px.bar(df_selection, y='total', x='SerialNumber', title='Total por Equipamento', color='SerialNumber')
            st.plotly_chart(bar1)
            
            
            with col1:
                pz1 = px.pie(names=('P&B', 'COR'), values=[A4Pb, A4Cor], title='Impressões A4', color_discrete_sequence=cores)
                st.plotly_chart(pz1)

            with col2:
                pz2 = px.pie(names=('P&B', 'COR'), values=[A3Pb, A3Cor], title='Impressões A3', color_discrete_sequence=cores)
                st.plotly_chart(pz2)

                 # Gráfico de Linha do Tempo
            st.title("Produção Total ao Longo do Tempo")
            timeline_data = filtered_data.groupby('data')['total'].sum().reset_index()
            line_chart = px.line(
                timeline_data,
                x='data',
                y='total',
                title='Produção Total ao Longo do Tempo'
            )
            st.plotly_chart(line_chart)
            
            resumo = df_selection.groupby(df_selection['SerialNumber']).agg({
            'pb_peq': 'sum',
            'pb_grande': 'sum',
            'cor_peq': 'sum',
            'cor_grande': 'sum',
            'total': 'sum'
             }).reset_index()

            
            # Renomeia as colunas do dataframe
            resumo = resumo.rename(columns={
                'SerialNumber': 'Equipamento',
                'pb_peq': 'P&B A4',
                'pb_grande': 'P&B A3',
                'cor_peq': 'COR A4',
                'cor_grande': 'COR A3',
                'total': 'TOTAL'
            })

            st.title("Resumo da Produção por Equipamento")
            st.dataframe(resumo, hide_index=True)

            resumo_total ={ 'P&B A4':df_selection['pb_peq'].sum(), 
                           'P&B A3':df_selection['pb_grande'].sum(), 
                           'COR A4':df_selection['cor_peq'].sum(), 
                           'COR A3':df_selection['cor_grande'].sum(), 
                           'TOTAL':df_selection['total'].sum()}
            
            st.title("Resumo da Produção Total") 
            st.dataframe(resumo_total)

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
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira seu nome de usuário e senha')

if st.session_state["authentication_status"] is None or st.session_state["authentication_status"] is False:
    try:
        (email_of_registered_user, username_of_registered_user, name_of_registered_user) = authenticator.register_user(fields={
            
        'Form name': 'Novo Usuário',
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
        st.error(e)

    try:
        (username_of_forgotten_password, email_of_forgotten_password, new_random_password) = authenticator.forgot_password(fields={
            'Form name': 'Esqueci a senha',
            'Username': 'Usuário',
            'Submit': 'Recuperar',
        })
        if username_of_forgotten_password:
            st.success('Nova senha enviada')
        elif not username_of_forgotten_password:
            st.error('Nome de usuário não localizado')
    except ForgotError as e:
        st.error(e)

    try:
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
        st.error(e)

    if st.session_state["authentication_status"]:
        try:
            if authenticator.update_user_details(st.session_state["username"]):
                st.success('Entries updated successfully')
        except UpdateError as e:
            st.error(e)

# Salvar as informações atualizadas no arquivo YAML
with open('../config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)
