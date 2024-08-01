from cryptography.fernet import Fernet

# Carregue a chave de um arquivo de configuração ou variável de ambiente
def load_key():
    return open('secret.key', 'rb').read()

key = load_key()
cipher_suite = Fernet(key)

def decrypt_code(encrypted_code: str) -> str:
    decrypted_number = cipher_suite.decrypt('encrypted_code'.encode())
    return decrypted_number.decode()

# Suponha que o código criptografado seja fornecido pelo cliente
encrypted_code_from_client = '...'  # Substitua pelo código fornecido pelo cliente
decrypted_number = decrypt_code(encrypted_code_from_client)
print("Número descriptografado:", decrypted_number)
