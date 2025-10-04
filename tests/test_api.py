from datetime import datetime
from zoneinfo import ZoneInfo
from db import db
from models import Measurement, SensorChannel

BOGOTA = ZoneInfo("America/Bogota")


def test_api_series_ok(client, app):
    # Inserta una fila de ejemplo
    with app.app_context():
        t = datetime(2025, 10, 2, 8, 0, tzinfo=BOGOTA)
        m = Measurement(
            device_id="S1_PMTHVD",
            sensor_channel=SensorChannel.Um1,
            pm25=10.0, pm10=15.0, temp=23.0, rh=60.0,
            fecha=t.date(), hora=t.time(),
            fechah_local=t, doy=int(t.strftime("%j")), w=None,
            raw_json="{}",
        )
        db.session.add(m); db.session.commit()

    qs = {
        "device_id": "S1_PMTHVD",
        "sensor_channel": "Um1",
        "vars": "pm25,pm10,temp,rh",
        "date": "2025-10-02",
    }
    r = client.get("/api/series", query_string=qs)
    assert r.status_code == 200
    data = r.get_json()
    assert "points" in data and len(data["points"]) >= 1
    p0 = data["points"][0]
    assert p0["device_id"] == "S1_PMTHVD"
    assert "pm25" in p0 and "pm10" in p0
