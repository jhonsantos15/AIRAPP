# check_db.py
from datetime import datetime
import pandas as pd
from flask import Flask

from db import db, get_db_uri
from models import Measurement, SensorChannel

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = get_db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app

def inspect():
    app = create_app()
    with app.app_context():
        rows = (
            db.session.query(
                Measurement.device_id,
                Measurement.sensor_channel,
                Measurement.fechah_local
            )
            .order_by(Measurement.fechah_local.asc())
            .all()
        )
        if not rows:
            print("No hay filas en Measurement.")
            return

        df = pd.DataFrame(rows, columns=["device_id", "sensor_channel", "fechah_local"])
        ts = pd.to_datetime(df["fechah_local"], errors="coerce")
        # Asume hora local si naive
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("America/Bogota")
        else:
            ts = ts.dt.tz_convert("America/Bogota")
        df["ts"] = ts
        df["day"] = df["ts"].dt.date
        df["Um"] = df["sensor_channel"].apply(lambda x: getattr(x, "name", str(x)))
        g = df.groupby(["device_id", "Um", "day"]).size().reset_index(name="count")
        print("\nConteo por día, dispositivo y canal:")
        print(g.to_string(index=False))
        print("\nRango global (America/Bogota):")
        print("min:", df["ts"].min())
        print("max:", df["ts"].max())

if __name__ == "__main__":
    inspect()
