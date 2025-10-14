# dashboards/callbacks.py
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from dash import Input, Output, State, no_update
import plotly.graph_objects as go
from labels import label_for

from db import db
from models import Measurement, SensorChannel

BOGOTA = ZoneInfo("America/Bogota")

COLORWAY = [
    "#22C55E", "#3B82F6", "#F59E0B", "#EF4444", "#A855F7", "#06B6D4",
    "#14B8A6", "#F97316", "#8B5CF6", "#10B981", "#E11D48", "#0EA5E9",
    "#84CC16", "#6366F1", "#D946EF", "#2DD4BF"
]
DASH_BY_UM = {"Um1": "solid", "Um2": "dot"}

def color_for_device(device_id: str) -> str:
    idx = abs(hash(str(device_id))) % len(COLORWAY)
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

def _parse_channels(code: str | None):
    if not code: return [SensorChannel.Um1, SensorChannel.Um2]
    q = str(code).strip().lower()
    if q in ("um1", "sensor1", "s1"): return [SensorChannel.Um1]
    if q in ("um2", "sensor2", "s2"): return [SensorChannel.Um2]
    return [SensorChannel.Um1, SensorChannel.Um2]

def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()

def _hover_fmt(start_date: str, end_date: str) -> str:
    return "%H:%M" if start_date == end_date else "%m-%d %H:%M"

