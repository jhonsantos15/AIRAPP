from models import to_bogota_dt


def test_to_bogota_from_fecha_hora():
    dt = to_bogota_dt("2025-10-02", "12:34:56", None)
    assert dt.tzinfo is not None
    assert dt.hour == 12 and dt.minute == 34 and dt.second == 56


def test_to_bogota_from_fechah():
    dt = to_bogota_dt(None, None, "2025-10-02T07:00:00")
    assert dt.tzinfo is not None
    assert dt.year == 2025 and dt.month == 10 and dt.day == 2
