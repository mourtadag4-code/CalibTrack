from datetime import date
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    last_calibration = db.Column(db.Date, nullable=False)
    next_calibration = db.Column(db.Date, nullable=False)
    
    # Nouvelle colonne Statut
    status = db.Column(db.String(50), default="NON FAIT", nullable=False)
    
    # alert_sent_for devient un texte pour stocker les paliers (ex: "2026-12-15:J-7,2026-12-15:J-0")
    alert_sent_for = db.Column(db.String(255), nullable=True)

    def days_left(self):
        return (self.next_calibration - date.today()).days

    def status_color(self):
        colors = {
            "FAIT": "success",       # Vert
            "NON FAIT": "secondary", # Gris
            "EN COURS": "info",      # Bleu clair
            "À CALIBRER": "warning"  # Orange
        }
        return colors.get(self.status, "secondary")

    def urgency_color(self):
        d = self.days_left()
        if d < 0:
            return "danger"      # dépassé
        if d <= 7:
            return "danger"
        if d <= 45:
            return "warning"     # orange à partir de 45 jours
        return "success"


class Recipient(db.Model):
    __tablename__ = "recipients"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)