"""
Schemas para mediciones de sensores.
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeasurementResponse(BaseModel):
    """Schema para respuesta de medición individual."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    sensor_channel: str
    fechah_local: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    temp: Optional[float] = None
    rh: Optional[float] = None
    no2: Optional[float] = None
    co2: Optional[float] = None
    vel_viento: Optional[float] = None
    dir_viento: Optional[float] = None
    

class MeasurementListResponse(BaseModel):
    """Schema para respuesta de lista de mediciones con paginación."""

    total: int
    count: int
    offset: int
    limit: int
    data: List[MeasurementResponse]
