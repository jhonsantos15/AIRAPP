"""
SQLAlchemy models for air quality measurements.
"""
from __future__ import annotations
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
import json
from typing import Optional
import enum

from sqlalchemy import (
    String, Integer, Float, Date, Time, DateTime, Text,
    UniqueConstraint, Index, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import db

BOGOTA = ZoneInfo("America/Bogota")


class SensorChannel(enum.Enum):
    """Enum for sensor channels (Um1, Um2)."""
    Um1 = "Um1"
    Um2 = "Um2"


class Measurement(db.Model):
    """
    Model for air quality measurements.
    Stores PM2.5, PM10, temperature, and humidity readings from sensors.
    """
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Sensor channel enum
    sensor_channel: Mapped[SensorChannel] = mapped_column(
        SAEnum(SensorChannel, name="sensorchannel"), 
        nullable=False
    )

    # Measurements
    pm25: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pm10: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps in Bogota timezone
    fecha: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hora: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    fechah_local: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )

    # Additional fields
    doy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Day of year
    w: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Raw JSON payload
    raw_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(BOGOTA)
    )

    __table_args__ = (
        # Unique constraint to avoid duplicates
        UniqueConstraint(
            "device_id", "sensor_channel", "fechah_local", 
            name="uq_device_channel_ts"
        ),
        # Indexes for fast queries
        Index("idx_fechah_local", "fechah_local"),
        Index("idx_device_fecha", "device_id", "fecha"),
        Index("idx_duplicate_check", "device_id", "sensor_channel", "fechah_local"),
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "sensor_channel": self.sensor_channel.name,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "temp": self.temp,
            "rh": self.rh,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora": self.hora.isoformat() if self.hora else None,
            "fechah_local": self.fechah_local.isoformat() if self.fechah_local else None,
            "doy": self.doy,
            "w": self.w,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# --------- Helper functions for date parsing ----------

def to_bogota_dt(
    fecha: Optional[str], 
    hora: Optional[str], 
    fechah: Optional[str]
) -> datetime:
    """
    Convert (Fecha + Hora) or (FechaH) to timezone-aware datetime in America/Bogota.
    
    Accepts:
      Fecha: 'YYYY-MM-DD' or 'DD/MM/YYYY'
      Hora:  'HH:MM[:SS]'
      FechaH: ISO-like 'YYYY-MM-DDTHH:MM:SS[Z]' or 'YYYY/MM/DD HH:MM:SS', etc.
    
    Args:
        fecha: Date string
        hora: Time string
        fechah: Combined datetime string
        
    Returns:
        Timezone-aware datetime in Bogota timezone
        
    Raises:
        ValueError: If date format is invalid
    """
    if fechah:
        s = fechah.strip().replace("Z", "")
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt).replace(tzinfo=BOGOTA)
                return dt
            except ValueError:
                continue

    # If separate fecha and hora
    if not fecha:
        raise ValueError("Fecha or FechaH required")
    
    f = fecha.strip()
    d = None
    for date_fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(f, date_fmt).date()
            break
        except ValueError:
            continue
    
    if d is None:
        raise ValueError("Invalid Fecha format")

    if not hora:
        h = time(0, 0, 0)
    else:
        hs = hora.strip()
        h = None
        for time_fmt in ("%H:%M:%S", "%H:%M"):
            try:
                h = datetime.strptime(hs, time_fmt).time()
                break
            except ValueError:
                continue
        if h is None:
            raise ValueError("Invalid Hora format")

    return datetime(
        d.year, d.month, d.day, 
        h.hour, h.minute, h.second, 
        tzinfo=BOGOTA
    )


def row_from_payload(
    payload: dict, 
    device_id_fallback: Optional[str] = None
) -> dict:
    """
    Map raw JSON payload to ORM fields.
    Called twice if data exists for both Um1 and Um2.
    
    Args:
        payload: Raw JSON payload from sensor
        device_id_fallback: Fallback device ID if not in payload
        
    Returns:
        Dictionary with mapped fields for Measurement model
    """
    device_id = payload.get("DeviceId") or device_id_fallback or "UNKNOWN"

    # Raw variables
    fecha = payload.get("Fecha")
    hora = payload.get("Hora")
    fechah = payload.get("FechaH")
    doy = payload.get("DOY")
    w = payload.get("W")
    temp = payload.get("temp")
    rh = payload.get("hr")

    dt_local = to_bogota_dt(fecha, hora, fechah)

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
