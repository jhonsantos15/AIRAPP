import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Cargar .env lo antes posible
load_dotenv()

from flask import Flask, jsonify, request, render_template
from flask_migrate import Migrate

from db import db, init_engine_and_session
from models import Measurement, SensorChannel
from dashboards.layout import build_layout
from dashboards.callbacks import register_callbacks

BOGOTA = ZoneInfo("America/Bogota")


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///aireapp.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambie_esto")
    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        init_engine_and_session()
        db.create_all()

    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler("logs/aireapp.log", maxBytes=2_000_000, backupCount=3)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("AireApp iniciado")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.get("/api/series")
    def api_series():
        q_devices = request.args.get("device_id", "").strip()
        q_channel = request.args.get("sensor_channel", "ambos").strip()
        q_vars = request.args.get("vars", "pm25,pm10,temp,rh").strip().lower()
        q_date = request.args.get("date")

        variables = set([v.strip() for v in q_vars.split(",") if v.strip()])

        if q_date:
            try:
                sel_day = datetime.strptime(q_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "date debe ser yyyy-mm-dd"}), 400
        else:
            sel_day = datetime.now(BOGOTA).date()

        day_start = datetime.combine(sel_day, time(0, 0, 0)).replace(tzinfo=BOGOTA)
        day_end = day_start + timedelta(days=1) - timedelta(seconds=1)

        devices = None
        if q_devices:
            devices = [d.strip() for d in q_devices.split(",") if d.strip()]

        channels = []
        if q_channel.lower() in ("um1", "um2"):
            channels = [SensorChannel[q_channel]]
        else:
            channels = [SensorChannel.Um1, SensorChannel.Um2]

        qry = Measurement.query.filter(
            Measurement.fechah_local >= day_start,
            Measurement.fechah_local <= day_end,
            Measurement.sensor_channel.in_(channels),
        )
        if devices:
            qry = qry.filter(Measurement.device_id.in_(devices))

        rows = qry.order_by(Measurement.fechah_local.asc()).all()

        def pick(valname, row):
            return getattr(row, valname) if valname in {"pm25", "pm10", "temp", "rh"} else None

        payload = []
        for r in rows:
            item = {
                "ts": r.fechah_local.isoformat(),
                "device_id": r.device_id,
                "Um": r.sensor_channel.name,
            }
            for v in variables:
                item[v] = pick(v, r)
            payload.append(item)

        return jsonify({"tz": "America/Bogota", "points": payload})

    from dash import Dash
    dash_app = Dash(
        __name__,
        server=app,
        url_base_pathname="/dash/",
        title="Calidad del Aire – Sensores Bajo Costo",
        suppress_callback_exceptions=True,
        assets_folder="static",
    )
    dash_app.layout = build_layout(app)
    register_callbacks(dash_app, app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
