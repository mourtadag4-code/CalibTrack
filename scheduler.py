from datetime import date, timedelta
from models import db, Product, Recipient
from mailer import send_email
from config import Config


def get_alert_recipients():
    emails = [r.email for r in Recipient.query.order_by(Recipient.email).all()]
    if emails:
        return emails
    return Config.ALERT_RECIPIENTS


def get_recipients_with_names():
    recipients = Recipient.query.order_by(Recipient.email).all()
    if recipients:
        return [(r.email, r.name) for r in recipients]
    return [(email, None) for email in Config.ALERT_RECIPIENTS]


def _plural_days(n):
    return f"{n} jour" if n == 1 else f"{n} jours"


def _build_alert_text(name, product):
    d = (product.next_calibration - date.today()).days
    greeting_name = name if name else "Madame, Monsieur"

    if d > 1:
        phrase = f"Devra passer en calibration dans exactement {_plural_days(d)} compte à rebours"
    elif d == 1:
        phrase = "Devra passer en calibration dans exactement 1 jour"
    elif d == 0:
        phrase = "Devra passer en calibration aujourd'hui"
    else:
        phrase = f"Aurait dû passer en calibration depuis {_plural_days(-d)}"

    text = (
        f"Bonjour {greeting_name},\n"
        f"\n"
        f"L'équipement suivant : {product.name}\n"
        f"\n"
        f"{phrase}\n"
        f"\n"
        f"Merci de faire le nécessaire.\n"
        f"\n"
        f"CalibTrack"
    )
    return text.replace("\n", "<br>")


def check_calibrations(app):
    """Vérifie les produits et envoie les alertes. Retourne (nb_envoyés, message)."""
    with app.app_context():
        today = date.today()
        limit = today + timedelta(days=Config.ALERT_DAYS_BEFORE)

        products = Product.query.filter(
            Product.next_calibration <= limit
        ).order_by(Product.next_calibration.asc()).all()

        to_alert = [p for p in products if p.alert_sent_for != p.next_calibration]
        
        if not to_alert:
            return 0, "Aucun produit n'est dans la marge de calibration (ou ils ont déjà été notifiés)."

        recipients = get_recipients_with_names()
        if not recipients:
            return 0, "Aucun destinataire configuré."

        sent_count = 0
        for p in to_alert:
            for email, name in recipients:
                body = _build_alert_text(name, p)
                try:
                    send_email(
                        subject=f"[CalibTrack] Calibration : {p.name}",
                        html_body=body,
                        recipients=[email],
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"[scheduler] Échec envoi à {email} : {e}")
            
            # Marquer le produit comme notifié pour cette date
            p.alert_sent_for = p.next_calibration

        db.session.commit()
        return sent_count, f"{sent_count} email(s) envoyé(s) avec succès."