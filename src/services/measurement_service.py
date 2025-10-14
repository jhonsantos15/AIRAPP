"""
Servicio para operaciones con mediciones de sensores.
"""
from datetime import datetime, date, time
from typing import List, Optional, Dict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from src.core.models import Measurement, SensorChannel
from src.utils.constants import BOGOTA

logger = logging.getLogger(__name__)


class MeasurementService:
    """
    Servicio de negocio para mediciones.
    Centraliza queries y lógica de negocio relacionada con measurements.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_by_id(self, measurement_id: int) -> Optional[Measurement]:
        """Obtiene medición por ID."""
        return self.db.query(Measurement).filter(Measurement.id == measurement_id).first()

    def get_measurements(
        self,
        device_ids: Optional[List[str]] = None,
        channels: Optional[List[SensorChannel]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Measurement]:
        """Obtiene mediciones con filtros."""
        query = self.db.query(Measurement)

        if device_ids:
            query = query.filter(Measurement.device_id.in_(device_ids))

        if channels:
            query = query.filter(Measurement.sensor_channel.in_(channels))

        if start_date:
            start_dt = datetime.combine(start_date, time(0, 0, 0)).replace(tzinfo=BOGOTA)
            query = query.filter(Measurement.fechah_local >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, time(23, 59, 59)).replace(tzinfo=BOGOTA)
            query = query.filter(Measurement.fechah_local <= end_dt)

        return (
            query.order_by(Measurement.fechah_local.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_measurements(
        self,
        device_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """Cuenta mediciones con filtros."""
        query = self.db.query(func.count(Measurement.id))

        if device_ids:
            query = query.filter(Measurement.device_id.in_(device_ids))

        if start_date:
            start_dt = datetime.combine(start_date, time(0, 0, 0)).replace(tzinfo=BOGOTA)
            query = query.filter(Measurement.fechah_local >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, time(23, 59, 59)).replace(tzinfo=BOGOTA)
            query = query.filter(Measurement.fechah_local <= end_dt)

        return query.scalar()

    def get_stats(
        self,
        device_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict:
        """Obtiene estadísticas agregadas."""
        query = self.db.query(
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

        if device_ids:
            query = query.filter(Measurement.device_id.in_(device_ids))

        if start_date:
            start_dt = datetime.combine(start_date, time(0, 0, 0)).replace(tzinfo=BOGOTA)
            query = query.filter(Measurement.fechah_local >= start_dt)

        if end_date:
            end_dt = datetime.combine(end_date, time(23, 59, 59)).replace(tzinfo=BOGOTA)
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

    def save_measurements(self, measurements: List[Measurement]) -> int:
        """
        Guarda mediciones evitando duplicados.
        
        Returns:
            Número de registros nuevos insertados
        """
        if not measurements:
            return 0

        logger.info(f"Procesando {len(measurements)} mediciones para guardar")

        # Normalizar timestamps a segundos (eliminar microsegundos)
        for m in measurements:
            if m.fechah_local:
                m.fechah_local = m.fechah_local.replace(microsecond=0)

        # Extraer claves únicas normalizadas
        keys_to_check = [
            (m.device_id, m.sensor_channel.value if isinstance(m.sensor_channel, SensorChannel) else m.sensor_channel, m.fechah_local) 
            for m in measurements
        ]

        # Consultar existentes
        from sqlalchemy import tuple_

        existing = self.db.query(
            Measurement.device_id,
            Measurement.sensor_channel,
            Measurement.fechah_local,
        ).filter(
            tuple_(
                Measurement.device_id,
                Measurement.sensor_channel,
                Measurement.fechah_local,
            ).in_(keys_to_check)
        ).all()

        # Normalizar existing_keys (convertir SensorChannel enum a string)
        existing_keys = {
            (row[0], row[1].value if isinstance(row[1], SensorChannel) else row[1], row[2])
            for row in existing
        }

        logger.info(f"Encontrados {len(existing_keys)} duplicados en BD")

        # Filtrar nuevos
        new_measurements = [
            m
            for m in measurements
            if (
                m.device_id, 
                m.sensor_channel.value if isinstance(m.sensor_channel, SensorChannel) else m.sensor_channel,
                m.fechah_local
            ) not in existing_keys
        ]

        logger.info(f"Insertando {len(new_measurements)} mediciones nuevas")

        # Guardar con manejo de errores
        if new_measurements:
            try:
                self.db.bulk_save_objects(new_measurements)
                self.db.commit()
                logger.info(f"✓ Batch guardado exitosamente: {len(new_measurements)} registros")
            except Exception as e:
                logger.error(f"Error en bulk_save, intentando inserción individual: {e}")
                self.db.rollback()
                # Intentar inserción uno por uno para identificar duplicados específicos
                inserted = 0
                for measurement in new_measurements:
                    try:
                        self.db.add(measurement)
                        self.db.commit()
                        inserted += 1
                    except Exception as inner_e:
                        self.db.rollback()
                        logger.debug(f"Saltando duplicado: {measurement.device_id} - {measurement.fechah_local}")
                        continue
                logger.info(f"Insertados {inserted} de {len(new_measurements)} mediante inserción individual")
                return inserted

        return len(new_measurements)
