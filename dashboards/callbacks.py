from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from dash import Input, Output, State, no_update, ctx
import plotly.graph_objects as go
from labels import label_for  # nombres amigables

BOGOTA = ZoneInfo("America/Bogota")

COLORWAY = [
    "#22C55E", "#3B82F6", "#F59E0B", "#EF4444", "#A855F7", "#06B6D4",
    "#14B8A6", "#F97316", "#8B5CF6", "#10B981", "#E11D48", "#0EA5E9",
    "#84CC16", "#6366F1", "#D946EF", "#2DD4BF"
]
DASH_BY_UM = {"Um1": "solid", "Um2": "dot"}  # NO se toca lógica


def color_for_device(device_id: str) -> str:
    idx = abs(hash(str(device_id))) % len(COLORWAY)
    return COLORWAY[idx]


def fixed_bounds(start_date: str, end_date: str):
    """Rango [start 00:00:00, end 23:59:59] en tz Bogotá."""
    if not start_date:
        start_date = end_date
    if not end_date:
        end_date = start_date
    s = datetime.strptime(start_date, "%Y-%m-%d")
    e = datetime.strptime(end_date, "%Y-%m-%d")
    x0 = datetime(s.year, s.month, s.day, 0, 0, 0, tzinfo=BOGOTA)
    x1 = datetime(e.year, e.month, e.day, 23, 59, 59, tzinfo=BOGOTA)
    return x0, x1


def fix_axis_y(fig: go.Figure, low: float = 0, high: float = 100, tick: float = 10, lock: bool = True):
    fig.update_yaxes(range=[low, high], dtick=tick, tickformat=".0f", fixedrange=lock)
    return fig


def um_label(um_value: str) -> str:
    s = str(um_value).lower()
    if s == "um1":
        return "Sensor 1"
    if s == "um2":
        return "Sensor 2"
    return um_value


UNIFIED_MAX_TRACES = 10
def pick_hovermode(trace_count: int) -> str:
    return "x unified" if trace_count <= UNIFIED_MAX_TRACES else "x"


COMMON_LAYOUT = dict(
    template="plotly_white",
    colorway=COLORWAY,
    uirevision="keep",  # se sobreescribe con una clave dinámica por figura
    transition=dict(duration=0),
    margin=dict(l=50, r=16, t=48, b=40),
    legend=dict(orientation="h", y=1.02, yanchor="bottom",
                x=0, xanchor="left", traceorder="normal"),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(
        font=dict(size=11),
        namelength=28,
        align="left",
        bgcolor="rgba(255,255,255,0.98)",
        bordercolor="#11B6C7",
    ),
)


def _fetch_points_for_range(sess, url, base_params, start_date: str, end_date: str):
    """Intenta con start/end; si no, día a día con 'date=' y concatena."""
    try:
        params_range = base_params.copy()
        params_range["start"] = start_date
        params_range["end"] = end_date
        r = sess.get(url, query_string=params_range)
        js = r.get_json() or {}
        pts = js.get("points", [])
        if pts:
            return pts
    except Exception:
        pass

    all_pts = []
    try:
        d0 = datetime.strptime(start_date, "%Y-%m-%d").date()
        d1 = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception:
        return all_pts

    d = d0
    while d <= d1:
        p = base_params.copy()
        p["date"] = d.strftime("%Y-%m-%d")
        try:
            rr = sess.get(url, query_string=p)
            jj = rr.get_json() or {}
            all_pts.extend(jj.get("points", []))
        except Exception:
            pass
        d += timedelta(days=1)

    return all_pts


def _revkey(start_date: str, end_date: str) -> str:
    return f"range:{start_date or ''}|{end_date or ''}"


