from datetime import date, timedelta
from models import db, Product
from mailer import send_email
from config import Config

def get_alert_recipients():
    """Récupère les destinataires depuis la DB. Fallback sur .env si vide."""
    from models import Recipient
    emails = [r.email for r in Recipient.query.order_by(Recipient.email).all()]
    if emails:
        return emails
    return Config.ALERT_RECIPIENTS

def check_calibrations(app):
    """Parcourt les produits et envoie un mail pour ceux dont la prochaine
    calibration arrive dans moins de ALERT_DAYS_BEFORE jours."""
    with app.app_context():
        today = date.today()
        limit = today + timedelta(days=Config.ALERT_DAYS_BEFORE)

        products = Product.query.filter(
            Product.next_calibration <= limit
        ).order_by(Product.next_calibration.asc()).all()

        # On ne garde que ceux pour qui on n'a pas déjà alerté pour cette échéance
        to_alert = [p for p in products if p.alert_sent_for != p.next_calibration]
        if not to_alert:
            print("[scheduler] Aucune alerte à envoyer.")
            return

        rows = ""
        for p in to_alert:
            d = p.days_left()
            color = "#dc3545" if d <= 7 else "#ffc107" if d <= 30 else "#28a745"
            etat = "DÉPASSÉ" if d < 0 else f"dans {d} jour(s)"
            rows += f"""
            <tr>
              <td>{p.code}</td>
              <td>{p.name}</td>
              <td>{p.zone}</td>
              <td>{p.last_calibration.strftime('%d/%m/%Y')}</td>
              <td><b style="color:{color}">{p.next_calibration.strftime('%d/%m/%Y')}</b>
                  <br><small>{etat}</small></td>
            </tr>"""

        html = f"""
        <html><body style="font-family:Arial,sans-serif">
        <h2>⚠️ Calibrations à prévoir</h2>
        <p>Les produits suivants arrivent à échéance de calibration
           (fenêtre de {Config.ALERT_DAYS_BEFORE} jours) :</p>
        <table border="1" cellpadding="8" cellspacing="0"
               style="border-collapse:collapse">
          <thead style="background:#f0f0f0">
            <tr><th>ID</th><th>Nom</th><th>Zone</th>
                <th>Dernière calib.</th><th>Prochaine calib.</th></tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        <p style="color:#888;font-size:12px">
          Message automatique — merci de ne pas répondre.</p>
        </body></html>"""

        send_email(
            subject=f"[Calibration] {len(to_alert)} produit(s) à recalibrer",
            html_body=html,
            recipients=get_alert_recipients(),
        )

        # Marquer comme envoyé pour ne pas spammer
        for p in to_alert:
            p.alert_sent_for = p.next_calibration
        db.session.commit()
        print(f"[scheduler] {len(to_alert)} alerte(s) envoyée(s).")