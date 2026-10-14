import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///calibration.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    MAIL_FROM = os.environ.get("MAIL_FROM", "no-reply@example.com")

    # Destinataires (séparés par des virgules)
    ALERT_RECIPIENTS = [e.strip() for e in os.environ.get(
        "ALERT_RECIPIENTS", "responsable@example.com").split(",") if e.strip()]

    # Combien de jours avant la date on alerte
    ALERT_DAYS_BEFORE = int(os.environ.get("ALERT_DAYS_BEFORE", 30))