"""
Schemas para solicitudes de reportes.
"""
from typing import List, Optional
from datetime import date

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Schema para solicitud de generación de reporte."""

    device_ids: Optional[List[str]] = Field(
        None, description="Lista de device IDs. None = todos"
    )
    start_date: date = Field(..., description="Fecha inicio del reporte")
    end_date: date = Field(..., description="Fecha fin del reporte")
    variables: List[str] = Field(
        ["pm25", "pm10", "temp", "rh"],
        description="Variables a incluir en el reporte",
    )
    channels: Optional[List[str]] = Field(
        None, description="Canales de sensores (um1, um2). None = ambos"
    )
