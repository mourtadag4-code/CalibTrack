import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def send_email(subject: str, html_body: str, recipients: list[str]):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.sendmail(Config.MAIL_FROM, recipients, msg.as_string())