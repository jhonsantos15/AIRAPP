"""
Schemas para dispositivos IoT.
"""
from typing import Optional
from pydantic import BaseModel


class DeviceResponse(BaseModel):
    """Schema para información básica de dispositivo."""

    device_id: str
    label: str
    measurement_count: int
    last_measurement: Optional[str] = None


class DeviceStatsResponse(BaseModel):
    """Schema para estadísticas detalladas de dispositivo."""

    device_id: str
    label: str
    total_measurements: int
    first_measurement: Optional[str] = None
    last_measurement: Optional[str] = None
    avg_pm25: Optional[float] = None
    avg_pm10: Optional[float] = None
    avg_temp: Optional[float] = None
    avg_rh: Optional[float] = None
    channels_count: int
