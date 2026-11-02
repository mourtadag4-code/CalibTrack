from datetime import date, timedelta
from models import db, Product, Recipient
from mailer import send_email
from config import Config

def get_alert_recipients():
    emails = [r.email for r in Recipient.query.order_by(Recipient.email).all()]
    return emails if emails else Config.ALERT_RECIPIENTS

def get_recipients_with_names():
    recipients = Recipient.query.order_by(Recipient.email).all()
    return [(r.email, r.name) for r in recipients] if recipients else [(email, None) for email in Config.ALERT_RECIPIENTS]

def _build_alert_text(name, product):
    d = (product.next_calibration - date.today()).days
    greeting_name = name if name else "Madame, Monsieur"

    if d > 1:
        phrase = f"Devra passer en calibration dans exactement {d} jours"
    elif d == 1:
        phrase = "Devra passer en calibration dans exactement 1 jour"
    elif d == 0:
        phrase = "Devra passer en calibration aujourd'hui"
    else:
        phrase = f"Aurait dû passer en calibration depuis {abs(d)} jours"

    text = (
        f"Bonjour {greeting_name},\n\n"
        f"L'équipement suivant : {product.name}\n\n"
        f"{phrase}\n\n"
        f"Merci de faire le nécessaire.\n\n"
        f"CalibTrack"
    )
    return text.replace("\n", "<br>")

def check_calibrations(app):
    with app.app_context():
        today = date.today()
        
        # 1. AUTOMATISATION DU STATUT (1 mois = 30 jours avant)
        limit_30j = today + timedelta(days=30)
        products_30j = Product.query.filter(Product.next_calibration <= limit_30j).all()
        
        for p in products_30j:
            if p.status == "NON FAIT":
                p.status = "À CALIBRER"
        
        db.session.commit()

        # 2. ENVOI DES ALERTES (J-7 et J-0)
        # On cherche les produits qui arrivent dans 7 jours ou moins
        limit_7j = today + timedelta(days=7)
        products = Product.query.filter(Product.next_calibration <= limit_7j).order_by(Product.next_calibration.asc()).all()

        recipients = get_recipients_with_names()
        if not recipients:
            return 0, "Aucun destinataire configuré."

        sent_count = 0
        
        for p in products:
            d = (p.next_calibration - today).days
            
            # On détermine quel palier doit être notifié
            palier = None
            if d <= 0:
                palier = "J-0"
            elif d <= 7:
                palier = "J-7"
                
            if palier:
                # On crée une clé unique pour ce palier (ex: "2026-12-15:J-7")
                cle_palier = f"{p.next_calibration.isoformat()}:{palier}"
                deja_notifie = p.alert_sent_for or ""
                
                if cle_palier not in deja_notifie:
                    for email, name in recipients:
                        body = _build_alert_text(name, p)
                        try:
                            send_email(
                                subject=f"[CalibTrack] Calibration ({palier}) : {p.name}",
                                html_body=body,
                                recipients=[email],
                            )
                            sent_count += 1
                        except Exception as e:
                            print(f"[scheduler] Échec envoi à {email} : {e}")
                    
                    # On mémorise l'envoi
                    p.alert_sent_for = (deja_notifie + "," + cle_palier).strip(",")

        db.session.commit()
        
        if sent_count == 0:
            return 0, "Aucune nouvelle alerte à envoyer."
        return sent_count, f"{sent_count} email(s) envoyé(s) avec succès."