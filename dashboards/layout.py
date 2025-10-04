from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dash import html, dcc
from labels import label_for  # mapeo de nombres visibles

BOGOTA = ZoneInfo("America/Bogota")


def build_layout(app):
    # IDs reales (los que usa la API)
    devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
    today_dt = datetime.now(BOGOTA)
    today = today_dt.strftime("%Y-%m-%d")
    start_default = (today_dt - timedelta(days=3)).strftime("%Y-%m-%d")  # rango por defecto 4 días

    return html.Div(
        className="page",
        children=[
            html.Link(rel="stylesheet", href="/static/styles.css"),

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

            # ---------- CONTROLES ----------
            html.Section(
                className="controls",
                children=[
                    html.Div(
                        className="control-row",
                        children=[
                            html.Div(
                                className="control full",
                                children=[
                                    html.Label("Equipos"),
                                    dcc.Dropdown(
                                        id="ddl-devices",
                                        # label = nombre amigable, value = id REAL
                                        options=[{"label": label_for(d), "value": d} for d in devices],
                                        value=devices,
                                        multi=True,
                                        clearable=False,
                                        placeholder="Selecciona uno o más equipos…",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="control-row",
                        children=[
                            html.Div(
                                className="control",
                                children=[
                                    html.Label("Canal"),
                                    dcc.RadioItems(
                                        id="rdo-channel",
                                        # OJO: valores siguen siendo Um1 / Um2 (no se toca la lógica)
                                        options=[
                                            {"label": "Sensor 1", "value": "Um1"},
                                            {"label": "Sensor 2", "value": "Um2"},
                                            {"label": "Ambos",    "value": "ambos"},
                                        ],
                                        value="ambos",
                                        inline=True,
                                        className="radio-group",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="control",
                                children=[
                                    html.Label("Particulado"),
                                    dcc.RadioItems(
                                        id="rdo-pm",
                                        options=[
                                            {"label": "PM2.5", "value": "pm25"},
                                            {"label": "PM10", "value": "pm10"},
                                            {"label": "Ambas", "value": "ambas"},
                                        ],
                                        value="ambas",
                                        inline=True,
                                        className="radio-group",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="control",
                                children=[
                                    html.Label("Fecha"),
                                    # Rango de fechas
                                    dcc.DatePickerRange(
                                        id="dp-range",
                                        start_date=start_default,
                                        end_date=today,
                                        display_format="YYYY-MM-DD",
                                        minimum_nights=0,
                                        updatemode="bothdates",
                                        className="date",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="control right",
                                children=[
                                    html.Button("Limpiar Filtros", id="btn-clear", n_clicks=0, className="btn ghost"),
                                    # Nuevo botón con el MISMO estilo que “Limpiar Filtros”
                                    html.Button("Aplicar Filtros", id="btn-apply", n_clicks=0, className="btn ghost"),
                                    html.Button("Actualizar ahora", id="btn-refresh", n_clicks=0, className="btn primary"),
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
