from __future__ import annotations
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
import json
from typing import Optional
import enum  # <-- importante

from sqlalchemy import (
    String, Integer, Float, Date, Time, DateTime, Text,
    UniqueConstraint, Index, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column

from db import db

BOGOTA = ZoneInfo("America/Bogota")


class SensorChannel(enum.Enum):  # Enum de Python (estable en migraciones)
    Um1 = "Um1"
    Um2 = "Um2"


class Measurement(db.Model):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Enum en DB usando el Enum de Python y nombre estable para el tipo
    sensor_channel: Mapped[SensorChannel] = mapped_column(
        SAEnum(SensorChannel, name="sensorchannel"), nullable=False
    )

    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rh:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Fechas en zona Bogotá para navegación por día
    fecha: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hora:  Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    fechah_local: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    doy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    w:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(BOGOTA)
    )

    __table_args__ = (
        # Evita duplicados por equipo/canal/instante (clave “natural”)
        UniqueConstraint("device_id", "sensor_channel", "fechah_local", name="uq_device_channel_ts"),
        # Búsquedas rápidas por rango temporal y por día
        Index("idx_fechah_local", "fechah_local"),
        Index("idx_device_fecha", "device_id", "fecha"),
    )


# --------- Helpers para parsing de fechas ----------
def to_bogota_dt(fecha: Optional[str], hora: Optional[str], fechah: Optional[str]) -> datetime:
    """
    Convierte (Fecha + Hora) o (FechaH) a datetime tz-aware en America/Bogota.
    Acepta:
      Fecha: 'YYYY-MM-DD' o 'DD/MM/YYYY'
      Hora:  'HH:MM[:SS]'
      FechaH: ISO-like 'YYYY-MM-DDTHH:MM:SS[Z]' o 'YYYY/MM/DD HH:MM:SS', etc.
    """
    if fechah:
        s = fechah.strip().replace("Z", "")
        fmts = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
        ]
        for fmt in fmts:
            try:
                dt = datetime.strptime(s, fmt).replace(tzinfo=BOGOTA)
                return dt
            except ValueError:
                continue

    # Si viene separado
    if not fecha:
        raise ValueError("Fecha u FechaH requeridos")
    f = fecha.strip()
    d = None
    for fmtf in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(f, fmtf).date()
            break
        except ValueError:
            continue
    if d is None:
        raise ValueError("Formato de Fecha inválido")

    if not hora:
        h = time(0, 0, 0)
    else:
        hs = hora.strip()
        h = None
        for fmth in ("%H:%M:%S", "%H:%M"):
            try:
                h = datetime.strptime(hs, fmth).time()
                break
            except ValueError:
                continue
        if h is None:
            raise ValueError("Formato de Hora inválido")

    return datetime(d.year, d.month, d.day, h.hour, h.minute, h.second, tzinfo=BOGOTA)


def row_from_payload(payload: dict, device_id_fallback: Optional[str] = None) -> dict:
    """
    Mapea JSON crudo a campos del ORM (se invoca dos veces si hay datos para Um1 y Um2).
    """
    device_id = payload.get("DeviceId") or device_id_fallback or "UNKNOWN"

    # Variables crudas
    fecha = payload.get("Fecha")
    hora = payload.get("Hora")
    fechah = payload.get("FechaH")
    doy = payload.get("DOY")
    w = payload.get("W")
    temp = payload.get("temp")
    rh = payload.get("hr")

    dt_local = to_bogota_dt(fecha, hora, fechah)

    # helpers numéricos simples
    def _as_float(x):
        try:
            return float(x) if x is not None else None
        except Exception:
            return None

    def _as_int(x):
        try:
            return int(x) if x is not None else None
        except Exception:
            return None

    return {
        "device_id": device_id,
        "fecha": dt_local.date(),
        "hora": dt_local.time().replace(microsecond=0),
        "fechah_local": dt_local,
        "doy": _as_int(doy),
        "w": _as_float(w),
        "temp": _as_float(temp),
        "rh": _as_float(rh),
        "raw_json": json.dumps(payload, ensure_ascii=False),
    }
