import smtplib
from email.mime.text import MIMEText

def send_reset_email(email, reset_link):
    sender = "conectividadecanon@outlook.com"
    password = "Canon@12345"

    msg = MIMEText(f"Use este link para redefinir sua senha: {reset_link}")
    msg["Subject"] = "Redefinição de senha"
    msg["From"] = sender
    msg["To"] = email

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()  # Inicia a conexão segura TLS
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())

reset_link = "https://your-app.com/reset-password?token=unique_token"
send_reset_email("tmedeiros@cusa.canon.com", reset_link)
