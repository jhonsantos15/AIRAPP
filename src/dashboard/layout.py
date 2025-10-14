from datetime import datetime, timedelta, date
from dash import html, dcc
from sqlalchemy import func
from src.utils.labels import label_for
from src.utils.constants import BOGOTA
from src.core.database import db
from src.core.models import Measurement


def get_available_date_range():
    """
    Obtiene el rango de fechas disponibles en la base de datos.
    Retorna (min_date, max_date) como objetos date de Python.
    Si no hay datos, retorna fechas por defecto.
    """
    try:
        # Consultar fecha mínima y máxima con datos
        result = db.session.query(
            func.min(Measurement.fecha).label('min_date'),
            func.max(Measurement.fecha).label('max_date')
        ).first()
        
        if result and result.min_date and result.max_date:
            return result.min_date, result.max_date
    except Exception as e:
        print(f"Error obteniendo rango de fechas: {e}")
    
    # Fallback: retornar rango por defecto (últimos 30 días)
    today = datetime.now(BOGOTA).date()
    return today - timedelta(days=30), today


def build_layout(app):
    """
    Construye el layout del dashboard.
    SIEMPRE muestra todos los equipos S1-S6, incluso si no tienen datos actualmente
    (pueden estar en mantenimiento o pendientes de instalación).
    """
    # IDs de TODOS los equipos configurados (S1 a S6)
    # No filtramos por disponibilidad de datos - mostramos todos los equipos del sistema
    devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
    
    today_dt = datetime.now(BOGOTA)
    today = today_dt.strftime("%Y-%m-%d")
    start_default = (today_dt - timedelta(days=3)).strftime("%Y-%m-%d")  # rango por defecto 4 días

    # Obtener rango de fechas disponibles en la BD
    with app.app_context():
        min_date_available, max_date_available = get_available_date_range()
    
    # Convertir a strings para el DatePickerRange
    min_date_str = min_date_available.strftime("%Y-%m-%d")
    max_date_str = max_date_available.strftime("%Y-%m-%d")
    
    # Asegurar que start_default esté dentro del rango disponible
    if start_default < min_date_str:
        start_default = min_date_str
    
    # Asegurar que today esté dentro del rango disponible
    if today > max_date_str:
        today = max_date_str

    return html.Div(
        className="page",
        children=[
            # ---------- TOPBAR ----------
            html.Header(
                className="topbar",
                children=[
                    html.Div(
                        className="brand",
                        children=[
                            html.Span("Monitoreo de Calidad del Aire", className="logo"),
                            html.Span("(Datos en tiempo real)", className="subtitle"),
                        ],
                    ),
                    html.Div(
                        className="status",
                        children=[
                            html.Div(id="txt-last-update", className="last-update"),
                            html.Small(
                                "Datos indicativos, Sistema de Vigilancia Calidad de Aire Sensores Bajo Costo",
                                className="disclaimer",
                            ),
                        ],
                    ),
                ],
            ),

            # ---------- CONTROLES OPTIMIZADOS ----------
            html.Section(
                className="controls",
                children=[
                    # FILA 1: Equipos a Monitorear
                    html.Div(
                        className="equipment-row",
                        children=[
                            html.Label("📍 Equipos a Monitorear", className="filter-label-inline"),
                            dcc.Dropdown(
                                id="ddl-devices",
                                options=[{"label": label_for(d), "value": d} for d in devices],
                                value=devices,
                                multi=True,
                                clearable=False,
                                placeholder="Selecciona uno o varios equipos...",
                                className="dropdown-modern",
                            ),
                        ],
                    ),
                    
                    # FILA 2: Todos los filtros en una sola fila horizontal
                    html.Div(
                        className="filters-unified-row",
                        children=[
                            # Sensores
                            html.Div(
                                className="filter-inline",
                                children=[
                                    html.Label("🔌 Sensores", className="filter-label-small"),
                                    dcc.Checklist(
                                        id="rdo-channel",
                                        options=[
                                            {"label": " Sensor 1", "value": "Um1"},
                                            {"label": " Sensor 2", "value": "Um2"},
                                        ],
                                        value=["Um1", "Um2"],
                                        inline=True,
                                        className="checkbox-modern",
                                        labelStyle={"display": "inline-flex", "alignItems": "center"},
                                    ),
                                ],
                            ),
                            # Material Particulado
                            html.Div(
                                className="filter-inline",
                                children=[
                                    html.Label("💨 Material Particulado", className="filter-label-small"),
                                    dcc.Checklist(
                                        id="rdo-pm",
                                        options=[
                                            {"label": " PM2.5", "value": "pm25"},
                                            {"label": " PM10", "value": "pm10"},
                                        ],
                                        value=["pm25", "pm10"],
                                        inline=True,
                                        className="checkbox-modern",
                                        labelStyle={"display": "inline-flex", "alignItems": "center"},
                                    ),
                                ],
                            ),
                            # Período de Análisis
                            html.Div(
                                className="filter-inline",
                                children=[
                                    html.Label("📅 Período de Análisis", className="filter-label-small"),
                                    dcc.DatePickerRange(
                                        id="dp-range",
                                        start_date=start_default,
                                        end_date=today,
                                        min_date_allowed=min_date_str,
                                        max_date_allowed=max_date_str,
                                        display_format="DD/MM/YYYY",
                                        minimum_nights=0,
                                        updatemode="singledate",
                                        className="date-modern",
                                        start_date_placeholder_text="Inicio",
                                        end_date_placeholder_text="Fin",
                                        clearable=False,
                                    ),
                                ],
                            ),
                            # Botones de acción (sin label, solo botones en línea)
                            html.Div(
                                className="action-buttons-inline",
                                children=[
                                    html.Button(
                                        [html.Span("🔄", className="btn-emoji"), " Actualizar"], 
                                        id="btn-refresh", 
                                        n_clicks=0, 
                                        className="btn-action btn-refresh",
                                        title="Actualizar datos ahora"
                                    ),
                                    html.Button(
                                        [html.Span("✓", className="btn-emoji"), " Aplicar Filtros"], 
                                        id="btn-apply", 
                                        n_clicks=0, 
                                        className="btn-action btn-apply"
                                    ),
                                    html.Button(
                                        [html.Span("↺", className="btn-emoji"), " Restablecer"], 
                                        id="btn-clear", 
                                        n_clicks=0, 
                                        className="btn-action btn-clear"
                                    ),
                                ],
                            ),
                        ],
                    ),
                    
                    # Separador visual
                    html.Hr(className="divider"),
                    
                    # ---------- SECCIÓN DE REPORTES EXCEL ----------
                    html.Div(
                        className="reports-section",
                        children=[
                            html.Label("📊 Descargar Reportes Excel", className="filter-label-small"),
                            html.Div(
                                className="report-buttons-modern",
                                children=[
                                    html.A(
                                        "Última Hora",
                                        href="/api/reports/excel?period=hour",
                                        target="_blank",
                                        className="btn-report"
                                    ),
                                    html.A(
                                        "Últimas 12 Horas",
                                        href="/api/reports/excel?period=12hours",
                                        target="_blank",
                                        className="btn-report"
                                    ),
                                    html.A(
                                        "Últimas 24 Horas",
                                        href="/api/reports/excel?period=24hours",
                                        target="_blank",
                                        className="btn-report"
                                    ),
                                    html.A(
                                        "Últimos 7 Días",
                                        href="/api/reports/excel?period=7days",
                                        target="_blank",
                                        className="btn-report"
                                    ),
                                    html.A(
                                        "Mes Actual",
                                        href="/api/reports/excel?period=month",
                                        target="_blank",
                                        className="btn-report"
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            # ---------- REJILLA DE GRÁFICOS ----------
            html.Section(
                className="charts-grid",
                children=[
                    html.Div(
                        className="plot-card col-span-12",
                        children=dcc.Loading(
                            type="dot", color="#11B6C7",
                            children=dcc.Graph(
                                id="graph-pm",
                                style={"height": "var(--h-pm)"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ),
                    ),
                    html.Div(
                        className="plot-card col-span-6",
                        children=dcc.Loading(
                            type="dot", color="#11B6C7",
                            children=dcc.Graph(
                                id="graph-rh",
                                style={"height": "var(--h-small)"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ),
                    ),
                    html.Div(
                        className="plot-card col-span-6",
                        children=dcc.Loading(
                            type="dot", color="#11B6C7",
                            children=dcc.Graph(
                                id="graph-temp",
                                style={"height": "var(--h-small)"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ),
                    ),
                ],
            ),

            dcc.Interval(id="intv", interval=60_000, n_intervals=0),
        ],
    )
