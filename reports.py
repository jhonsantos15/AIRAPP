"""
Módulo para generar reportes en PDF de las mediciones de calidad del aire.
"""
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from io import BytesIO
from typing import List, Optional
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from sqlalchemy import func
from db import db
from models import Measurement, SensorChannel
from labels import label_for

BOGOTA = ZoneInfo("America/Bogota")

logger = logging.getLogger(__name__)


def _bounds_of_day_local(d: date):
    """Retorna los límites de un día en zona local."""
    start_local = datetime.combine(d, time(0, 0, 0)).replace(tzinfo=BOGOTA)
    end_local = datetime.combine(d, time(23, 59, 59)).replace(tzinfo=BOGOTA)
    return start_local, end_local


def _bounds_of_range_local(dstart: date, dend: date):
    """Retorna los límites de un rango de fechas en zona local."""
    a, _ = _bounds_of_day_local(dstart)
    _, b = _bounds_of_day_local(dend)
    return a, b


def _get_measurements(
    start_dt: datetime,
    end_dt: datetime,
    devices: Optional[List[str]] = None,
    channels: Optional[List[SensorChannel]] = None
):
    """Obtiene mediciones filtradas por rango de fechas, dispositivos y canales."""
    if channels is None:
        channels = [SensorChannel.Um1, SensorChannel.Um2]
    
    qry = Measurement.query.filter(
        Measurement.fechah_local >= start_dt,
        Measurement.fechah_local <= end_dt,
        Measurement.sensor_channel.in_(channels),
    )
    
    if devices:
        qry = qry.filter(Measurement.device_id.in_(devices))
    
    return qry.order_by(Measurement.fechah_local.desc()).all()


def _calculate_statistics(measurements: List[Measurement]):
    """Calcula estadísticas de las mediciones."""
    if not measurements:
        return {}
    
    stats = {
        'total_records': len(measurements),
        'devices': {},
        'pm25': {'min': None, 'max': None, 'avg': None},
        'pm10': {'min': None, 'max': None, 'avg': None},
        'temp': {'min': None, 'max': None, 'avg': None},
        'rh': {'min': None, 'max': None, 'avg': None},
    }
    
    # Agrupar por dispositivos
    for m in measurements:
        dev = m.device_id
        if dev not in stats['devices']:
            stats['devices'][dev] = 0
        stats['devices'][dev] += 1
    
    # Calcular estadísticas por variable
    for var in ['pm25', 'pm10', 'temp', 'rh']:
        values = [getattr(m, var) for m in measurements if getattr(m, var) is not None]
        if values:
            stats[var]['min'] = round(min(values), 2)
            stats[var]['max'] = round(max(values), 2)
            stats[var]['avg'] = round(sum(values) / len(values), 2)
    
    return stats


def _add_header(canvas_obj, doc):
    """Agrega encabezado a cada página."""
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica-Bold', 14)
    canvas_obj.drawString(inch, doc.height + 1.5 * inch, "Reporte de Calidad del Aire")
    canvas_obj.setFont('Helvetica', 10)
    canvas_obj.drawString(inch, doc.height + 1.3 * inch, f"Generado: {datetime.now(BOGOTA).strftime('%Y-%m-%d %H:%M:%S')}")
    canvas_obj.line(inch, doc.height + 1.2 * inch, doc.width + inch, doc.height + 1.2 * inch)
    canvas_obj.restoreState()


def _add_footer(canvas_obj, doc):
    """Agrega pie de página a cada página."""
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 8)
    canvas_obj.drawString(inch, 0.5 * inch, "Sistema de Vigilancia Calidad de Aire - Sensores Bajo Costo")
    canvas_obj.drawRightString(doc.width + inch, 0.5 * inch, f"Página {doc.page}")
    canvas_obj.restoreState()


