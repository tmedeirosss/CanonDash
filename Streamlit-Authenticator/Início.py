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
from streamlit_option_menu import option_menu

st.set_page_config(
    layout="wide",
    page_title="Canon Dashboard",
    page_icon="pages/Canon-Logo.png",  # Você pode usar um ícone emoji ou uma URL de ícone
    menu_items={  # Esvazia os itens do menu para ocultar a barra de deploy
        'About': None
    }
)

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()
    
logo_base64 = get_base64_image("pages/Canon-Logo.png")


with open('pages/styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html= True)



st.markdown(f'''
    <div class="header">
        <img src="data:image/png;base64,{logo_base64}" alt="Logo">
    </div>
''', unsafe_allow_html=True)



# Carregar arquivo de configuração
with open('pages/config.yaml', 'r', encoding='utf-8') as file:
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


def login():
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
login()
if st.session_state["authentication_status"]:
    authenticator.logout(button_name= 'Sair')
    if st.session_state["name"] is None:
        st.write('Aguarde...')
        st.stop()
    else:
        st.write(f'Bem vindo *{st.session_state["name"]}*')
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
                with open('pages/config.yaml', 'w', encoding='utf-8') as file:
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
        if role == 'admin': #Bloco de dashboard do administrador

            st.write("Dados carregados com sucesso.")
            

            # Campo de entrada para o código do cliente na barra lateral
            with st.sidebar.expander('Atualizar chave de acesso'):
                arquivo_carregado = st.file_uploader('Carregue o arquivo de Chave', label_visibility="collapsed", help='Arraste sua chave de cliente para esse espaço, o clique em "Browse files" para localiza-la')
                st.info('Carregue sua chave de acesso')
                if arquivo_carregado:
                    client_code_input = arquivo_carregado.read().decode("utf-8")
                    if st.button("Salvar"):
                        client_code_input = decrypt_code(client_code_input)
                        # Atualizar a configuração do cliente
                        config['credentials']['usernames'][client_id]['client_code'] = client_code_input

                        # Salvar as informações atualizadas no arquivo YAML
                        with open('pages/config.yaml', 'w', encoding='utf-8') as file:
                            yaml.dump(config, file, default_flow_style=False)
                        
                        st.sidebar.success("Código do cliente atualizado com sucesso.")
            with st.sidebar.expander('Alterar Senha'):
                if st.session_state['authentication_status']:
                    try:
                        if authenticator.reset_password(st.session_state['username'], fields= {'Form name':'Atualizar Senha', 
                                                                                               'Current password':'Senha Atual', 
                                                                                               'New password':'Nova Senha', 
                                                                                               'Repeat password': 'Repita a Senha', 
                                                                                               'Reset':'OK'}):
                            # Salvar as informações atualizadas no arquivo YAML
                            with open('pages/config.yaml', 'w', encoding='utf-8') as file:
                                yaml.dump(config, file, default_flow_style=False)
                            st.success('Senha alterada com sucesso!')
                    except Exception as e:
                        st.error(e)

            st.sidebar.title("Filtros")
            # Utilize st.session_state para armazenar e manter os valores dos filtros
            
            if 'selected_enterprise' not in st.session_state:
                st.session_state.selected_enterprise = "Todos"
            if 'selected_model' not in st.session_state:
                st.session_state.selected_model = "Todos"
            if 'selected_serial' not in st.session_state:
                st.session_state.selected_serial = "Todos"
            if 'selected_date_range' not in st.session_state:
                st.session_state.selected_date_range = None

            # Definir as opções de tabelas
            tabela_options = ["NDD", "IW"]
            st.session_state.selected_tabelas = st.sidebar.multiselect(
                "Selecione o banco de dados",
                options=tabela_options,
                default=st.session_state.get('selected_tabelas', tabela_options)
            )

            # Filtrar os dados com base nas tabelas selecionadas
            if "NDD" in st.session_state.selected_tabelas and "IW" in st.session_state.selected_tabelas:
                filtered_data = data  # Não filtra nada, exibe tudo
            elif "NDD" in st.session_state.selected_tabelas:
                filtered_data = data[data['tabela'] == 'vw_NDD']  # Filtra apenas os dados de NDD
            elif "IW" in st.session_state.selected_tabelas:
                filtered_data = data[data['tabela'] == 'vw_IW_Main']  # Filtra apenas os dados de IW
            else:
                st.warning("Selecione um ou mais bancos de dados para a consulta")
                st.stop()
                
            
            modo_grafico = st.sidebar.selectbox(label="Selecione Gráficos Desejados", options=["Gráfico Gerencial", "Gráfico Cliente"], index = 0)
            st.write(modo_grafico)
            if modo_grafico == "Gráfico Cliente":
                index_cliente = 1
            else:
                index_cliente = 0

            

            # Primeiro filtro: Cliente
            enterprise_options = ["Todos"] + list(data['EnterpriseName'].unique())
            st.session_state.selected_enterprise = st.sidebar.selectbox(
                "Selecione o nome da empresa",
                options=enterprise_options,
                index= index_cliente
            )
            
            # Filtrar os modelos com base no cliente selecionado
            if st.session_state.selected_enterprise == "Todos":
                filtered_data = filtered_data
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
            # Verificar se a tupla tem dois elementos antes de desempacotá-la
            if len(st.session_state.selected_date_range) != 2:
                st.warning("Por favor, selecione um intervalo de datas completo.")
                st.stop()
            else:
               pass 

            start_date, end_date = st.session_state.selected_date_range
            df_selection = filtered_data[(filtered_data['data'] >= start_date) & (filtered_data['data'] <= end_date)]
            formatted_start_date = start_date.strftime('%d/%m/%Y')
            formatted_end_date = end_date.strftime('%d/%m/%Y')

            # Exibir o intervalo de datas formatado
            st.sidebar.write("Período selecionado:", formatted_start_date, "-", formatted_end_date)
            #st.dataframe(df_selection) exibe todas colunas do dataframe filtrado

            #Início do bloco de gráficos do administrador

            gerente_container = st.container()
            cliente_container = st.container()

            if modo_grafico == "Gráfico Gerencial":
                with gerente_container:

                    df_selection['Número de Série - Cliente'] = df_selection['SerialNumber'] + " - " + df_selection['EnterpriseName']

                    #Top 10 clientes que mais imprimiram
                    df_grouped_EnterpriseName = df_selection.groupby('EnterpriseName', as_index=False).sum(numeric_only=True)
                    st.title("Clientes que mais imprimiram")
                    top_10 = df_grouped_EnterpriseName.nlargest(10, 'total')
                    bar0 = px.bar(top_10, y='total', x='EnterpriseName', title='Top 10 clientes que mais imprimiram', color='EnterpriseName')
                    st.plotly_chart(bar0)

                    #Top 10 clientes que menos imprimiram
                    df_grouped_EnterpriseName = df_selection.groupby('EnterpriseName', as_index=False).sum(numeric_only=True)
                    st.title("Clientes que menos imprimiram")
                    df_filtered_enterprise = df_grouped_EnterpriseName[df_grouped_EnterpriseName['total'] > 0]
                    top_10 = df_filtered_enterprise.nsmallest(10, 'total')
                    bar1 = px.bar(top_10, y='total', x='EnterpriseName', title='Top 10 clientes que menos imprimiram', color='EnterpriseName')
                    st.plotly_chart(bar1)
                    
                    #Top 10 equipamentos que mais imprimiram
                    df_grouped_total = df_selection.groupby('Número de Série - Cliente', as_index=False).sum(numeric_only=True)
                    st.title("Equipamentos que mais imprimiram")
                    top_10 = df_grouped_total.nlargest(10, 'total')
                    bar2 = px.bar(top_10, y='total', x='Número de Série - Cliente', title='Top 10 equipamentos que mais imprimiram', color='Número de Série - Cliente')
                    st.plotly_chart(bar2)

                    #Top 10 equipamentos que menos imprimiram
                    df_grouped_total = df_selection.groupby('Número de Série - Cliente', as_index=False).sum(numeric_only=True)
                    df_filtered_serial = df_grouped_total[df_grouped_total['total'] > 0]
                    st.title("Equipamentos que menos imprimiram")
                    top_10 = df_filtered_serial.nsmallest(10, 'total')
                    bar3 = px.bar(top_10, y='total', x='Número de Série - Cliente', title='Top 10 equipamentos que menos imprimiram', color='Número de Série - Cliente',  labels={
                        "SerialNumber": "Número de Série - Cliente",
                        "total": "Total Impresso"
                    })
                    st.plotly_chart(bar3)
            elif modo_grafico == "Gráfico Cliente":
                with cliente_container:
                    #Início do bloco de gráficos
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
                    df_grouped_total = df_selection.groupby('SerialNumber', as_index=False).sum(numeric_only=True)
                    bar1 = px.bar(df_grouped_total, y='total', x='SerialNumber', title='Total por Equipamento', color='SerialNumber')
                    st.plotly_chart(bar1)
                    
                    
                    with col1:
                        pz1 = px.pie(names=('P&B', 'COR'), values=[A4Pb, A4Cor], title='Impressões A4', color_discrete_sequence=cores)
                        st.plotly_chart(pz1)

                    if A3Pb != 0 or A3Cor != 0:
                        with col2:
                            pz2 = px.pie(names=('P&B', 'COR'), values=[A3Pb, A3Cor], title='Impressões A3', color_discrete_sequence=cores)
                            st.plotly_chart(pz2)

                    # Criar novas colunas para a produção colorida e PB
                    filtered_data['Producao_Cor'] = filtered_data['cor_peq'] + filtered_data['cor_grande']
                    filtered_data['Producao_PB'] = filtered_data['pb_peq'] + filtered_data['pb_grande']

                    # Agrupar por data e somar as produções
                    timeline_data_cor = filtered_data.groupby('data')['Producao_Cor'].sum().reset_index()
                    timeline_data_pb = filtered_data.groupby('data')['Producao_PB'].sum().reset_index()
                    timeline_data_total = filtered_data.groupby('data')['total'].sum().reset_index()

                    # Fazer o merge dos DataFrames resultantes
                    timeline_data = pd.merge(timeline_data_cor, timeline_data_pb, on='data', suffixes=('_Cor', '_PB'))
                    timeline_data = pd.merge(timeline_data, timeline_data_total, on='data')

                    if timeline_data['Producao_Cor'].sum() == 0:
                        timeline_data.drop(columns=['Producao_Cor'], inplace=True)

                    if timeline_data['Producao_PB'].sum() == 0:
                        timeline_data.drop(columns=['Producao_PB'], inplace=True)

                    if timeline_data['total'].sum() == 0:
                        timeline_data.drop(columns=['total'], inplace=True)

                    # Gráfico de linha com 3 linhas, uma para 'Producao_Cor', outra para 'Producao_PB' e outra para 'Producao total' 
                    st.title("Produção por cor ao Longo do Tempo")
                    fig = px.line(timeline_data, x='data', y=timeline_data.columns[1:], 
                                labels={'value': 'Produção', 'data': 'Data'}, 
                                title='Produção ao Longo do Tempo')

                    # Exibindo o gráfico
                    st.plotly_chart(fig)

                    resumo = df_selection.groupby(df_selection['SerialNumber']).agg({
                    'ModelName': 'first',
                    'pb_peq': 'sum',
                    'pb_grande': 'sum',
                    'cor_peq': 'sum',
                    'cor_grande': 'sum',
                    'total': 'sum'
                    
                    }).reset_index()

                    # Renomeia as colunas do dataframe
                    resumo = resumo.rename(columns={
                        'ModelName': 'Modelo',
                        'SerialNumber': 'Série',
                        'pb_peq': 'P&B A4',
                        'pb_grande': 'P&B A3',
                        'cor_peq': 'COR A4',
                        'cor_grande': 'COR A3',
                        'total': 'TOTAL'
                    })
                
                    
                    coluna_ignorada = 'Modelo', 'Série'

                    cols_to_format = ['P&B A4', 'P&B A3', 'COR A4', 'COR A3', 'TOTAL']
                    resumo[cols_to_format] = resumo[cols_to_format].applymap(lambda x: f"{x:,}".replace(",", "."))

                    st.title("Resumo da Produção por Equipamento")
                    nova_ordem = ['Modelo','Série','P&B A4','COR A4','P&B A3','COR A3','TOTAL']
                    resumo = resumo[nova_ordem]
                    resumo = resumo.reset_index(drop=True)
                    resumo.update(resumo.loc[:, resumo.columns != coluna_ignorada].apply(pd.to_numeric, errors='coerce'))
                    resumo = resumo.loc[:, (resumo != 0).any(axis=0)]
                    st.dataframe(resumo, hide_index= True)


                    resumo_total ={ 'P&B A4':df_selection['pb_peq'].sum(), 
                                'P&B A3':df_selection['pb_grande'].sum(), 
                                'COR A4':df_selection['cor_peq'].sum(), 
                                'COR A3':df_selection['cor_grande'].sum(), 
                                'TOTAL':df_selection['total'].sum()}
                    
                    df_resumo_total = pd.DataFrame(resumo_total, index=[0])

                    # Substituindo vírgulas por pontos na formatação dos números
                    df_resumo_total = df_resumo_total.applymap(lambda x: f"{x:,}".replace(",", "."))
                    
                    st.title("Resumo da Produção Total") 
                    nova_ordem = ['P&B A4','COR A4','P&B A3','COR A3','TOTAL']
                    df_resumo_total=df_resumo_total[nova_ordem]
                    df_resumo_total = df_resumo_total.reset_index(drop=True)
                    df_resumo_total.update(df_resumo_total.loc[:, df_resumo_total.columns != coluna_ignorada].apply(pd.to_numeric, errors='coerce'))
                    df_resumo_total = df_resumo_total.loc[:, (df_resumo_total != 0).any(axis=0)]
                    st.dataframe(df_resumo_total, hide_index= True)

        
        elif role == 'user' and str(config['credentials']['usernames'][client_id]['client_code']) == str(admin_code): 
            st.warning('Contate o seu representante Canon')
            st.stop()
        else:  #Bloco de dashboard do cliente
            st.write('Você possui acesso somente as suas informações')
            
            # Campo de entrada para o código do cliente na barra lateral
            with st.sidebar.expander('Atualizar chave de acesso'):
                arquivo_carregado = st.file_uploader('Carregue o arquivo de Chave', label_visibility="collapsed", help='Arraste sua chave de cliente para esse espaço, o clique em "Browse files" para localiza-la')
                st.info('Carregue sua chave de acesso')
                if arquivo_carregado:
                    client_code_input = arquivo_carregado.read().decode("utf-8")
                    if st.button("Salvar"):
                        client_code_input = decrypt_code(client_code_input)
                        # Atualizar a configuração do cliente
                        config['credentials']['usernames'][client_id]['client_code'] = client_code_input

                        # Salvar as informações atualizadas no arquivo YAML
                        with open('pages/config.yaml', 'w', encoding='utf-8') as file:
                            yaml.dump(config, file, default_flow_style=False)
                        
                        st.sidebar.success("Código do cliente atualizado com sucesso.")
            with st.sidebar.expander('Alterar Senha'):
                if st.session_state['authentication_status']:
                    try:
                        if authenticator.reset_password(st.session_state['username'], fields= {'Form name':'Atualizar Senha', 
                                                                                               'Current password':'Senha Atual', 
                                                                                               'New password':'Nova Senha', 
                                                                                               'Repeat password': 'Repita a Senha', 
                                                                                               'Reset':'OK'}):
                            # Salvar as informações atualizadas no arquivo YAML
                            with open('pages/config.yaml', 'w', encoding='utf-8') as file:
                                yaml.dump(config, file, default_flow_style=False)
                            st.success('Senha alterada com sucesso!')
                    except Exception as e:
                        st.error(e)
            
            st.sidebar.title("Filtros")
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
            enterprise_names = data[data['EnterpriseName'] == config['credentials']['usernames'][client_id]['client_code']]['EnterpriseName']
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
            if len(st.session_state.selected_date_range) != 2:
                st.warning("Por favor, selecione um intervalo de datas completo.")
                st.stop()
            else:
               pass 
            start_date, end_date = st.session_state.selected_date_range
            df_selection = filtered_data[(filtered_data['data'] >= start_date) & (filtered_data['data'] <= end_date)]

            formatted_start_date = start_date.strftime('%d/%m/%Y')
            formatted_end_date = end_date.strftime('%d/%m/%Y')

            # Exibir o intervalo de datas formatado
            st.sidebar.write("Período selecionado:", formatted_start_date, "-", formatted_end_date)

            #Início do bloco de gráficos
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
            df_grouped_total = df_selection.groupby('SerialNumber', as_index=False).sum(numeric_only=True)
            bar1 = px.bar(df_grouped_total, y='total', x='SerialNumber', title='Total por Equipamento', color='SerialNumber')
            st.plotly_chart(bar1)
            
            
            with col1:
                pz1 = px.pie(names=('P&B', 'COR'), values=[A4Pb, A4Cor], title='Impressões A4', color_discrete_sequence=cores)
                st.plotly_chart(pz1)

            if A3Pb != 0 or A3Cor != 0:
                with col2:
                    pz2 = px.pie(names=('P&B', 'COR'), values=[A3Pb, A3Cor], title='Impressões A3', color_discrete_sequence=cores)
                    st.plotly_chart(pz2)

            # Criar novas colunas para a produção colorida e PB
            filtered_data['Producao_Cor'] = filtered_data['cor_peq'] + filtered_data['cor_grande']
            filtered_data['Producao_PB'] = filtered_data['pb_peq'] + filtered_data['pb_grande']

            # Agrupar por data e somar as produções
            timeline_data_cor = filtered_data.groupby('data')['Producao_Cor'].sum().reset_index()
            timeline_data_pb = filtered_data.groupby('data')['Producao_PB'].sum().reset_index()
            timeline_data_total = filtered_data.groupby('data')['total'].sum().reset_index()

            # Fazer o merge dos DataFrames resultantes
            timeline_data = pd.merge(timeline_data_cor, timeline_data_pb, on='data', suffixes=('_Cor', '_PB'))
            timeline_data = pd.merge(timeline_data, timeline_data_total, on='data')

            if timeline_data['Producao_Cor'].sum() == 0:
                timeline_data.drop(columns=['Producao_Cor'], inplace=True)

            if timeline_data['Producao_PB'].sum() == 0:
                timeline_data.drop(columns=['Producao_PB'], inplace=True)

            if timeline_data['total'].sum() == 0:
                timeline_data.drop(columns=['total'], inplace=True)

            # Gráfico de linha com 3 linhas, uma para 'Producao_Cor', outra para 'Producao_PB' e outra para 'Producao total' 
            st.title("Produção por cor ao Longo do Tempo")
            fig = px.line(timeline_data, x='data', y=timeline_data.columns[1:], 
                        labels={'value': 'Produção', 'data': 'Data'}, 
                        title='Produção ao Longo do Tempo')

            # Exibindo o gráfico
            st.plotly_chart(fig)
          
            resumo = df_selection.groupby(df_selection['SerialNumber']).agg({
            'ModelName': 'first',
            'pb_peq': 'sum',
            'pb_grande': 'sum',
            'cor_peq': 'sum',
            'cor_grande': 'sum',
            'total': 'sum'
            
            }).reset_index()

            # Renomeia as colunas do dataframe
            resumo = resumo.rename(columns={
                'ModelName': 'Modelo',
                'SerialNumber': 'Série',
                'pb_peq': 'P&B A4',
                'pb_grande': 'P&B A3',
                'cor_peq': 'COR A4',
                'cor_grande': 'COR A3',
                'total': 'TOTAL'
            })
        
            
            coluna_ignorada = 'Modelo', 'Série'

            cols_to_format = ['P&B A4', 'P&B A3', 'COR A4', 'COR A3', 'TOTAL']
            resumo[cols_to_format] = resumo[cols_to_format].applymap(lambda x: f"{x:,}".replace(",", "."))

            st.title("Resumo da Produção por Equipamento")
            nova_ordem = ['Modelo','Série','P&B A4','COR A4','P&B A3','COR A3','TOTAL']
            resumo = resumo[nova_ordem]
            resumo = resumo.reset_index(drop=True)
            resumo.update(resumo.loc[:, resumo.columns != coluna_ignorada].apply(pd.to_numeric, errors='coerce'))
            resumo = resumo.loc[:, (resumo != 0).any(axis=0)]
            st.dataframe(resumo, hide_index= True)


            resumo_total ={ 'P&B A4':df_selection['pb_peq'].sum(), 
                        'P&B A3':df_selection['pb_grande'].sum(), 
                        'COR A4':df_selection['cor_peq'].sum(), 
                        'COR A3':df_selection['cor_grande'].sum(), 
                        'TOTAL':df_selection['total'].sum()}
            
            df_resumo_total = pd.DataFrame(resumo_total, index=[0])

            # Substituindo vírgulas por pontos na formatação dos números
            df_resumo_total = df_resumo_total.applymap(lambda x: f"{x:,}".replace(",", "."))
            
            st.title("Resumo da Produção Total") 
            nova_ordem = ['P&B A4','COR A4','P&B A3','COR A3','TOTAL']
            df_resumo_total=df_resumo_total[nova_ordem]
            df_resumo_total = df_resumo_total.reset_index(drop=True)
            df_resumo_total.update(df_resumo_total.loc[:, df_resumo_total.columns != coluna_ignorada].apply(pd.to_numeric, errors='coerce'))
            df_resumo_total = df_resumo_total.loc[:, (df_resumo_total != 0).any(axis=0)]
            st.dataframe(df_resumo_total, hide_index= True)

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
                    with open('pages/config.yaml', 'w', encoding='utf-8') as file:
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
with open('pages/config.yaml', 'w', encoding='utf-8') as file:
    yaml.dump(config, file, default_flow_style=False)