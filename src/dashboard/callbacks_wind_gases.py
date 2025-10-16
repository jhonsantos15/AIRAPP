"""
Callbacks para el dashboard de Viento y Gases.
Maneja la actualización de gráficos de rosa de vientos, NO2, CO2 y velocidad del viento.
"""
from datetime import datetime
from dash import Input, Output, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sqlalchemy import and_

from src.core.database import db
from src.core.models import Measurement, SensorChannel
from src.utils.constants import DEVICE_COLORS, DASH_BY_UM, BOGOTA
from src.utils.labels import label_for


def register_wind_gases_callbacks(app):
    """Registra todos los callbacks del dashboard de viento y gases."""
    
    @app.callback(
        [
            Output("graph-windrose", "figure"),
            Output("graph-wind-speed", "figure"),
            Output("graph-no2", "figure"),
            Output("graph-co2", "figure"),
            Output("stats-summary-wind", "children"),
            Output("txt-last-update-wind", "children"),
        ],
        [
            Input("btn-refresh-wind", "n_clicks"),
            Input("interval-auto-refresh-wind", "n_intervals"),
            Input("btn-apply-wind", "n_clicks"),
        ],
        [
            Input("ddl-devices-wind", "value"),
            Input("chk-variables-wind", "value"),
            Input("date-picker-wind", "start_date"),
            Input("date-picker-wind", "end_date"),
        ],
    )
    def update_wind_gases_dashboard(
        n_refresh, n_intervals, n_apply, devices, variables, start_date, end_date
    ):
        """Actualiza todos los gráficos del dashboard de viento y gases."""
        
        # Validaciones
        if not devices or not variables:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Selecciona al menos un dispositivo y variable",
                template="plotly_white",
            )
            return empty_fig, empty_fig, empty_fig, empty_fig, html.Div("Sin datos"), ""
        
        # Convertir strings a listas si es necesario
        if isinstance(devices, str):
            devices = [devices]
        if isinstance(variables, str):
            variables = [variables]
        
        # Para viento y gases, buscar TODOS los sensores (no depende del sensor)
        channels = [SensorChannel.Um1, SensorChannel.Um2]
        
        # Construir query
        try:
            query = db.session.query(Measurement).filter(
                and_(
                    Measurement.device_id.in_(devices),
                    Measurement.sensor_channel.in_(channels),
                    Measurement.fecha >= start_date,
                    Measurement.fecha <= end_date,
                )
            ).order_by(Measurement.fechah_local)
            
            rows = query.all()
            
            if not rows:
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="No hay datos para el rango seleccionado",
                    template="plotly_white",
                )
                return empty_fig, empty_fig, empty_fig, empty_fig, html.Div("Sin datos"), ""
            
            # Convertir a DataFrame
            data = []
            for row in rows:
                data.append({
                    'device_id': row.device_id,
                    'sensor_channel': row.sensor_channel.name,
                    'fechah_local': row.fechah_local,
                    'no2': row.no2,
                    'co2': row.co2,
                    'vel_viento': row.vel_viento,
                    'dir_viento': row.dir_viento,
                })
            
            df = pd.DataFrame(data)
            
            # Filtrar solo datos con valores no nulos
            df_wind = df[df['vel_viento'].notna() & df['dir_viento'].notna()].copy()
            df_no2 = df[df['no2'].notna()].copy()
            df_co2 = df[df['co2'].notna()].copy()
            
            # Crear gráficos (pasar rango de fechas para el eje X)
            fig_windrose = create_windrose(df_wind, devices)
            fig_wind_speed = create_wind_speed_chart(df_wind, devices, channels, start_date, end_date)
            fig_no2 = create_gas_chart(df_no2, 'no2', 'NO2 (ppb)', devices, channels, start_date, end_date)
            fig_co2 = create_gas_chart(df_co2, 'co2', 'CO2 (ppm)', devices, channels, start_date, end_date)
            
            # Crear resumen estadístico
            stats_html = create_stats_summary(df, variables)
            
            # Última actualización
            now = datetime.now(BOGOTA)
            last_update = f"Última actualización: {now.strftime('%d/%m/%Y %H:%M:%S')}"
            
            return fig_windrose, fig_wind_speed, fig_no2, fig_co2, stats_html, last_update
            
        except Exception as e:
            print(f"Error en update_wind_gases_dashboard: {e}")
            import traceback
            traceback.print_exc()
            
            error_fig = go.Figure()
            error_fig.update_layout(
                title=f"Error al cargar datos: {str(e)}",
                template="plotly_white",
            )
            return error_fig, error_fig, error_fig, error_fig, html.Div(f"Error: {str(e)}"), ""


