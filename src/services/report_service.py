"""
Servicio para generación de reportes PDF y Excel.
Centraliza la lógica de reports.py y reports_excel.py.
"""
from datetime import date, datetime, time
from io import BytesIO
from typing import List, Optional

from sqlalchemy.orm import Session

from src.core.models import Measurement, SensorChannel
from src.core.config import settings
from src.utils.constants import BOGOTA

# Imports para PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

# Imports para Excel
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

from src.utils.labels import label_for


class ReportService:
    """
    Servicio para generación de reportes de mediciones.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def _get_measurements(
        self,
        device_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        channels: Optional[List[str]] = None,
    ) -> List[Measurement]:
        """Obtiene mediciones filtradas."""
        start_dt = datetime.combine(start_date, time(0, 0, 0)).replace(tzinfo=BOGOTA)
        end_dt = datetime.combine(end_date, time(23, 59, 59)).replace(tzinfo=BOGOTA)

        query = self.db.query(Measurement).filter(
            Measurement.fechah_local >= start_dt, Measurement.fechah_local <= end_dt
        )

        if device_ids:
            query = query.filter(Measurement.device_id.in_(device_ids))

        if channels:
            channel_objs = []
            for ch in channels:
                if ch.lower() in ("um1", "sensor1"):
                    channel_objs.append(SensorChannel.Um1)
                elif ch.lower() in ("um2", "sensor2"):
                    channel_objs.append(SensorChannel.Um2)
            if channel_objs:
                query = query.filter(Measurement.sensor_channel.in_(channel_objs))

        return query.order_by(Measurement.fechah_local.asc()).all()

    def generate_pdf(
        self,
        device_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        variables: List[str],
        channels: Optional[List[str]] = None,
    ) -> BytesIO:
        """
        Genera reporte PDF.
        
        Returns:
            Buffer con el PDF generado
        """
        measurements = self._get_measurements(device_ids, start_date, end_date, channels)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Título
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#2C3E50"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        title = Paragraph(
            f"Reporte de Calidad del Aire<br/>{start_date} a {end_date}", title_style
        )
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))

        # Tabla de datos
        if measurements:
            data = [["Fecha/Hora", "Dispositivo", "Canal", "PM2.5", "PM10", "Temp", "RH"]]

            for m in measurements[:1000]:  # Limitar a 1000 para PDF
                row = [
                    m.fechah_local.strftime("%Y-%m-%d %H:%M"),
                    label_for(m.device_id),
                    m.sensor_channel.value,
                    f"{m.pm25:.1f}" if m.pm25 else "-",
                    f"{m.pm10:.1f}" if m.pm10 else "-",
                    f"{m.temp:.1f}" if m.temp else "-",
                    f"{m.rh:.1f}" if m.rh else "-",
                ]
                data.append(row)

            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(table)
        else:
            story.append(Paragraph("No hay datos para el período seleccionado", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_excel(
        self,
        device_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        variables: List[str],
        channels: Optional[List[str]] = None,
    ) -> BytesIO:
        """
        Genera reporte Excel con TODOS los datos minuto a minuto.
        
        Returns:
            Buffer con el Excel generado
        """
        measurements = self._get_measurements(device_ids, start_date, end_date, channels)

        # Convertir a DataFrame
        data = []
        for m in measurements:
            data.append(
                {
                    "Fecha/Hora": m.fechah_local.strftime("%Y-%m-%d %H:%M:%S"),
                    "Dispositivo": label_for(m.device_id),
                    "Device ID": m.device_id,
                    "Canal": m.sensor_channel.value,
                    "PM2.5": m.pm25,
                    "PM10": m.pm10,
                    "Temperatura": m.temp,
                    "Humedad": m.rh,
                }
            )

        df = pd.DataFrame(data)

        # Crear workbook
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Mediciones", index=False)

            # Formatear
            workbook = writer.book
            worksheet = writer.sheets["Mediciones"]

            # Estilo de encabezados
            header_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Ajustar anchos de columna
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)

        buffer.seek(0)
        return buffer

    def preview_data(
        self,
        device_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        limit: int = 10,
    ) -> dict:
        """Preview de datos para validación."""
        measurements = self._get_measurements(device_ids, start_date, end_date)

        total = len(measurements)
        preview = measurements[:limit]

        return {
            "total_records": total,
            "preview_count": len(preview),
            "sample_data": [
                {
                    "fechah_local": m.fechah_local.isoformat(),
                    "device_id": m.device_id,
                    "device_label": label_for(m.device_id),
                    "sensor_channel": m.sensor_channel.value,
                    "pm25": m.pm25,
                    "pm10": m.pm10,
                    "temp": m.temp,
                    "rh": m.rh,
                }
                for m in preview
            ],
        }
