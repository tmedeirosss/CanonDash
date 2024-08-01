import yaml
from yaml.loader import SafeLoader
import streamlit as st
from cryptography.fernet import Fernet, InvalidToken
import streamlit_authenticator as stauth
import unificado

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
    
data = unificado.export_data()

st.write(data)

# Input para o código do cliente
codigo_cliente = st.text_input('Digite o código do cliente: ')

# Criptografia do código do cliente
codigo_criptografado = encrypt_number(codigo_cliente)
st.write(f"Código criptografado: {codigo_criptografado}")

# Input para testar a descriptografia
testar_codigo = st.text_input('Digite o código criptografado para testar a descriptografia: ')

# Descriptografia do código
codigo_decriptografado = decrypt_code(testar_codigo)
st.write(f"Código descriptografado: {codigo_decriptografado}")



