from cryptography.fernet import Fernet



def encrypt_number(number: str) -> str:
    key = open('secret.key', 'rb').read()
    cipher_suite = Fernet(key)
    encrypted_number = cipher_suite.encrypt(number.encode())
    return encrypted_number.decode()

def gerar_nova_chave(): 
    # Salve a chave em um arquivo de configuração ou variável de ambiente
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)

# Exemplo de criptografia
print("Código criptografado:", encrypt_number('123456'))



