from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)      # ID métier
    name = db.Column(db.String(200), nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    last_calibration = db.Column(db.Date, nullable=False)
    next_calibration = db.Column(db.Date, nullable=False)

    # Pour éviter d'envoyer plusieurs fois le même rappel
    alert_sent_for = db.Column(db.Date, nullable=True)

    def days_left(self):
        return (self.next_calibration - date.today()).days

    def status(self):
        d = self.days_left()
        if d < 0:
            return "danger"      # dépassé
        if d <= 7:
            return "danger"
        if d <= 30:
            return "warning"
        return "success"

class Recipient(db.Model):
    __tablename__ = "recipients"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)