def register_callbacks(dash_app, flask_app):
    @dash_app.callback(
        Output("txt-last-update", "children"),
        Input("intv", "n_intervals"),
        Input("btn-refresh", "n_clicks"),
        prevent_initial_call=False,
    )
    def _last_update(_n, _c):
        return datetime.now(BOGOTA).strftime("Última actualización: %Y-%m-%d %H:%M:%S (América/Bogotá)")

    @dash_app.callback(
        Output("graph-pm", "figure"),
        Output("graph-rh", "figure"),
        Output("graph-temp", "figure"),

        # Inputs que deben gatillar redibujado
        Input("ddl-devices", "value"),
        Input("rdo-channel", "value"),
        Input("rdo-pm", "value"),
        Input("btn-apply", "n_clicks"),     # aplicar
        Input("btn-clear", "n_clicks"),     # limpiar
        Input("btn-refresh", "n_clicks"),   # botón “Actualizar ahora”
        Input("intv", "n_intervals"),       # auto-refresh

        # Fechas como INPUTS (así leemos los nuevos valores tras limpiar/aplicar)
        Input("dp-range", "start_date"),
        Input("dp-range", "end_date"),
        prevent_initial_call=False,
    )
    def _update(devices, channel, pm_sel, _n_apply, _n_clear, _n_refresh, _n_intv,
                start_date, end_date):
        # Si no hay equipos seleccionados
        if not devices:
            return no_update, no_update, no_update

        # Si el disparador NO es aplicar/limpiar/refresh/interval/equipos/radios
        # y sólo cambió el datepicker (usuario moviendo fechas), no actualizamos.
        trigger_ids_ok = {
            "btn-apply", "btn-clear", "btn-refresh", "intv",
            "ddl-devices", "rdo-channel", "rdo-pm"
        }
        trig = ctx.triggered_id
        if trig not in trigger_ids_ok and trig is not None:
            return no_update, no_update, no_update

        # fallbacks de fechas
        if not start_date and end_date:
            start_date = end_date
        if not end_date and start_date:
            end_date = start_date
        if not start_date and not end_date:
            today = datetime.now(BOGOTA).strftime("%Y-%m-%d")
            start_date = end_date = today

        base_params = {
            "device_id": ",".join(devices),
            "sensor_channel": channel,       # sigue siendo Um1/Um2/ambos
            "vars": "pm25,pm10,temp,rh",
        }

        with flask_app.test_request_context():
            url = "/api/series"
        sess = flask_app.test_client()

        # obtiene los puntos (con soporte para ambas variantes de API)
        points = _fetch_points_for_range(sess, url, base_params, start_date, end_date)

        df = pd.DataFrame(points)
        if df.empty:
            df = pd.DataFrame(columns=["ts", "device_id", "Um", "pm25", "pm10", "temp", "rh"])
        if "ts" in df.columns:
            df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

        # Rango X para los tres gráficos y clave de uirevision por rango
        x0, x1 = fixed_bounds(start_date, end_date)
        rev = _revkey(start_date, end_date)

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

                if want_pm25:
                    fig_pm.add_trace(go.Scatter(
                        x=sub["ts"], y=sub["pm25"], mode="lines",
                        name=f"{base} PM2.5",
                        line=dict(color=dev_color, width=2.2, dash=dash_style),
                        opacity=0.95,
                        hovertemplate="%{x|%H:%M} — %{y:.1f} µg/m³<extra>%{fullData.name}</extra>",
                    ))
                if want_pm10:
                    fig_pm.add_trace(go.Scatter(
                        x=sub["ts"], y=sub["pm10"], mode="lines",
                        name=f"{base} PM10",
                        line=dict(color=dev_color, width=1.2, dash=dash_style),
                        opacity=0.70,
                        hovertemplate="%{x|%H:%M} — %{y:.1f} µg/m³<extra>%{fullData.name}</extra>",
                    ))
##===========================================================================
    ## Eje fijo

##        fig_pm.update_layout(**COMMON_LAYOUT, hovermode=pick_hovermode(len(fig_pm.data)), yaxis_title=" Material Particulado µg/m³")
##        fig_pm.update_xaxes(range=[x0, x1], tickformat="%H:%M", showspikes=True,
##                            spikemode="across", spikesnap="cursor")
##        fix_axis_y(fig_pm, low=0, high=100, tick=10, lock=True)
##        fig_pm.update_layout(uirevision=rev)
##==========================================================================
        fig_pm.update_layout(
            **COMMON_LAYOUT,
            hovermode=pick_hovermode(len(fig_pm.data)),
            yaxis_title="Material particulado(µg/m³)",
    )
        fig_pm.update_xaxes(
            range=[x0, x1],
            tickformat="%H:%M",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
    )

# Eje Y dinámico 
        fig_pm.update_yaxes(autorange=True, fixedrange=False)

        fig_pm.update_layout(uirevision=rev)

        

        # ========== RH ==========
        fig_rh = go.Figure()
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            if sub.empty:
                continue
            fig_rh.add_trace(go.Scatter(
                x=sub["ts"], y=sub["rh"], mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                hovertemplate="%{x|%H:%M} — %{y:.0f} %<extra>%{fullData.name}</extra>",
            ))

        fig_rh.update_layout(**COMMON_LAYOUT, hovermode=pick_hovermode(len(fig_rh.data)),
                             yaxis_title="Humedad Relativa(%)")
        fig_rh.update_xaxes(range=[x0, x1], tickformat="%H:%M", showspikes=True,
                            spikemode="across", spikesnap="cursor")
        fig_rh.update_layout(uirevision=rev)

        # ========== Temp ==========
        fig_temp = go.Figure()
        for dev in sorted(df["device_id"].dropna().unique()):
            friendly = label_for(dev)
            sub = df[df["device_id"] == dev]
            if sub.empty:
                continue
            fig_temp.add_trace(go.Scatter(
                x=sub["ts"], y=sub["temp"], mode="lines", name=friendly,
                line=dict(color=color_for_device(dev), width=2.0),
                hovertemplate="%{x|%H:%M} — %{y:.1f} °C<extra>%{fullData.name}</extra>",
            ))

        fig_temp.update_layout(**COMMON_LAYOUT, hovermode=pick_hovermode(len(fig_temp.data)),
                               yaxis_title="Temperatura (°C)")
        fig_temp.update_xaxes(range=[x0, x1], tickformat="%H:%M", showspikes=True,
                              spikemode="across", spikesnap="cursor")
        fig_temp.update_layout(uirevision=rev)

        return fig_pm, fig_rh, fig_temp

    # -------- Limpiar filtros: deja hoy y radios por defecto --------
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
