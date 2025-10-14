"""
Rutas API para mediciones de sensores.
"""
from typing import List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from src.api.dependencies import get_db
from src.core.models import Measurement, SensorChannel
from src.schemas.measurement import MeasurementResponse, MeasurementListResponse
from src.utils.labels import get_all_devices

router = APIRouter()


@router.get("/measurements", response_model=MeasurementListResponse)
def get_measurements(
    device_ids: Optional[str] = Query(None, description="Device IDs separados por coma"),
    channels: Optional[str] = Query(None, description="Canales: um1, um2, o ambos"),
    start_date: Optional[date] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    variables: Optional[str] = Query(
        "pm25,pm10,temp,rh", description="Variables: pm25,pm10,temp,rh"
    ),
    limit: int = Query(1000, ge=1, le=10000, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
):
    """
    Obtiene mediciones con filtros opcionales.
    
    - **device_ids**: IDs de dispositivos separados por coma
    - **channels**: um1, um2, o ambos (por defecto ambos)
    - **start_date**: Fecha inicio
    - **end_date**: Fecha fin
    - **variables**: Variables a incluir
    - **limit**: Máximo de resultados (default 1000, max 10000)
    - **offset**: Para paginación
    """
    query = db.query(Measurement)

    # Filtro por devices
    if device_ids:
        device_list = [d.strip() for d in device_ids.split(",") if d.strip()]
        if device_list:
            query = query.filter(Measurement.device_id.in_(device_list))

    # Filtro por channels
    if channels:
        channel_list = []
        for ch in channels.lower().split(","):
            ch = ch.strip()
            if ch in ("um1", "sensor1", "s1"):
                channel_list.append(SensorChannel.Um1)
            elif ch in ("um2", "sensor2", "s2"):
                channel_list.append(SensorChannel.Um2)
        if channel_list:
            query = query.filter(Measurement.sensor_channel.in_(channel_list))

    # Filtro por fechas
    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Measurement.fechah_local >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Measurement.fechah_local <= end_dt)

    # Contar total
    total = query.count()

    # Ordenar y paginar
    measurements = (
        query.order_by(Measurement.fechah_local.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "count": len(measurements),
        "offset": offset,
        "limit": limit,
        "data": measurements,
    }


@router.get("/measurements/stats")
def get_measurements_stats(
    device_ids: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Obtiene estadísticas agregadas de mediciones.
    """
    query = db.query(
        func.count(Measurement.id).label("count"),
        func.avg(Measurement.pm25).label("avg_pm25"),
        func.max(Measurement.pm25).label("max_pm25"),
        func.min(Measurement.pm25).label("min_pm25"),
        func.avg(Measurement.pm10).label("avg_pm10"),
        func.max(Measurement.pm10).label("max_pm10"),
        func.min(Measurement.pm10).label("min_pm10"),
        func.avg(Measurement.temp).label("avg_temp"),
        func.avg(Measurement.rh).label("avg_rh"),
    )

    # Filtros
    if device_ids:
        device_list = [d.strip() for d in device_ids.split(",") if d.strip()]
        if device_list:
            query = query.filter(Measurement.device_id.in_(device_list))

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Measurement.fechah_local >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Measurement.fechah_local <= end_dt)

    result = query.one()

    return {
        "count": result.count,
        "pm25": {
            "avg": round(result.avg_pm25, 2) if result.avg_pm25 else None,
            "max": round(result.max_pm25, 2) if result.max_pm25 else None,
            "min": round(result.min_pm25, 2) if result.min_pm25 else None,
        },
        "pm10": {
            "avg": round(result.avg_pm10, 2) if result.avg_pm10 else None,
            "max": round(result.max_pm10, 2) if result.max_pm10 else None,
            "min": round(result.min_pm10, 2) if result.min_pm10 else None,
        },
        "temp": {
            "avg": round(result.avg_temp, 2) if result.avg_temp else None,
        },
        "rh": {
            "avg": round(result.avg_rh, 2) if result.avg_rh else None,
        },
    }


@router.get("/measurements/{measurement_id}", response_model=MeasurementResponse)
def get_measurement_by_id(measurement_id: int, db: Session = Depends(get_db)):
    """Obtiene una medición específica por ID."""
    measurement = db.query(Measurement).filter(Measurement.id == measurement_id).first()
    if not measurement:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return measurement
