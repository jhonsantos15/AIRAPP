import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from db import db
from models import Measurement, SensorChannel

BOGOTA = ZoneInfo("America/Bogota")


def seed_one_day(day_str=None):
    if day_str:
        day = datetime.strptime(day_str, "%Y-%m-%d").date()
    else:
        day = datetime.now(BOGOTA).date()

    devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
    start = datetime(day.year, day.month, day.day, 0, 0, tzinfo=BOGOTA)
    for device in devices:
        t = start
        for _ in range(60 * 24):  # 1 punto por minuto
            base = {
                "device_id": device,
                "fecha": t.date(),
                "hora": t.time().replace(microsecond=0),
                "fechah_local": t,
                "doy": int(t.strftime("%j")),
                "w": None,
                "temp": 22 + random.uniform(-2, 4),
                "rh": 60 + random.uniform(-10, 10),
                "raw_json": "{}",
            }
            # Um1
            db.session.add(
                Measurement(
                    **base,
                    sensor_channel=SensorChannel.Um1,
                    pm25=max(0.0, 8 + 3 * random.random()),
                    pm10=max(0.0, 15 + 5 * random.random()),
                )
            )
            # Um2
            db.session.add(
                Measurement(
                    **base,
                    sensor_channel=SensorChannel.Um2,
                    pm25=max(0.0, 7 + 2 * random.random()),
                    pm10=max(0.0, 13 + 4 * random.random()),
                )
            )
            t += timedelta(minutes=1)
    db.session.commit()