def _fetch_points_for_range(flask_app, channel_value: str, variables: list[str],
                            start_date: str, end_date: str, sel_devices: list[str] | None):
    """
    Lee DIRECTO de la BD por rango y canal; luego filtra equipos en pandas
    aceptando IDs o etiquetas, insensible a mayúsculas/espacios.
    """
    channels = _parse_channels(channel_value)
    variables = variables or ["pm25", "pm10", "temp", "rh"]

    sel_devices = [str(d) for d in (sel_devices or [])]
    sel_norm = {_norm(d) for d in sel_devices if d}

    start_local, end_local = fixed_bounds(start_date, end_date)

    with flask_app.app_context():
        # Consulta optimizada con filtro directo en la base de datos
        qry = (
            db.session.query(Measurement)
            .filter(
                Measurement.fechah_local >= start_local,
                Measurement.fechah_local <= end_local,
                Measurement.sensor_channel.in_(channels),
            )
        )
        
        # Si hay dispositivos seleccionados, filtrar directamente en la consulta
        if sel_devices:
            qry = qry.filter(Measurement.device_id.in_(sel_devices))
        
        # Ordenar y ejecutar
        qry = qry.order_by(Measurement.fechah_local.asc())
        rows = qry.all()

    if not rows:
        return []

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
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    try:
        if df["ts"].dt.tz is None:
            df["ts"] = df["ts"].dt.tz_localize(BOGOTA)
        else:
            df["ts"] = df["ts"].dt.tz_convert(BOGOTA)
    except Exception:
        df["ts"] = pd.to_datetime(df["ts"]).dt.tz_localize(BOGOTA)

    # Filtrado por equipos robusto
    if sel_norm:
        ids_presentes = [str(x) for x in df["device_id"].dropna().unique()]
        allowed_ids = set()
        for dev in ids_presentes:
            if _norm(dev) in sel_norm or _norm(label_for(dev)) in sel_norm:
                allowed_ids.add(dev)
        if allowed_ids:
            df = df[df["device_id"].isin(list(allowed_ids))]

    if df.empty:
        return []

    df = df.set_index("ts").sort_index()
    
    # Filtrar estrictamente dentro del rango solicitado
    df = df.loc[start_local:end_local]
    
    # Optimización: ajustar la frecuencia de resample según el rango de fechas
    days_diff = (end_local - start_local).days
    if days_diff <= 1:
        freq = "1min"  # 1 día o menos: cada minuto
    elif days_diff <= 7:
        freq = "5min"  # Hasta 1 semana: cada 5 minutos
    else:
        freq = "15min"  # Más de 1 semana: cada 15 minutos

    out_rows = []
    had_numeric = False
    for (dev, um), g in df.groupby(["device_id", "Um"]):
        g1 = (
            g[["pm25", "pm10", "temp", "rh"]]
            .apply(pd.to_numeric, errors="coerce")
            .resample(freq).mean()
        )
        # NO usar reindex - solo los datos que existen
        if not g1.empty and g1.notna().any().any():
            had_numeric = True
            for ts, row in g1.iterrows():
                # Verificar que está dentro del rango
                if ts < start_local or ts > end_local:
                    continue
                item = {"ts": ts.isoformat(), "device_id": dev, "Um": um}
                for v in variables:
                    val = row.get(v, None)
                    if pd.isna(val):
                        item[v] = None
                    else:
                        try:
                            item[v] = round(float(val), 3)
                        except Exception:
                            item[v] = None
                out_rows.append(item)

    if had_numeric:
        return out_rows

    # fallback crudo - solo si no hubo datos numéricos
    out_rows = []
    df_raw = df.reset_index()
    for _, row in df_raw.iterrows():
        ts = pd.to_datetime(row["ts"])
        # Verificar que está dentro del rango
        if ts < start_local or ts > end_local:
            continue
        item = {
            "ts": ts.tz_convert(BOGOTA).isoformat(),
            "device_id": row["device_id"],
            "Um": row["Um"],
        }
        for v in variables:
            try:
                val = row.get(v, None)
                item[v] = round(float(val), 3) if val is not None and not pd.isna(val) else None
            except Exception:
                item[v] = None
        out_rows.append(item)
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

    # Actualiza con: aplicar, refrescar, intervalo, limpiar O cambio de fechas
    @dash_app.callback(
        Output("graph-pm", "figure"),
        Output("graph-rh", "figure"),
        Output("graph-temp", "figure"),

        # Disparadores
        Input("btn-apply", "n_clicks"),
        Input("btn-refresh", "n_clicks"),
        Input("intv", "n_intervals"),
        Input("btn-clear", "n_clicks"),
        Input("dp-range", "start_date"),  # Cambiado de State a Input
        Input("dp-range", "end_date"),    # Cambiado de State a Input

        # Filtros (como State)
        State("ddl-devices", "value"),
        State("rdo-channel", "value"),
        State("rdo-pm", "value"),
        prevent_initial_call=False,
    )
    def _update(n_apply, n_refresh, n_intv, n_clear, start_date, end_date,
                devices, channel, pm_sel):

        # Normalizar entradas
        if not devices:
            return no_update, no_update, no_update
        if not start_date and end_date:
            start_date = end_date
        if not end_date and start_date:
            end_date = start_date
        if not start_date and not end_date:
            today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
            start_date = end_date = today

        dev_list = list(map(str, devices if isinstance(devices, (list, tuple)) else [devices]))
        variables = ["pm25", "pm10", "temp", "rh"]

        # --------- DATA ---------
        points = _fetch_points_for_range(flask_app, channel, variables, start_date, end_date, sel_devices=dev_list)
        df = pd.DataFrame(points)
        if df.empty:
            df = pd.DataFrame(columns=["ts", "device_id", "Um", "pm25", "pm10", "temp", "rh"])
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

        # LOGS de depuración en consola del servidor
        try:
            uniq = df["device_id"].dropna().unique().tolist()
            flask_app.logger.info(
                f"[dash] apply={n_apply} refresh={n_refresh} intv={n_intv} clear={n_clear} "
                f"range={start_date}..{end_date} channel={channel} pm={pm_sel} "
                f"sel_devices={dev_list} -> devices_in_df={uniq} rows={len(df)}"
            )
            # Log adicional para fechas
            if len(df) > 0:
                fecha_min = df["ts"].min() if "ts" in df.columns else None
                fecha_max = df["ts"].max() if "ts" in df.columns else None
                flask_app.logger.info(f"[dash] datos: fecha_min={fecha_min}, fecha_max={fecha_max}")
        except Exception as e:
            flask_app.logger.error(f"[dash] Error en logging: {e}")

        x0, x1 = fixed_bounds(start_date, end_date)
        rev = _revkey(start_date, end_date, dev_list, channel, pm_sel, n_apply, n_refresh, n_intv, n_clear)
        hfmt = _hover_fmt(start_date, end_date)

        # ========== PM ==========
        fig_pm = go.Figure()
        want_pm25 = pm_sel in ("pm25", "ambas")
        want_pm10 = pm_sel in ("pm10", "ambas")

        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            dev_color = color_for_device(dev)
            for um in sorted(df["Um"].dropna().unique()):
                sub = df[(df["device_id"] == dev) & (df["Um"] == um)]
                if sub.empty:
                    continue
                dash_style = DASH_BY_UM.get(str(um), "solid")
                base = f"{friendly} {um_label(um)}"
                if want_pm25 and ("pm25" in sub):
                    fig_pm.add_trace(go.Scatter(
                        x=sub["ts"], y=sub["pm25"], mode="lines",
                        name=f"{base} PM2.5",
                        line=dict(color=dev_color, width=2.2, dash=dash_style),
                        opacity=0.95,
                        hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} µg/m³<extra>%{{fullData.name}}</extra>",
                    ))
                if want_pm10 and ("pm10" in sub):
                    fig_pm.add_trace(go.Scatter(
                        x=sub["ts"], y=sub["pm10"], mode="lines",
                        name=f"{base} PM10",
                        line=dict(color=dev_color, width=1.2, dash=dash_style),
                        opacity=0.70,
                        hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} µg/m³<extra>%{{fullData.name}}</extra>",
                    ))

        apply_layout(fig_pm, rev)
        fig_pm.update_layout(hovermode=pick_hovermode(len(fig_pm.data)),
                             yaxis_title="Material particulado(µg/m³)")
        fig_pm.update_yaxes(autorange=True, fixedrange=False)
        fig_pm.update_xaxes(range=[x0, x1], tickformat=hfmt,
                            showspikes=True, spikemode="across", spikesnap="cursor")

        # ========== RH ==========
        fig_rh = go.Figure()
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            if sub.empty or "rh" not in sub:
                continue
            fig_rh.add_trace(go.Scatter(
                x=sub["ts"], y=sub["rh"], mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                hovertemplate=f"%{{x|{hfmt}}} — %{{y:.0f}} %<extra>%{{fullData.name}}</extra>",
            ))
        apply_layout(fig_rh, rev)
        fig_rh.update_layout(hovermode=pick_hovermode(len(fig_rh.data)),
                             yaxis_title="Humedad Relativa(%)")
        fig_rh.update_xaxes(range=[x0, x1], tickformat=hfmt,
                            showspikes=True, spikemode="across", spikesnap="cursor")

        # ========== Temp ==========
        fig_temp = go.Figure()
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            if sub.empty or "temp" not in sub:
                continue
            fig_temp.add_trace(go.Scatter(
                x=sub["ts"], y=sub["temp"], mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                hovertemplate=f"%{{x|{hfmt}}} — %{{y:.1f}} °C<extra>%{{fullData.name}}</extra>",
            ))
        apply_layout(fig_temp, rev)
        fig_temp.update_layout(hovermode=pick_hovermode(len(fig_temp.data)),
                               yaxis_title="Temperatura (°C)")
        fig_temp.update_xaxes(range=[x0, x1], tickformat=hfmt,
                              showspikes=True, spikemode="across", spikesnap="cursor")

        return fig_pm, fig_rh, fig_temp

    @dash_app.callback(
        Output("dp-range", "start_date"),
        Output("dp-range", "end_date"),
        Output("rdo-channel", "value"),
        Output("rdo-pm", "value"),
        Input("btn-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    def _clear_filters(n_clicks):
        today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
        return today, today, "ambos", "ambas"

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
        if channel and channel != "ambos":
            params.append(f"sensor_channel={channel}")
        
        query_string = "&".join(params)
        base_params = f"&{query_string}" if query_string else ""
        
        # URLs para cada período (Excel en lugar de PDF)
        url_hour = f"/api/reports/excel?period=hour{base_params}"
        url_24h = f"/api/reports/excel?period=24hours{base_params}"
        url_7d = f"/api/reports/excel?period=7days{base_params}"
        url_month = f"/api/reports/excel?period=month{base_params}"
        
        return url_hour, url_24h, url_7d, url_month
