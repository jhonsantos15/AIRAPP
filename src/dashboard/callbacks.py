# src/dashboard/callbacks.py
from datetime import datetime, timedelta
import pandas as pd
from dash import Input, Output, State, no_update
import plotly.graph_objects as go

from src.utils.labels import label_for
from src.utils.constants import BOGOTA, COLORWAY, DASH_BY_UM, DEVICE_COLORS, PM_COLORS
from src.core.database import db
from src.core.models import Measurement, SensorChannel

def color_for_device(device_id: str) -> str:
    """
    Retorna el color FIJO asignado a cada equipo.
    Cada dispositivo tiene un color único y consistente.
    """
    device_str = str(device_id)
    # Buscar en mapeo fijo
    if device_str in DEVICE_COLORS:
        return DEVICE_COLORS[device_str]
    # Fallback para dispositivos no mapeados
    idx = abs(hash(device_str)) % len(COLORWAY)
    return COLORWAY[idx]

def fixed_bounds(start_date: str, end_date: str):
    if not start_date:
        start_date = end_date
    if not end_date:
        end_date = start_date
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    x0 = datetime(s.year, s.month, s.day, 0, 0, 0, tzinfo=BOGOTA)
    x1 = datetime(e.year, e.month, e.day, 23, 59, 59, tzinfo=BOGOTA)
    return x0, x1

def um_label(um_value: str) -> str:
    s = str(um_value).lower()
    return "Sensor 1" if s == "um1" else ("Sensor 2" if s == "um2" else um_value)

UNIFIED_MAX_TRACES = 10
def pick_hovermode(trace_count: int) -> str:
    return "x unified" if trace_count <= UNIFIED_MAX_TRACES else "x"

COMMON_LAYOUT = dict(
    template="plotly_white",
    colorway=COLORWAY,
    transition=dict(duration=0),
    margin=dict(l=50, r=16, t=48, b=40),
    legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, xanchor="left", traceorder="normal"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(font=dict(size=11), namelength=28, align="left",
                    bgcolor="rgba(255,255,255,0.98)", bordercolor="#11B6C7"),
)

def apply_layout(fig: go.Figure, uirev: str):
    fig.update_layout(**COMMON_LAYOUT)
    fig.layout.uirevision = uirev

# ---------------- helpers ---------------- #

def _parse_channels(code):
    """
    Convierte el input de canales (ahora una lista de checkboxes) en lista de SensorChannel.
    Si code es None o lista vacía, retorna ambos canales.
    """
    if not code:
        return [SensorChannel.Um1, SensorChannel.Um2]
    
    # Si es una lista (del Checklist)
    if isinstance(code, list):
        result = []
        for c in code:
            if str(c).lower() in ("um1", "sensor1", "s1"):
                result.append(SensorChannel.Um1)
            elif str(c).lower() in ("um2", "sensor2", "s2"):
                result.append(SensorChannel.Um2)
        return result if result else [SensorChannel.Um1, SensorChannel.Um2]
    
    # Si es string único (legacy)
    q = str(code).strip().lower()
    if q in ("um1", "sensor1", "s1"):
        return [SensorChannel.Um1]
    if q in ("um2", "sensor2", "s2"):
        return [SensorChannel.Um2]
    return [SensorChannel.Um1, SensorChannel.Um2]

def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()

def _hover_fmt(start_date: str, end_date: str) -> str:
    """Formato de hora en hover según el rango."""
    return "%H:%M" if start_date == end_date else "%m-%d %H:%M"

def _xaxis_format(start_date: str, end_date: str) -> dict:
    """
    Retorna configuración del eje X adaptativa según el rango de fechas.
    
    Reglas optimizadas para legibilidad:
    - 1 día: formato hora cada 2 horas (%H:%M)
    - 2-7 días: formato mes-día y hora (%m-%d %H:%M)
    - Más de 7 días: solo fecha (%Y-%m-%d)
    """
    if not start_date or not end_date:
        return {}
    
    try:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        days = (e - s).days
        
        if days == 0:
            return {"tickformat": "%H:%M", "dtick": 7200000}  # 2 horas
        elif days <= 3:
            return {"tickformat": "%m-%d %H:%M", "dtick": 14400000}  # 4 horas
        elif days <= 7:
            return {"tickformat": "%m-%d", "dtick": 86400000}  # 1 día
        else:
            return {"tickformat": "%Y-%m-%d", "dtick": 86400000 * 2}  # 2 días
    except Exception:
        return {}


