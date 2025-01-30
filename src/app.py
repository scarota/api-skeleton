from flask import Flask
from src.extensions import db
from src.endpoints import api
from datetime import time
from src.models import Doctor


def initialize_doctors():
    if Doctor.query.count() == 0:
        dr_strange = Doctor(
            name="Strange", start_time=time(9, 0), end_time=time(17, 0)  # 9 AM  # 5 PM
        )
        dr_who = Doctor(
            name="Who", start_time=time(8, 0), end_time=time(16, 0)  # 8 AM  # 4 PM
        )
        db.session.add(dr_strange)
        db.session.add(dr_who)
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        initialize_doctors()
    app.register_blueprint(api, url_prefix="/api")
    return app
