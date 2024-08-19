import smtplib
from email.mime.text import MIMEText

def send_reset_email(email, reset_link):
    sender = "conectividadecanon@outlook.com"
    
    msg = MIMEText(f"Use este link para redefinir sua senha: {reset_link}")
    msg["Subject"] = "Redefinição de senha"
    msg["From"] = sender
    msg["To"] = email

    # Conexão com o relay sem autenticação na porta 25
    with smtplib.SMTP("Melville-app-mail.cusa.canon.com", 25) as server:
        server.sendmail(sender, email, msg.as_string())

reset_link = "https://your-app.com/reset-password?token=unique_token"
send_reset_email("tmedeiros@cusa.canon.com", reset_link)