def _insert_gaps_for_plotly(timestamps, values, gap_threshold_minutes=15):
    """
    Inserta valores None en los arrays cuando hay gaps temporales significativos.
    
    Esto fuerza a Plotly a NO dibujar líneas entre puntos con gaps de tiempo.
    
    Args:
        timestamps: Serie de pandas con timestamps
        values: Serie de pandas con valores
        gap_threshold_minutes: Umbral en minutos para considerar un gap
        
    Returns:
        Tuple (x_vals, y_vals) con None insertados en los gaps
    """
    if len(timestamps) == 0:
        return [], []
    
    x_vals = []
    y_vals = []
    gap_threshold = timedelta(minutes=gap_threshold_minutes)
    
    prev_ts = None
    for ts, val in zip(timestamps, values):
        if prev_ts is not None:
            # Calcular diferencia temporal
            time_diff = ts - prev_ts
            
            # Si hay un gap significativo, insertar None
            if time_diff > gap_threshold:
                x_vals.append(None)
                y_vals.append(None)
        
        x_vals.append(ts)
        y_vals.append(val)
        prev_ts = ts
    
    return x_vals, y_vals


def _xaxis_format(start_date: str, end_date: str) -> dict:
    """
    Retorna configuración del eje X adaptativa según el rango de fechas.
    
    Reglas optimizadas para legibilidad:
    - 1 día: formato hora cada 2 horas (%H:%M)
    - 2-3 días: formato día-mes hora cada 6 horas (%d %b %H:%M)
    - 4-7 días: formato día-mes hora cada 12 horas (%d %b %H:%M)
    - 8-31 días: formato día-mes cada 1 día (%d %b)
    - >31 días: formato mes-año auto (%b %Y)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_diff = (end - start).days
    except:
        days_diff = 0
    
    if days_diff == 0:
        # 1 día: mostrar horas cada 2 horas (más legible)
        return {
            "tickformat": "%H:%M",
            "dtick": 7200000,  # 2 horas en milisegundos
            "tickmode": "linear",
            "nticks": 12  # Máximo 12 etiquetas
        }
    elif days_diff <= 3:
        # 2-3 días: día-mes con hora cada 6 horas
        return {
            "tickformat": "%d %b<br>%H:%M",
            "dtick": 21600000,  # 6 horas
            "tickmode": "linear",
            "nticks": 12
        }
    elif days_diff <= 7:
        # 4-7 días: día-mes con hora cada 12 horas
        return {
            "tickformat": "%d %b<br>%H:%M",
            "dtick": 43200000,  # 12 horas
            "tickmode": "linear",
            "nticks": 14
        }
    elif days_diff <= 31:
        # 8-31 días: solo fechas cada día
        return {
            "tickformat": "%d %b",
            "dtick": 86400000,  # 1 día
            "tickmode": "linear",
            "nticks": 15
        }
    else:
        # >31 días: mes-año (auto ajusta)
        return {
            "tickformat": "%b %Y",
            "tickmode": "auto",
            "nticks": 12
        }


def _fetch_points_for_range(flask_app, channel_value: str, variables: list[str],
                            start_date: str, end_date: str, sel_devices: list[str] | None):
    """
    Lee datos de la BD aplicando filtros directamente en SQL.
    Más simple y permisivo - respeta exactamente lo que el usuario selecciona.
    """
    channels = _parse_channels(channel_value)
    variables = variables or ["pm25", "pm10", "temp", "rh"]
    
    flask_app.logger.info(f"[dash] Consultando datos con canales: {[ch.name for ch in channels]}")

    start_local, end_local = fixed_bounds(start_date, end_date)
    
    # Limpiar lista de dispositivos
    sel_devices = [str(d).strip() for d in (sel_devices or []) if d]

    with flask_app.app_context():
        # Consulta SQL con filtros directos
        qry = (
            db.session.query(Measurement)
            .filter(
                Measurement.fechah_local >= start_local,
                Measurement.fechah_local <= end_local,
                Measurement.sensor_channel.in_(channels),
            )
        )
        
        # Filtrar por dispositivos si hay selección
        if sel_devices:
            qry = qry.filter(Measurement.device_id.in_(sel_devices))
            flask_app.logger.info(f"[dash] Filtro SQL por dispositivos: {sel_devices}")
        else:
            flask_app.logger.info(f"[dash] Sin filtro de dispositivos - buscando todos")
        
        # Ejecutar consulta ordenada
        qry = qry.order_by(Measurement.fechah_local.asc())
        rows = qry.all()
        
        # LOG de resultados
        devices_found = sorted(list(set([r.device_id for r in rows])))
        flask_app.logger.info(
            f"[dash] SQL retornó {len(rows)} filas. "
            f"Dispositivos encontrados: {devices_found}"
        )

    if not rows:
        flask_app.logger.warning(
            f"[dash] ⚠ Sin datos para: dispositivos={sel_devices}, "
            f"fechas={start_date}→{end_date}, canales={[ch.name for ch in channels]}"
        )
        return []

    # Convertir a DataFrame
    recs = []
    for r in rows:
        recs.append({
            "ts": r.fechah_local,
            "device_id": r.device_id,
            "Um": r.sensor_channel.name,
            "pm25": getattr(r, "pm25", None),
            "pm10": getattr(r, "pm10", None),
            "temp": getattr(r, "temp", None),
            "rh": getattr(r, "rh", None),
        })
    
    df = pd.DataFrame(recs)
    
    # Normalizar timestamps
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    try:
        if df["ts"].dt.tz is None:
            df["ts"] = df["ts"].dt.tz_localize(BOGOTA)
        else:
            df["ts"] = df["ts"].dt.tz_convert(BOGOTA)
    except Exception as e:
        flask_app.logger.error(f"[dash] Error normalizando timestamps: {e}")
        df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(BOGOTA)

    if df.empty:
        flask_app.logger.warning("[dash] DataFrame vacío después de procesar timestamps")
        return []

    df = df.set_index("ts").sort_index()
    
    # LOG: Verificar cuántos datos hay antes del resample
    flask_app.logger.info(f"[dash] DataFrame antes de resample: {len(df)} filas")
    if len(df) > 0:
        flask_app.logger.info(f"[dash] Rango temporal real: {df.index.min()} a {df.index.max()}")
    
    # Determinar frecuencia de resample según rango
    days_diff = (end_local - start_local).days
    
    # Ajustar frecuencia para tiempo real: usar 1 minuto para periodos cortos
    if days_diff == 0:
        # Un solo día: usar 1min para tiempo casi real
        freq = "1min"
    elif days_diff <= 1:
        # Hasta 1 día: 1 minuto
        freq = "1min"
    elif days_diff <= 3:
        # 2-3 días: 5 minutos
        freq = "5min"
    elif days_diff <= 7:
        # 4-7 días: 10 minutos
        freq = "10min"
    else:
        # Más de 7 días: 30 minutos
        freq = "30min"
    
    flask_app.logger.info(f"[dash] Resampleando con frecuencia: {freq} (rango: {days_diff} días, start={start_local}, end={end_local})")

    # Procesar datos por dispositivo y sensor
    out_rows = []
    for (dev, um), g in df.groupby(["device_id", "Um"]):
        # Convertir a numérico
        g_numeric = g[["pm25", "pm10", "temp", "rh"]].apply(pd.to_numeric, errors="coerce")
        
        # NUEVO ENFOQUE: En lugar de resample que rellena gaps,
        # usar agrupación por timestamp redondeado solo donde hay datos
        # Esto evita crear puntos artificiales entre mediciones
        
        # Redondear timestamps a la frecuencia deseada
        g_numeric = g_numeric.copy()
        g_numeric['ts_rounded'] = g_numeric.index.floor(freq)
        
        # Agrupar por timestamp redondeado y promediar
        # Esto solo crea grupos donde HAY datos reales
        g_grouped = g_numeric.groupby('ts_rounded')[["pm25", "pm10", "temp", "rh"]].mean()
        
        # Solo incluir si hay datos válidos
        if g_grouped.empty or not g_grouped.notna().any().any():
            flask_app.logger.debug(f"[dash] Sin datos válidos para {dev} {um}")
            continue
        
        # Contador de puntos procesados
        points_added = 0
        
        # Convertir a lista de diccionarios
        for ts, row in g_grouped.iterrows():
            item = {
                "ts": ts.isoformat(),
                "device_id": dev,
                "Um": um
            }
            
            # Agregar variables solicitadas
            has_data = False
            for v in variables:
                val = row.get(v, None)
                if pd.isna(val):
                    item[v] = None
                else:
                    try:
                        item[v] = round(float(val), 3)
                        has_data = True
                    except Exception:
                        item[v] = None
            
            # Solo agregar si tiene al menos un dato válido
            if has_data:
                out_rows.append(item)
                points_added += 1
        
        flask_app.logger.debug(f"[dash] {dev} {um}: agregados {points_added} puntos")
    
    flask_app.logger.info(f"[dash] Procesados {len(out_rows)} puntos de datos en total")
    return out_rows
    
    flask_app.logger.info(f"[dash] Procesados {len(out_rows)} puntos de datos en total")
    return out_rows


def _revkey(start_date: str, end_date: str, devices, channel: str, pm_sel: str,
            n_apply, n_refresh, n_intv, n_clear) -> str:
    devs = ",".join(sorted(map(str, devices))) if isinstance(devices, (list, tuple)) else str(devices)
    # Incluimos contadores de botones para forzar refresco cuando corresponde
    return f"{start_date}|{end_date}|{devs}|{channel}|{pm_sel}|a{n_apply or 0}|r{n_refresh or 0}|i{n_intv or 0}|c{n_clear or 0}"

# ---------------- Dash callbacks ---------------- #

def register_callbacks(dash_app, flask_app):
    @dash_app.callback(
        Output("txt-last-update", "children"),
        Input("intv", "n_intervals"),
        Input("btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def _last_update(_n, _c):
        return datetime.now(BOGOTA).strftime("Última actualización: %Y-%m-%d %H:%M:%S (América/Bogotá)")

    # Actualiza el rango de fechas permitidas basado en los datos disponibles
    @dash_app.callback(
        Output("dp-range", "min_date_allowed"),
        Output("dp-range", "max_date_allowed"),
        Input("intv", "n_intervals"),
        Input("btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def _update_available_dates(_n, _c):
        """
        Actualiza dinámicamente el rango de fechas permitidas en el DatePickerRange
        basándose en los datos disponibles en la base de datos.
        """
        from sqlalchemy import func
        from src.core.models import Measurement
        
        try:
            with flask_app.app_context():
                result = db.session.query(
                    func.min(Measurement.fecha).label('min_date'),
                    func.max(Measurement.fecha).label('max_date')
                ).first()
                
                if result and result.min_date and result.max_date:
                    min_date = result.min_date.strftime("%Y-%m-%d")
                    max_date = result.max_date.strftime("%Y-%m-%d")
                    flask_app.logger.debug(f"[dash] Rango de fechas disponibles actualizado: {min_date} a {max_date}")
                    return min_date, max_date
        except Exception as e:
            flask_app.logger.error(f"[dash] Error actualizando rango de fechas: {e}")
        
        # Fallback
        today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
        month_ago = (datetime.now(BOGOTA) - timedelta(days=30)).strftime("%Y-%m-%d")
        return month_ago, today

    # Callback de DEBUG para monitorear cambios en el DatePickerRange
    @dash_app.callback(
        Output("dp-range", "style"),  # Salida dummy, no cambiamos nada
        Input("dp-range", "start_date"),
        Input("dp-range", "end_date"),
        prevent_initial_call=True,
    )
    def _debug_date_changes(start_date, end_date):
        """Callback de debug para verificar que las fechas se están actualizando."""
        flask_app.logger.info(f"[dash] DEBUG DatePicker cambio: start={start_date}, end={end_date}")
        return {}  # Retornar estilo vacío (no cambia nada visualmente)

    # Actualiza con: aplicar, refrescar, intervalo, limpiar
    @dash_app.callback(
        Output("graph-pm", "figure"),
        Output("graph-rh", "figure"),
        Output("graph-temp", "figure"),

        # Disparadores - botones, intervalo Y cambios en fechas
        Input("btn-apply", "n_clicks"),
        Input("btn-refresh", "n_clicks"),
        Input("intv", "n_intervals"),
        Input("btn-clear", "n_clicks"),
        Input("dp-range", "start_date"),  # Ahora es Input para detectar cambios
        Input("dp-range", "end_date"),    # Ahora es Input para detectar cambios

        # Resto de filtros como State - se leen al disparar
        State("ddl-devices", "value"),
        State("rdo-channel", "value"),
        State("rdo-pm", "value"),
        prevent_initial_call=False,
    )
    def _update(n_apply, n_refresh, n_intv, n_clear, start_date, end_date,
                devices, channel, pm_sel):
        
        from dash import callback_context
        
        # Identificar qué disparó el callback
        trigger_id = "initial"
        if callback_context.triggered:
            trigger_prop = callback_context.triggered[0]['prop_id']
            trigger_id = trigger_prop.split('.')[0] if '.' in trigger_prop else trigger_prop
        
        # LOG inicial para debug
        flask_app.logger.info(f"[dash] ===== Callback disparado por: {trigger_id} =====")
        flask_app.logger.info(f"[dash] Filtros recibidos (RAW):")
        flask_app.logger.info(f"  - start_date: {start_date}")
        flask_app.logger.info(f"  - end_date: {end_date}")
        flask_app.logger.info(f"  - devices: {devices}")
        flask_app.logger.info(f"  - channel: {channel} (tipo: {type(channel).__name__})")
        flask_app.logger.info(f"  - pm_sel: {pm_sel} (tipo: {type(pm_sel).__name__})")
        
        # VERIFICACIÓN DE FECHAS
        if start_date == end_date:
            flask_app.logger.info(f"[dash] FILTRO UN SOLO DIA: {start_date}")
        else:
            flask_app.logger.info(f"[dash] FILTRO RANGO: {start_date} a {end_date}")

        # ========== VALIDACIÓN Y NORMALIZACIÓN ==========
        
        # 1. Validar dispositivos
        if not devices or (isinstance(devices, list) and len(devices) == 0):
            flask_app.logger.warning("[dash] No hay dispositivos seleccionados - retornando sin cambios")
            return no_update, no_update, no_update
        
        dev_list = list(map(str, devices if isinstance(devices, (list, tuple)) else [devices]))
        
        # 2. Validar y normalizar fechas
        if not start_date and end_date:
            start_date = end_date
        if not end_date and start_date:
            end_date = start_date
        if not start_date and not end_date:
            today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
            start_date = end_date = today
        
        # 3. SOLO actualizar end_date a hoy si el usuario presiona Actualizar
        # NO modificar las fechas en actualizaciones automáticas (intv)
        if trigger_id == 'btn-refresh':
            today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
            end_date = today
            flask_app.logger.info(f"[dash] Botón Actualizar - extendiendo end_date a hoy: {end_date}")
        
        # 4. Validar y normalizar sensores (channel)
        if isinstance(channel, list):
            # Filtrar valores válidos: solo strings que empiecen con "Um"
            channel = [c for c in channel if isinstance(c, str) and c.startswith("Um")]
        elif channel is None:
            channel = []
        else:
            # Convertir string único a lista
            channel = [channel] if channel else []
        
        # Si no hay sensores seleccionados, buscar TODOS los disponibles (no forzar)
        if not channel or len(channel) == 0:
            channel = ["Um1", "Um2"]
            flask_app.logger.info("[dash] No hay sensores seleccionados - buscando datos de ambos sensores")
        
        # 5. Validar y normalizar material particulado (pm_sel)
        if isinstance(pm_sel, list):
            # Filtrar valores válidos: solo "pm25" o "pm10"
            pm_sel = [p for p in pm_sel if p in ("pm25", "pm10")]
        elif pm_sel is None:
            pm_sel = []
        else:
            # Convertir string único a lista
            pm_sel = [pm_sel] if pm_sel else []
        
        # Si no hay PM seleccionado, buscar TODOS (no forzar)
        if not pm_sel or len(pm_sel) == 0:
            pm_sel = ["pm25", "pm10"]
            flask_app.logger.info("[dash] No hay material particulado seleccionado - mostrando ambos tipos")
        
        # LOG después de normalización
        flask_app.logger.info(f"[dash] Filtros normalizados:")
        flask_app.logger.info(f"  - Fecha: {start_date} a {end_date}")
        flask_app.logger.info(f"  - Dispositivos: {dev_list}")
        flask_app.logger.info(f"  - Sensores (channel): {channel}")
        flask_app.logger.info(f"  - Material Particulado (pm_sel): {pm_sel}")

        # ========== CONSULTA DE DATOS ==========
        
        variables = ["pm25", "pm10", "temp", "rh"]
        
        # Determinar si hay datos de PM para mostrar
        fetch_pm_data = bool(channel) and bool(pm_sel)
        
        points = _fetch_points_for_range(flask_app, channel, variables, start_date, end_date, sel_devices=dev_list)
        df = pd.DataFrame(points)
        
        if df.empty:
            flask_app.logger.warning("[dash] No se encontraron datos para los filtros aplicados")
            df = pd.DataFrame(columns=["ts", "device_id", "Um", "pm25", "pm10", "temp", "rh"])
        
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

        # ========== LOGS DE DEPURACIÓN ==========
        try:
            uniq_devices = df["device_id"].dropna().unique().tolist() if "device_id" in df.columns else []
            uniq_ums = df["Um"].dropna().unique().tolist() if "Um" in df.columns else []
            
            flask_app.logger.info(
                f"[dash] Datos obtenidos: {len(df)} filas, "
                f"devices={uniq_devices}, sensores={uniq_ums}"
            )
            
            if len(df) > 0 and "ts" in df.columns:
                fecha_min = df["ts"].min()
                fecha_max = df["ts"].max()
                flask_app.logger.info(f"[dash] Rango de datos: {fecha_min} a {fecha_max}")
        except Exception as e:
            flask_app.logger.error(f"[dash] Error en logging: {e}")

        # ========== CONFIGURACIÓN DE VISUALIZACIÓN ==========

        x0, x1 = fixed_bounds(start_date, end_date)
        rev = _revkey(start_date, end_date, dev_list, channel, pm_sel, n_apply, n_refresh, n_intv, n_clear)
        hfmt = _hover_fmt(start_date, end_date)
        xaxis_config = _xaxis_format(start_date, end_date)

        # ========== GRÁFICA DE MATERIAL PARTICULADO ==========
        fig_pm = go.Figure()
        
        # Generar gráfica de PM con los filtros aplicados
        # Determinar qué material particulado mostrar según pm_sel
        want_pm25 = "pm25" in pm_sel
        want_pm10 = "pm10" in pm_sel
        
        # Calcular umbral de gap dinámico según rango de fechas
        try:
            s = datetime.strptime(start_date, "%Y-%m-%d")
            e = datetime.strptime(end_date, "%Y-%m-%d")
            days_range = (e - s).days
            
            # Umbral adaptativo: más días = umbral mayor para evitar gaps excesivos
            if days_range == 0:
                gap_threshold_minutes = 15  # 1 día: gaps de 15+ minutos
            elif days_range <= 3:
                gap_threshold_minutes = 30  # 2-3 días: gaps de 30+ minutos
            elif days_range <= 7:
                gap_threshold_minutes = 60  # 4-7 días: gaps de 1+ hora
            else:
                gap_threshold_minutes = 180  # 8+ días: gaps de 3+ horas
                
            flask_app.logger.info(f"[dash] Gap threshold: {gap_threshold_minutes} min para rango de {days_range} días")
        except Exception:
            gap_threshold_minutes = 30  # Fallback seguro
        
        flask_app.logger.info(f"[dash] Generando gráfica PM - PM2.5: {want_pm25}, PM10: {want_pm10}, sensores: {channel}")
        
        traces_added = 0
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            dev_color = color_for_device(dev)  # Color fijo por equipo
            
            # Iterar sobre los sensores disponibles en el DataFrame
            for um in sorted(df["Um"].dropna().unique()):
                # Verificar si este sensor está en la selección del usuario
                if str(um) not in channel:
                    flask_app.logger.debug(f"[dash] Omitiendo sensor {um} (filtro: {channel})")
                    continue
                
                sub = df[(df["device_id"] == dev) & (df["Um"] == um)]
                if sub.empty:
                    flask_app.logger.debug(f"[dash] Sin datos para {dev} {um}")
                    continue
                
                flask_app.logger.debug(f"[dash] {dev} {um}: {len(sub)} puntos disponibles")
                
                # Estilo de línea según sensor (sólido vs punteado)
                dash_style = DASH_BY_UM.get(str(um), "solid")
                base = f"{friendly} {um_label(um)}"
                
                # Agregar PM2.5 si está seleccionado
                if want_pm25 and ("pm25" in sub.columns):
                    pm25_data = sub["pm25"].dropna()
                    if len(pm25_data) > 0:
                        # Detectar gaps temporales y agregar None para forzar interrupciones
                        x_vals, y_vals = _insert_gaps_for_plotly(sub["ts"], sub["pm25"], gap_threshold_minutes=gap_threshold_minutes)
                        
                        fig_pm.add_trace(go.Scatter(
                            x=x_vals, y=y_vals, mode="lines",
                            name=f"{base} PM2.5",
                            line=dict(
                                color=dev_color,
                                width=PM_COLORS["pm25"]["width"],
                                dash=dash_style
                            ),
                            opacity=PM_COLORS["pm25"]["opacity"],
                            connectgaps=False,  # No conectar donde no hay datos
                            hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} µg/m³<extra>%{{fullData.name}}</extra>",
                        ))
                        traces_added += 1
                        flask_app.logger.debug(f"[dash] Agregada traza: {base} PM2.5 ({len(pm25_data)} puntos)")
                
                # Agregar PM10 si está seleccionado
                if want_pm10 and ("pm10" in sub.columns):
                    pm10_data = sub["pm10"].dropna()
                    if len(pm10_data) > 0:
                        # Detectar gaps temporales y agregar None para forzar interrupciones
                        x_vals, y_vals = _insert_gaps_for_plotly(sub["ts"], sub["pm10"], gap_threshold_minutes=gap_threshold_minutes)
                        
                        fig_pm.add_trace(go.Scatter(
                            x=x_vals, y=y_vals, mode="lines",
                            name=f"{base} PM10",
                            line=dict(
                                color=dev_color,
                                width=PM_COLORS["pm10"]["width"],
                                dash=dash_style
                            ),
                            opacity=PM_COLORS["pm10"]["opacity"],
                            connectgaps=False,  # No conectar donde no hay datos
                            hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} µg/m³<extra>%{{fullData.name}}</extra>",
                        ))
                        traces_added += 1
                        flask_app.logger.debug(f"[dash] Agregada traza: {base} PM10 ({len(pm10_data)} puntos)")
        
        flask_app.logger.info(f"[dash] Total trazas PM agregadas: {traces_added}")
        
        # Si no hay trazas, mostrar mensaje informativo
        if len(fig_pm.data) == 0:
            fig_pm.add_annotation(
                text="No hay datos disponibles para los filtros seleccionados",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color="#666")
            )

        apply_layout(fig_pm, rev)
        fig_pm.update_layout(hovermode=pick_hovermode(len(fig_pm.data)),
                             yaxis_title="Material particulado(µg/m³)")
        fig_pm.update_yaxes(autorange=True, fixedrange=False)
        fig_pm.update_xaxes(
            range=[x0, x1], 
            showspikes=True, 
            spikemode="across", 
            spikesnap="cursor",
            tickangle=-45,  # Rotar etiquetas para mejor legibilidad
            **xaxis_config
        )

        # ========== GRÁFICA DE HUMEDAD RELATIVA ==========
        fig_rh = go.Figure()
        
        # Agrupar por dispositivo (temp y RH no dependen del sensor Um)
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            
            if sub.empty or "rh" not in sub.columns:
                continue
            
            # Agrupar por timestamp para promediar si hay múltiples sensores
            sub_grouped = sub.groupby("ts")["rh"].mean().reset_index()
            
            # Detectar gaps temporales y agregar None para forzar interrupciones
            x_vals, y_vals = _insert_gaps_for_plotly(sub_grouped["ts"], sub_grouped["rh"], gap_threshold_minutes=gap_threshold_minutes)
            
            fig_rh.add_trace(go.Scatter(
                x=x_vals, y=y_vals, mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                connectgaps=False,  # No conectar donde no hay datos
                hovertemplate=f"%{{x|{hfmt}}} — %{{y:.0f}} %<extra>%{{fullData.name}}</extra>",
            ))
        
        apply_layout(fig_rh, rev)
        fig_rh.update_layout(hovermode=pick_hovermode(len(fig_rh.data)),
                             yaxis_title="Humedad Relativa(%)")
        fig_rh.update_xaxes(
            range=[x0, x1], 
            showspikes=True, 
            spikemode="across", 
            spikesnap="cursor",
            tickangle=-45,
            **xaxis_config
        )

        # ========== GRÁFICA DE TEMPERATURA ==========
        fig_temp = go.Figure()
        
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            
            if sub.empty or "temp" not in sub.columns:
                continue
            
            # Agrupar por timestamp para promediar si hay múltiples sensores
            sub_grouped = sub.groupby("ts")["temp"].mean().reset_index()
            
            # Detectar gaps temporales y agregar None para forzar interrupciones
            x_vals, y_vals = _insert_gaps_for_plotly(sub_grouped["ts"], sub_grouped["temp"], gap_threshold_minutes=gap_threshold_minutes)
            
            fig_temp.add_trace(go.Scatter(
                x=x_vals, y=y_vals, mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                connectgaps=False,  # No conectar donde no hay datos
                hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} °C<extra>%{{fullData.name}}</extra>",
            ))
        
        apply_layout(fig_temp, rev)
        fig_temp.update_layout(hovermode=pick_hovermode(len(fig_temp.data)),
                               yaxis_title="Temperatura (°C)")
        fig_temp.update_xaxes(
            range=[x0, x1], 
            showspikes=True, 
            spikemode="across", 
            spikesnap="cursor",
            tickangle=-45,
            **xaxis_config
        )

        flask_app.logger.info(f"[dash] Gráficas generadas - PM: {len(fig_pm.data)} trazas, RH: {len(fig_rh.data)} trazas, Temp: {len(fig_temp.data)} trazas")
        
        return fig_pm, fig_rh, fig_temp

    @dash_app.callback(
        Output("dp-range", "start_date"),
        Output("dp-range", "end_date"),
        Output("ddl-devices", "value"),
        Output("rdo-channel", "value"),
        Output("rdo-pm", "value"),
        Input("btn-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    def _clear_filters(n_clicks):
        """Restablece TODOS los filtros a sus valores por defecto."""
        # Fechas: últimos 4 días
        today_dt = datetime.now(BOGOTA)
        today = today_dt.strftime("%Y-%m-%d")
        start_default = (today_dt - timedelta(days=3)).strftime("%Y-%m-%d")
        
        # Dispositivos: TODOS los equipos del sistema (S1 a S6)
        # No filtramos por disponibilidad de datos
        all_devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
        
        # Sensores: ambos
        all_sensors = ["Um1", "Um2"]
        
        # Material Particulado: ambos
        all_pm = ["pm25", "pm10"]
        
        flask_app.logger.info("[dash] Restableciendo filtros: todos los equipos, sensores y PM")
        
        return start_default, today, all_devices, all_sensors, all_pm

    # Callbacks para actualizar URLs de botones de reportes con filtros actuales
    @dash_app.callback(
        Output("btn-report-hour", "href"),
        Output("btn-report-24h", "href"),
        Output("btn-report-7d", "href"),
        Output("btn-report-month", "href"),
        Input("ddl-devices", "value"),
        Input("rdo-channel", "value"),
    )
    def _update_report_urls(devices, channel):
        """Actualiza las URLs de los botones de reporte Excel con los filtros actuales."""
        # Construir parámetros de query
        params = []
        
        # Agregar dispositivos si hay selección específica
        if devices and len(devices) > 0:
            device_str = ",".join(devices)
            params.append(f"device_id={device_str}")
        
        # Agregar canal
        if channel:
            # Si es lista (Checklist), convertir a string separado por comas
            if isinstance(channel, list):
                if len(channel) == 1:
                    params.append(f"sensor_channel={channel[0]}")
                # Si ambos están seleccionados o ninguno, no filtrar
            else:
                # Legacy: string único
                if channel != "ambos":
                    params.append(f"sensor_channel={channel}")
        
        query_string = "&".join(params)
        base_params = f"&{query_string}" if query_string else ""
        
        # URLs para cada período (Excel en lugar de PDF)
        url_hour = f"/api/reports/excel?period=hour{base_params}"
        url_24h = f"/api/reports/excel?period=24hours{base_params}"
        url_7d = f"/api/reports/excel?period=7days{base_params}"
        url_month = f"/api/reports/excel?period=month{base_params}"
        
        return url_hour, url_24h, url_7d, url_month
