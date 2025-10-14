"""
Rutas API para dispositivos.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from src.api.dependencies import get_db
from src.core.models import Measurement
from src.schemas.device import DeviceResponse, DeviceStatsResponse
from src.utils.labels import label_for, get_all_devices

router = APIRouter()


@router.get("/devices", response_model=List[DeviceResponse])
def get_devices(db: Session = Depends(get_db)):
    """
    Obtiene lista de todos los dispositivos con información básica.
    """
    # Obtener devices únicos de la BD
    db_devices = (
        db.query(
            Measurement.device_id,
            func.count(Measurement.id).label("measurement_count"),
            func.max(Measurement.fechah_local).label("last_measurement"),
        )
        .group_by(Measurement.device_id)
        .all()
    )

    # Combinar con labels conocidos
    known_devices = get_all_devices()
    
    devices = []
    for db_dev in db_devices:
        device_id = db_dev.device_id
        devices.append({
            "device_id": device_id,
            "label": label_for(device_id),
            "measurement_count": db_dev.measurement_count,
            "last_measurement": db_dev.last_measurement.isoformat() if db_dev.last_measurement else None,
        })

    return devices


@router.get("/devices/{device_id}", response_model=DeviceStatsResponse)
def get_device_stats(device_id: str, db: Session = Depends(get_db)):
    """
    Obtiene estadísticas detalladas de un dispositivo específico.
    """
    stats = (
        db.query(
            func.count(Measurement.id).label("total_measurements"),
            func.min(Measurement.fechah_local).label("first_measurement"),
            func.max(Measurement.fechah_local).label("last_measurement"),
            func.avg(Measurement.pm25).label("avg_pm25"),
            func.avg(Measurement.pm10).label("avg_pm10"),
            func.avg(Measurement.temp).label("avg_temp"),
            func.avg(Measurement.rh).label("avg_rh"),
            func.count(distinct(Measurement.sensor_channel)).label("channels_count"),
        )
        .filter(Measurement.device_id == device_id)
        .one_or_none()
    )

    if not stats or stats.total_measurements == 0:
        return {
            "device_id": device_id,
            "label": label_for(device_id),
            "total_measurements": 0,
            "first_measurement": None,
            "last_measurement": None,
            "avg_pm25": None,
            "avg_pm10": None,
            "avg_temp": None,
            "avg_rh": None,
            "channels_count": 0,
        }

    return {
        "device_id": device_id,
        "label": label_for(device_id),
        "total_measurements": stats.total_measurements,
        "first_measurement": stats.first_measurement.isoformat() if stats.first_measurement else None,
        "last_measurement": stats.last_measurement.isoformat() if stats.last_measurement else None,
        "avg_pm25": round(stats.avg_pm25, 2) if stats.avg_pm25 else None,
        "avg_pm10": round(stats.avg_pm10, 2) if stats.avg_pm10 else None,
        "avg_temp": round(stats.avg_temp, 2) if stats.avg_temp else None,
        "avg_rh": round(stats.avg_rh, 2) if stats.avg_rh else None,
        "channels_count": stats.channels_count,
    }
