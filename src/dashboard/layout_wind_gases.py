"""
Layout para dashboard de Viento y Gases (NO2, CO2).
Incluye rosa de vientos y series temporales.
"""
from datetime import datetime, timedelta
from dash import html, dcc
from sqlalchemy import func
from src.utils.labels import label_for
from src.utils.constants import BOGOTA
from src.core.database import db
from src.core.models import Measurement
from src.dashboard.navigation import create_navigation_sidebar, create_breadcrumbs, create_sidebar_toggle_button


def get_available_date_range():
    """Obtiene el rango de fechas disponibles en la BD."""
    try:
        result = db.session.query(
            func.min(Measurement.fecha).label('min_date'),
            func.max(Measurement.fecha).label('max_date')
        ).first()
        
        if result and result.min_date and result.max_date:
            return result.min_date, result.max_date
    except Exception as e:
        print(f"Error obteniendo rango de fechas: {e}")
    
    today = datetime.now(BOGOTA).date()
    return today - timedelta(days=30), today


def build_wind_gases_layout(app):
    """
    Construye el layout del dashboard de Viento y Gases.
    """
    devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
    
    today_dt = datetime.now(BOGOTA)
    today = today_dt.strftime("%Y-%m-%d")
    # Cambiar a 24 horas por defecto (1 día completo)
    start_default = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    with app.app_context():
        min_date_available, max_date_available = get_available_date_range()
    
    min_date_str = min_date_available.strftime("%Y-%m-%d")
    max_date_str = max_date_available.strftime("%Y-%m-%d")
    
    if start_default < min_date_str:
        start_default = min_date_str
    if today > max_date_str:
        today = max_date_str

    return html.Div(
        className="page",
        children=[
            # ---------- NAVEGACIÓN LATERAL ----------
            create_navigation_sidebar(current_page="viento-gases"),
            
            # ---------- BREADCRUMBS ----------
            create_breadcrumbs([
                ("🏠 Inicio", "/dash/"),
                "Viento y Gases"
            ]),
            
            # ---------- TOPBAR (IDÉNTICO EN AMBOS DASHBOARDS) ----------
            html.Header(
                className="topbar",
                children=[
                    # Botón de menú integrado
                    create_sidebar_toggle_button(),
                    
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
                            html.Div(id="txt-last-update-wind", className="last-update"),
                            html.Small(
                                "Datos indicativos, Sistema de Vigilancia Calidad de Aire Sensores Bajo Costo",
                                className="disclaimer",
                            ),
                        ],
                    ),
                ],
            ),

            # ---------- CONTROLES (IDÉNTICO EN AMBOS DASHBOARDS) ----------
            html.Section(
                className="controls",
                children=[
                    # FILA 1: Equipos a Monitorear
                    html.Div(
                        className="equipment-row",
                        children=[
                            html.Label("📍 EQUIPOS A MONITOREAR", className="filter-label-inline"),
                            dcc.Dropdown(
                                id="ddl-devices-wind",
                                options=[{"label": label_for(d), "value": d} for d in devices],
                                value=devices,
                                multi=True,
                                clearable=False,
                                placeholder="Selecciona uno o varios equipos...",
                                className="dropdown-modern",
                            ),
                        ],
                    ),
                    
                    # FILA 2: Filtros unificados (sin sensores - no aplica para viento y gases)
                    html.Div(
                        className="filters-unified-row",
                        children=[
                            # Variables (NO2, CO2, Velocidad)
                            html.Div(
                                className="filter-inline",
                                children=[
                                    html.Label("📊 VARIABLES", className="filter-label-small"),
                                    dcc.Checklist(
                                        id="chk-variables-wind",
                                        options=[
                                            {"label": " NO2", "value": "no2"},
                                            {"label": " CO2", "value": "co2"},
                                            {"label": " Velocidad Viento", "value": "vel_viento"},
                                        ],
                                        value=["no2", "co2", "vel_viento"],
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
                                    html.Label("📅 PERIODO DE ANÁLISIS", className="filter-label-small"),
                                    dcc.DatePickerRange(
                                        id="date-picker-wind",
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
                                        first_day_of_week=1,
                                    ),
                                ],
                            ),
                            
                            # Botones de acción (sin label, solo botones en línea)
                            html.Div(
                                className="action-buttons-inline",
                                children=[
                                    html.Button(
                                        [html.Span("🔄", className="btn-emoji"), " Actualizar"], 
                                        id="btn-refresh-wind", 
                                        n_clicks=0, 
                                        className="btn-action btn-refresh",
                                        title="Actualizar datos ahora"
                                    ),
                                    html.Button(
                                        [html.Span("✓", className="btn-emoji"), " Aplicar Filtros"], 
                                        id="btn-apply-wind", 
                                        n_clicks=0, 
                                        className="btn-action btn-apply"
                                    ),
                                    html.Button(
                                        [html.Span("↺", className="btn-emoji"), " Restablecer"], 
                                        id="btn-reset-wind", 
                                        n_clicks=0, 
                                        className="btn-action btn-reset"
                                    ),
                                ],
                            ),
                        ],
                    ),
                    
                    # FILA 3: Descargar Reportes Excel
                    html.Hr(className="divider"),
                    
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

            # ---------- SECCIÓN DE GRÁFICOS ----------
            html.Section(
                className="content",
                children=[
                    # Primera Fila: Rosa de Vientos + Velocidad del Viento
                    html.Div(
                        className="graphs-row-compact",
                        children=[
                            html.Div(
                                className="plot-card",
                                children=[
                                    html.H3("🌹 Rosa de Vientos", className="card-title"),
                                    dcc.Loading(
                                        id="loading-windrose",
                                        type="circle",
                                        children=dcc.Graph(
                                            id="graph-windrose",
                                            config={"displayModeBar": True, "displaylogo": False},
                                            className="graph-compact",
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(
                                className="plot-card",
                                children=[
                                    html.H3("💨 Velocidad del Viento", className="card-title"),
                                    dcc.Loading(
                                        id="loading-wind-speed",
                                        type="circle",
                                        children=dcc.Graph(
                                            id="graph-wind-speed",
                                            config={"displayModeBar": True, "displaylogo": False},
                                            className="graph-compact",
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    
                    # Segunda Fila: NO2 + CO2
                    html.Div(
                        className="graphs-row-compact",
                        children=[
                            html.Div(
                                className="plot-card",
                                children=[
                                    html.H3("🏭 Dióxido de Nitrógeno (NO2)", className="card-title"),
                                    dcc.Loading(
                                        id="loading-no2",
                                        type="circle",
                                        children=dcc.Graph(
                                            id="graph-no2",
                                            config={"displayModeBar": True, "displaylogo": False},
                                            className="graph-compact",
                                        ),
                                    ),
                                ],
                            ),
                            html.Div(
                                className="plot-card",
                                children=[
                                    html.H3("🌫️ Dióxido de Carbono (CO2)", className="card-title"),
                                    dcc.Loading(
                                        id="loading-co2",
                                        type="circle",
                                        children=dcc.Graph(
                                            id="graph-co2",
                                            config={"displayModeBar": True, "displaylogo": False},
                                            className="graph-compact",
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),

            # ---------- FOOTER ----------
            html.Footer(
                className="footer",
                children=[
                    html.P(
                        "© 2025 Sistema de Monitoreo de Calidad del Aire | Desarrollado con Dash & Plotly",
                        className="footer-text",
                    ),
                ],
            ),

            # Interval para actualización automática (cada 5 minutos)
            dcc.Interval(
                id="interval-auto-refresh-wind",
                interval=5*60*1000,  # 5 minutos
                n_intervals=0,
            ),
        ],
    )
