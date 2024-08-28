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
    page_title="Contatos",
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

st.title('Home do portal')