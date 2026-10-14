from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

load_dotenv()

from config import Config
from models import db, Product
from scheduler import check_calibrations
from mailer import send_email

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Routes ----------
    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        query = Product.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(Product.code.ilike(like),
                       Product.name.ilike(like),
                       Product.zone.ilike(like))
            )
        products = query.order_by(Product.next_calibration.asc()).all()
        return render_template("index.html", products=products, today=date.today())

    @app.route("/products/new", methods=["GET", "POST"])
    def create_product():
        if request.method == "POST":
            try:
                p = Product(
                    code=request.form["code"].strip(),
                    name=request.form["name"].strip(),
                    zone=request.form["zone"].strip(),
                    last_calibration=datetime.strptime(
                        request.form["last_calibration"], "%Y-%m-%d").date(),
                    next_calibration=datetime.strptime(
                        request.form["next_calibration"], "%Y-%m-%d").date(),
                )
            except (KeyError, ValueError):
                flash("Champs invalides.", "danger")
                return redirect(url_for("create_product"))

            if p.next_calibration < p.last_calibration:
                flash("La prochaine calibration doit être après la dernière.", "danger")
                return redirect(url_for("create_product"))

            if Product.query.filter_by(code=p.code).first():
                flash("Cet ID existe déjà.", "danger")
                return redirect(url_for("create_product"))

            db.session.add(p)
            db.session.commit()
            flash("Produit ajouté.", "success")
            return redirect(url_for("index"))
        return render_template("form.html", product=None)

    @app.route("/products/<int:pid>/edit", methods=["GET", "POST"])
    def edit_product(pid):
        p = Product.query.get_or_404(pid)
        if request.method == "POST":
            p.code = request.form["code"].strip()
            p.name = request.form["name"].strip()
            p.zone = request.form["zone"].strip()
            p.last_calibration = datetime.strptime(
                request.form["last_calibration"], "%Y-%m-%d").date()
            p.next_calibration = datetime.strptime(
                request.form["next_calibration"], "%Y-%m-%d").date()
            # Reset l'alerte si la date change
            p.alert_sent_for = None
            db.session.commit()
            flash("Produit mis à jour.", "success")
            return redirect(url_for("index"))
        return render_template("form.html", product=p)

    @app.route("/products/<int:pid>/delete", methods=["POST"])
    def delete_product(pid):
        p = Product.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        flash("Produit supprimé.", "success")
        return redirect(url_for("index"))

    # ---------- Commandes CLI ----------
    @app.cli.command("check-calibrations")
    def check_cmd():
        """Lance la vérification manuellement : flask check-calibrations"""
        check_calibrations(app)

    @app.cli.command("test-email")
    def test_email_cmd():
        """Envoie un email de test : flask test-email"""
        send_email("Test calibration",
                   "<p>Ceci est un test.</p>",
                   Config.ALERT_RECIPIENTS)
        print("Email de test envoyé à", Config.ALERT_RECIPIENTS)

    

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)