def generate_pdf_report(
    period: str,
    devices: Optional[List[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    channels: Optional[List[SensorChannel]] = None
) -> BytesIO:
    """
    Genera un reporte PDF para el período especificado.
    
    Args:
        period: Tipo de período ('hour', '24hours', '7days', 'year', 'custom')
        devices: Lista de device_ids a incluir (None = todos)
        start_date: Fecha de inicio (para custom)
        end_date: Fecha de fin (para custom)
        channels: Canales a incluir (None = ambos)
    
    Returns:
        BytesIO con el contenido del PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=2*inch, bottomMargin=inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12,
    )
    
    # Calcular rango de fechas según el período
    now = datetime.now(BOGOTA)
    today = now.date()
    
    if period == 'hour':
        # Última hora
        start_dt = now - timedelta(hours=1)
        end_dt = now
        title = "Reporte Última Hora"
    elif period == '24hours':
        # Últimas 24 horas
        start_dt = now - timedelta(hours=24)
        end_dt = now
        title = "Reporte Últimas 24 Horas"
    elif period == '7days':
        # Últimos 7 días
        start_dt, _ = _bounds_of_day_local(today - timedelta(days=6))
        _, end_dt = _bounds_of_day_local(today)
        title = "Reporte Últimos 7 Días"
    elif period == 'year':
        # Año actual
        start_dt, _ = _bounds_of_day_local(date(today.year, 1, 1))
        _, end_dt = _bounds_of_day_local(today)
        title = f"Reporte Año {today.year}"
    elif period == 'custom' and start_date and end_date:
        start_dt, _ = _bounds_of_day_local(start_date)
        _, end_dt = _bounds_of_day_local(end_date)
        title = f"Reporte Personalizado"
    else:
        raise ValueError(f"Período no válido: {period}")
    
    # Obtener mediciones
    measurements = _get_measurements(start_dt, end_dt, devices, channels)
    stats = _calculate_statistics(measurements)
    
    # Construir contenido del PDF
    story = []
    
    # Título
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Información del período
    period_info = f"""
    <b>Período:</b> {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%Y-%m-%d %H:%M')}<br/>
    <b>Total de registros:</b> {stats.get('total_records', 0)}<br/>
    """
    if devices:
        device_names = ', '.join([label_for(d) for d in devices])
        period_info += f"<b>Dispositivos:</b> {device_names}<br/>"
    else:
        period_info += "<b>Dispositivos:</b> Todos<br/>"
    
    story.append(Paragraph(period_info, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Estadísticas generales
    story.append(Paragraph("Estadísticas Generales", heading_style))
    
    if stats.get('total_records', 0) > 0:
        stats_data = [
            ['Variable', 'Mínimo', 'Máximo', 'Promedio', 'Unidad'],
            ['PM2.5', 
             str(stats['pm25'].get('min', 'N/A')),
             str(stats['pm25'].get('max', 'N/A')),
             str(stats['pm25'].get('avg', 'N/A')),
             'µg/m³'],
            ['PM10',
             str(stats['pm10'].get('min', 'N/A')),
             str(stats['pm10'].get('max', 'N/A')),
             str(stats['pm10'].get('avg', 'N/A')),
             'µg/m³'],
            ['Temperatura',
             str(stats['temp'].get('min', 'N/A')),
             str(stats['temp'].get('max', 'N/A')),
             str(stats['temp'].get('avg', 'N/A')),
             '°C'],
            ['Humedad Relativa',
             str(stats['rh'].get('min', 'N/A')),
             str(stats['rh'].get('max', 'N/A')),
             str(stats['rh'].get('avg', 'N/A')),
             '%'],
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, inch, inch, inch, inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Distribución por dispositivos
        if stats.get('devices'):
            story.append(Paragraph("Distribución por Dispositivos", heading_style))
            
            device_data = [['Dispositivo', 'Registros']]
            for dev, count in sorted(stats['devices'].items()):
                device_data.append([label_for(dev), str(count)])
            
            device_table = Table(device_data, colWidths=[3*inch, 2*inch])
            device_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            story.append(device_table)
            story.append(Spacer(1, 0.3 * inch))
        
        # Muestra de datos recientes (últimos 20 registros)
        story.append(PageBreak())
        story.append(Paragraph("Muestra de Datos Recientes (Últimos 20 registros)", heading_style))
        
        sample_data = [['Fecha/Hora', 'Dispositivo', 'Canal', 'PM2.5', 'PM10', 'Temp', 'HR']]
        for m in measurements[:20]:
            sample_data.append([
                m.fechah_local.strftime('%Y-%m-%d %H:%M'),
                label_for(m.device_id),
                m.sensor_channel.name,
                str(round(m.pm25, 1)) if m.pm25 is not None else 'N/A',
                str(round(m.pm10, 1)) if m.pm10 is not None else 'N/A',
                str(round(m.temp, 1)) if m.temp is not None else 'N/A',
                str(round(m.rh, 1)) if m.rh is not None else 'N/A',
            ])
        
        sample_table = Table(sample_data, colWidths=[1.3*inch, 1.2*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch])
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(sample_table)
    else:
        story.append(Paragraph("No se encontraron datos para el período seleccionado.", styles['Normal']))
    
    # Pie de página con información adicional
    story.append(Spacer(1, 0.5 * inch))
    footer_text = """
    <b>Nota:</b> Los datos presentados son indicativos y provienen de sensores de bajo costo.
    Sistema de Vigilancia de Calidad del Aire.
    """
    story.append(Paragraph(footer_text, styles['Italic']))
    
    # Construir PDF
    doc.build(story, onFirstPage=_add_header, onLaterPages=_add_header)
    
    buffer.seek(0)
    logger.info(f"Reporte PDF generado: {period}, {len(measurements)} registros")
    return buffer
