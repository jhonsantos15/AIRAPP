# check_db.py
from sqlalchemy import func, select
from app import create_app
from db import db
from models import Measurement

app = create_app()
with app.app_context():
    # Rango temporal
    mn, mx = db.session.execute(
        select(func.min(Measurement.fechah_local), func.max(Measurement.fechah_local))
    ).one()
    print("Rangos de tiempo (fechah_local, tz=America/Bogota):")
    print(mn, mx)

    # Conteo por dispositivo y canal
    print("\nConteo por dispositivo y canal:")
    rows = db.session.execute(
        select(Measurement.device_id, Measurement.sensor_channel, func.count())
        .group_by(Measurement.device_id, Measurement.sensor_channel)
        .order_by(Measurement.device_id, Measurement.sensor_channel)
    ).all()
    for device_id, channel, cnt in rows:
        print(device_id, channel, cnt)

    # Conteo por día
    print("\nConteo por día:")
    rows = db.session.execute(
        select(func.date(Measurement.fechah_local), func.count())
        .group_by(func.date(Measurement.fechah_local))
        .order_by(func.date(Measurement.fechah_local))
    ).all()
    for day, cnt in rows:
        print(day, cnt)
