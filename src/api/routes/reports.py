"""
Rutas API para generación de reportes (PDF y Excel).
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.services.report_service import ReportService
from src.schemas.report import ReportRequest

router = APIRouter()


@router.post("/reports/pdf")
def generate_pdf_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
):
    """
    Genera reporte PDF de mediciones.
    
    - **device_ids**: Lista de IDs de dispositivos
    - **start_date**: Fecha inicio
    - **end_date**: Fecha fin
    - **variables**: Variables a incluir (pm25, pm10, temp, rh)
    - **channels**: Canales de sensores (um1, um2)
    """
    report_service = ReportService(db)
    
    pdf_buffer = report_service.generate_pdf(
        device_ids=request.device_ids,
        start_date=request.start_date,
        end_date=request.end_date,
        variables=request.variables,
        channels=request.channels,
    )

    filename = f"reporte_{request.start_date}_{request.end_date}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/reports/excel")
def generate_excel_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
):
    """
    Genera reporte Excel de mediciones.
    Incluye TODOS los datos minuto a minuto del período seleccionado.
    
    - **device_ids**: Lista de IDs de dispositivos
    - **start_date**: Fecha inicio
    - **end_date**: Fecha fin
    - **variables**: Variables a incluir (pm25, pm10, temp, rh)
    - **channels**: Canales de sensores (um1, um2)
    """
    report_service = ReportService(db)
    
    excel_buffer = report_service.generate_excel(
        device_ids=request.device_ids,
        start_date=request.start_date,
        end_date=request.end_date,
        variables=request.variables,
        channels=request.channels,
    )

    filename = f"reporte_{request.start_date}_{request.end_date}.xlsx"
    
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/reports/preview")
def preview_report_data(
    device_ids: Optional[str] = Query(None, description="Device IDs separados por coma"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Preview de datos que se incluirían en el reporte.
    Útil para validar antes de generar el reporte completo.
    """
    report_service = ReportService(db)
    
    device_list = None
    if device_ids:
        device_list = [d.strip() for d in device_ids.split(",") if d.strip()]
    
    preview = report_service.preview_data(
        device_ids=device_list,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return preview