def create_windrose(df, devices):
    """Crea una rosa de vientos (polar plot)."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No hay datos de viento disponibles")
        return fig
    
    fig = go.Figure()
    
    # Agregar traza por cada dispositivo
    for device in devices:
        df_device = df[df['device_id'] == device]
        if df_device.empty:
            continue
        
        # Agrupar por sectores de dirección (cada 10 grados)
        df_device['dir_sector'] = (df_device['dir_viento'] // 10) * 10
        
        # Calcular frecuencia y velocidad promedio por sector
        stats = df_device.groupby('dir_sector').agg({
            'vel_viento': ['mean', 'count']
        }).reset_index()
        
        stats.columns = ['direccion', 'vel_promedio', 'frecuencia']
        
        # Crear traza
        fig.add_trace(go.Barpolar(
            r=stats['frecuencia'],
            theta=stats['direccion'],
            name=label_for(device),
            marker_color=DEVICE_COLORS.get(device, '#888888'),
            opacity=0.7,
            hovertemplate=(
                f"<b>{label_for(device)}</b><br>" +
                "Dirección: %{theta}°<br>" +
                "Frecuencia: %{r}<br>" +
                "Vel. Promedio: %{customdata:.1f} m/s<extra></extra>"
            ),
            customdata=stats['vel_promedio'],
        ))
    
    fig.update_layout(
        template="plotly_white",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, df.groupby('dir_viento')['vel_viento'].count().max() * 1.1]
            ),
            angularaxis=dict(
                direction="clockwise",
                rotation=90,
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
        ),
        height=280,
        margin=dict(l=40, r=30, t=30, b=50),
    )
    
    return fig


def create_wind_speed_chart(df, devices, channels, start_date, end_date):
    """Crea gráfico de serie temporal de velocidad del viento."""
    from datetime import timedelta
    
    # Convertir fechas string a datetime para el rango del eje X
    if isinstance(start_date, str):
        time_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=BOGOTA)
    else:
        time_start = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=BOGOTA)
    
    if isinstance(end_date, str):
        time_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=BOGOTA)
    else:
        time_end = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=BOGOTA)
    
    if df.empty:
        # Configurar formato del eje X según el rango (incluso sin datos)
        days_diff = (time_end - time_start).days
        if days_diff == 0:
            xaxis_config = {"tickformat": "%H:%M", "dtick": 7200000, "tickangle": -45}
        elif days_diff == 1:
            xaxis_config = {"tickformat": "%H:%M<br>%d %b", "dtick": 10800000, "tickangle": -45}
        elif days_diff <= 3:
            xaxis_config = {"tickformat": "%d %b<br>%H:%M", "dtick": 21600000, "tickangle": -45}
        else:
            xaxis_config = {"tickformat": "%d %b", "dtick": 86400000, "tickangle": -45}
        
        fig = go.Figure()
        fig.update_layout(
            title="No hay datos de velocidad del viento en el rango seleccionado",
            template="plotly_white",
            xaxis=dict(
                range=[time_start, time_end],
                title="Fecha y Hora",
                **xaxis_config
            )
        )
        return fig
    
    fig = go.Figure()
    
    for device in devices:
        for channel in channels:
            df_subset = df[
                (df['device_id'] == device) & 
                (df['sensor_channel'] == channel)
            ]
            
            if df_subset.empty:
                continue
            
            color = DEVICE_COLORS.get(device, '#888888')
            dash_style = DASH_BY_UM.get(channel, 'solid')
            
            fig.add_trace(go.Scatter(
                x=df_subset['fechah_local'],
                y=df_subset['vel_viento'],
                mode='lines+markers',
                name=f"{label_for(device)} - {channel}",
                line=dict(color=color, dash=dash_style, width=2),
                marker=dict(size=4),
                hovertemplate=(
                    f"<b>{label_for(device)} - {channel}</b><br>" +
                    "Fecha: %{x|%d/%m/%Y %H:%M}<br>" +
                    "Velocidad: %{y:.2f} m/s<extra></extra>"
                ),
            ))
    
    # Configurar formato del eje X según el rango
    days_diff = (time_end - time_start).days
    if days_diff == 0:
        # Mismo día: solo horas
        xaxis_tickformat = "%H:%M"
        xaxis_dtick = 7200000  # 2 horas en ms
    elif days_diff == 1:
        # 24 horas: hora prominente
        xaxis_tickformat = "%H:%M<br>%d %b"
        xaxis_dtick = 10800000  # 3 horas en ms
    elif days_diff <= 3:
        # 2-3 días: día + hora
        xaxis_tickformat = "%d %b<br>%H:%M"
        xaxis_dtick = 21600000  # 6 horas en ms
    else:
        # Más días: solo fecha
        xaxis_tickformat = "%d %b"
        xaxis_dtick = 86400000  # 1 día en ms
    
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            range=[time_start, time_end],
            title="Fecha y Hora",
            tickformat=xaxis_tickformat,
            dtick=xaxis_dtick,
            tickangle=-45
        ),
        yaxis_title="Velocidad del Viento (m/s)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
        height=280,
        margin=dict(l=40, r=30, t=30, b=60),
    )
    
    return fig


def create_gas_chart(df, variable, ylabel, devices, channels, start_date, end_date):
    """Crea gráfico de serie temporal para gases (NO2 o CO2)."""
    from datetime import timedelta
    
    # Convertir fechas string a datetime para el rango del eje X
    if isinstance(start_date, str):
        time_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=BOGOTA)
    else:
        time_start = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=BOGOTA)
    
    if isinstance(end_date, str):
        time_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=BOGOTA)
    else:
        time_end = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=BOGOTA)
    
    fig = go.Figure()
    
    if df.empty:
        # Configurar formato del eje X según el rango (incluso sin datos)
        days_diff = (time_end - time_start).days
        if days_diff == 0:
            xaxis_config = {"tickformat": "%H:%M", "dtick": 7200000, "tickangle": -45}
        elif days_diff == 1:
            xaxis_config = {"tickformat": "%H:%M<br>%d %b", "dtick": 10800000, "tickangle": -45}
        elif days_diff <= 3:
            xaxis_config = {"tickformat": "%d %b<br>%H:%M", "dtick": 21600000, "tickangle": -45}
        else:
            xaxis_config = {"tickformat": "%d %b", "dtick": 86400000, "tickangle": -45}
        
        fig.update_layout(
            title=f"⚠️ No hay datos de {variable.upper()} disponibles en el rango seleccionado",
            template="plotly_white",
            xaxis=dict(
                range=[time_start, time_end],
                title="Fecha y Hora",
                **xaxis_config
            ),
            annotations=[{
                'text': f'Los sensores actuales no están enviando datos de {variable.upper()}.<br>' +
                        'Verifique que los dispositivos tengan sensores de gases instalados<br>' +
                        'y estén configurados para transmitir estos datos.',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'xanchor': 'center',
                'yanchor': 'middle',
                'showarrow': False,
                'font': {'size': 12, 'color': '#666'}
            }]
        )
        return fig
    
    has_data = False
    
    for device in devices:
        for channel in channels:
            df_subset = df[
                (df['device_id'] == device) & 
                (df['sensor_channel'] == channel)
            ]
            
            if df_subset.empty:
                continue
            
            has_data = True
            color = DEVICE_COLORS.get(device, '#888888')
            dash_style = DASH_BY_UM.get(channel, 'solid')
            
            fig.add_trace(go.Scatter(
                x=df_subset['fechah_local'],
                y=df_subset[variable],
                mode='lines+markers',
                name=f"{label_for(device)} - {channel}",
                line=dict(color=color, dash=dash_style, width=2),
                marker=dict(size=4),
                hovertemplate=(
                    f"<b>{label_for(device)} - {channel}</b><br>" +
                    "Fecha: %{x|%d/%m/%Y %H:%M}<br>" +
                    f"{ylabel}: " + "%{y:.2f}<extra></extra>"
                ),
            ))
    
    # Si no hay datos reales, mostrar mensaje
    if not has_data:
        fig.update_layout(
            title=f"⚠️ No hay datos de {variable.upper()} en el período seleccionado",
            template="plotly_white",
            annotations=[{
                'text': 'No se encontraron mediciones de este gas<br>para los dispositivos y fechas seleccionadas.',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'xanchor': 'center',
                'yanchor': 'middle',
                'showarrow': False,
                'font': {'size': 12, 'color': '#666'}
            }]
        )
        return fig
    
    # Agregar líneas de referencia según el gas
    if variable == 'no2':
        # Límite OMS para NO2: 40 ppb (promedio anual)
        fig.add_hline(
            y=40, 
            line_dash="dash", 
            line_color="orange",
            annotation_text="Límite OMS (40 ppb)",
            annotation_position="right",
        )
        fig.add_hline(
            y=100, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Alto (100 ppb)",
            annotation_position="right",
        )
    elif variable == 'co2':
        # Referencia CO2 interior
        fig.add_hline(
            y=1000, 
            line_dash="dash", 
            line_color="orange",
            annotation_text="Ventilación adecuada (1000 ppm)",
            annotation_position="right",
        )
        fig.add_hline(
            y=2000, 
            line_dash="dash", 
            line_color="red",
            annotation_text="Atención requerida (2000 ppm)",
            annotation_position="right",
        )
    
    # Configurar formato del eje X según el rango
    days_diff = (time_end - time_start).days
    if days_diff == 0:
        # Mismo día: solo horas
        xaxis_tickformat = "%H:%M"
        xaxis_dtick = 7200000  # 2 horas en ms
    elif days_diff == 1:
        # 24 horas: hora prominente
        xaxis_tickformat = "%H:%M<br>%d %b"
        xaxis_dtick = 10800000  # 3 horas en ms
    elif days_diff <= 3:
        # 2-3 días: día + hora
        xaxis_tickformat = "%d %b<br>%H:%M"
        xaxis_dtick = 21600000  # 6 horas en ms
    else:
        # Más días: solo fecha
        xaxis_tickformat = "%d %b"
        xaxis_dtick = 86400000  # 1 día en ms
    
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(
            range=[time_start, time_end],
            title="Fecha y Hora",
            tickformat=xaxis_tickformat,
            dtick=xaxis_dtick,
            tickangle=-45
        ),
        yaxis_title=ylabel,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.20,
            xanchor="center",
            x=0.5,
        ),
        height=280,
        margin=dict(l=40, r=30, t=30, b=60),
    )
    
    return fig


def create_stats_summary(df, variables):
    """Crea resumen estadístico de las variables."""
    stats_cards = []
    
    variable_config = {
        'no2': ('NO2', 'ppb', '🏭'),
        'co2': ('CO2', 'ppm', '🌫️'),
        'vel_viento': ('Velocidad Viento', 'm/s', '💨'),
    }
    
    for var in variables:
        if var not in variable_config:
            continue
        
        name, unit, icon = variable_config[var]
        
        df_var = df[df[var].notna()]
        if df_var.empty:
            continue
        
        mean_val = df_var[var].mean()
        min_val = df_var[var].min()
        max_val = df_var[var].max()
        count = len(df_var)
        
        stats_cards.append(
            html.Div(
                className="stat-card",
                children=[
                    html.Div(icon, className="stat-icon"),
                    html.Div(
                        children=[
                            html.H4(name, className="stat-title"),
                            html.P(f"Promedio: {mean_val:.2f} {unit}", className="stat-value"),
                            html.P(f"Min: {min_val:.2f} | Max: {max_val:.2f} {unit}", className="stat-range"),
                            html.P(f"Registros: {count:,}", className="stat-count"),
                        ],
                        className="stat-content",
                    ),
                ],
            )
        )
    
    return html.Div(stats_cards, className="stats-grid")


def register_reset_callback(app):
    """Registra callback para restablecer filtros."""
    from datetime import datetime, timedelta
    from src.utils.constants import BOGOTA
    
    @app.callback(
        [
            Output("ddl-devices-wind", "value"),
            Output("chk-variables-wind", "value"),
            Output("date-picker-wind", "start_date"),
            Output("date-picker-wind", "end_date"),
        ],
        Input("btn-reset-wind", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_wind_filters(n_clicks):
        """Restablece todos los filtros a valores por defecto."""
        # Dispositivos: todos
        all_devices = [f"S{i}_PMTHVD" for i in range(1, 7)]
        
        # Variables: todas
        all_variables = ["no2", "co2", "vel_viento"]
        
        # Fechas: últimas 24 horas
        today_dt = datetime.now(BOGOTA)
        today = today_dt.strftime("%Y-%m-%d")
        start_default = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")
        
        return all_devices, all_variables, start_default, today
