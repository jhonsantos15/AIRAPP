import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Cargar .env lo antes posible
load_dotenv()

from flask import Flask, jsonify, request, render_template, send_file
from flask_migrate import Migrate

from db import db, init_engine_and_session
from models import Measurement, SensorChannel
from dashboards.layout import build_layout
from dashboards.callbacks import register_callbacks
from reports import generate_pdf_report
from reports_excel import generate_excel_report

# -------- Constantes --------
BOGOTA = ZoneInfo("America/Bogota")

# Ruta absoluta y estable a la DB en ./instance/aireapp.db
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DEFAULT_DB_URI = f"sqlite:///{os.path.join(INSTANCE_DIR, 'aireapp.db')}"


def _parse_vars(q_vars: str):
    raw = [v.strip().lower() for v in (q_vars or "").split(",")]
    valid = {"pm25", "pm10", "temp", "rh"}
    return [v for v in raw if v in valid] or ["pm25", "pm10", "temp", "rh"]


def _parse_devices(q_devices: str | None):
    if not q_devices:
        return None
    return [d.strip() for d in q_devices.split(",") if d.strip()]


def _parse_channels(q_channel: str | None):
    if not q_channel:
        return [SensorChannel.Um1, SensorChannel.Um2]
    q = q_channel.strip().lower()
    if q in ("um1", "sensor1", "s1"):
        return [SensorChannel.Um1]
    if q in ("um2", "sensor2", "s2"):
        return [SensorChannel.Um2]
    return [SensorChannel.Um1, SensorChannel.Um2]


def _bounds_of_day_local(d: date):
    start_local = datetime.combine(d, time(0, 0, 0)).replace(tzinfo=BOGOTA)
    end_local = datetime.combine(d, time(23, 59, 59)).replace(tzinfo=BOGOTA)
    return start_local, end_local


def _bounds_of_range_local(dstart: date, dend: date):
    a, _ = _bounds_of_day_local(dstart)
    _, b = _bounds_of_day_local(dend)
    return a, b


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # DB estable en instance/aireapp.db (se puede sobrescribir con DATABASE_URL)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", DEFAULT_DB_URI)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambie_esto")
    app.config["JSON_SORT_KEYS"] = False

    db.init_app(app)
    Migrate(app, db)
    with app.app_context():
        init_engine_and_session()
        db.create_all()

    # Logging a archivo
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler("logs/aireapp.log", maxBytes=2_000_000, backupCount=3)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    app.logger.info("AireApp iniciado")
    app.logger.info(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    @app.route("/")
    def index():
        return render_template("index.html")

    # ------------------ API: Día actual / día elegido (ya existente) ------------------ #
    @app.get("/api/series")
    def api_series():
        """
        Devuelve puntos del DÍA seleccionado (00:00–23:59, America/Bogota).
        Params:
          - device_id: CSV opcional
          - sensor_channel: um1 | um2 | ambos
          - vars: pm25,pm10,temp,rh (CSV)
          - date: YYYY-MM-DD (default hoy)
        """
        q_devices = request.args.get("device_id", "").strip()
        q_channel = request.args.get("sensor_channel", "ambos").strip()
        q_vars = request.args.get("vars", "pm25,pm10,temp,rh").strip().lower()
        q_date = request.args.get("date")

        variables = set(_parse_vars(q_vars))

        if q_date:
            try:
                sel_day = datetime.strptime(q_date, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "date debe ser yyyy-mm-dd"}), 400
        else:
            sel_day = datetime.now(BOGOTA).date()

        day_start, day_end = _bounds_of_day_local(sel_day)

        devices = _parse_devices(q_devices)
        channels = _parse_channels(q_channel)

        qry = Measurement.query.filter(
            Measurement.fechah_local >= day_start,
            Measurement.fechah_local <= day_end,
            Measurement.sensor_channel.in_(channels),
        )
        if devices:
            qry = qry.filter(Measurement.device_id.in_(devices))

        rows = qry.order_by(Measurement.fechah_local.asc()).all()

        def pick(valname, row):
            return getattr(row, valname) if valname in {"pm25", "pm10", "temp", "rh"} else None

        payload = []
        for r in rows:
            item = {
                "ts": r.fechah_local.isoformat(),
                "device_id": r.device_id,
                "Um": r.sensor_channel.name,
            }
            for v in variables:
                item[v] = pick(v, r)
            payload.append(item)

        app.logger.info(f"/api/series -> day={sel_day} points={len(payload)}")
        return jsonify({"tz": "America/Bogota", "points": payload})

    # ------------------ API NUEVA: Rango de fechas (multi-día) ------------------ #
    @app.get("/api/series/range")
    def api_series_range():
        """
        Devuelve puntos entre start..end (INCLUSIVO) en hora local America/Bogota.
        Útil para ver históricos multi-día desde Dash.
        Params:
          - start: YYYY-MM-DD (requerido)
          - end:   YYYY-MM-DD (requerido)
          - device_id: CSV opcional
          - sensor_channel: um1 | um2 | ambos
          - vars: pm25,pm10,temp,rh (CSV)
          - agg:  'none' | '1min'  -> si '1min', promedia por minuto por device+Um
        Respuesta (si agg='none' o '1min'): {"tz": "...", "points": [ {ts, device_id, Um, pm25?...}, ... ]}
        """
        start_s = request.args.get("start")
        end_s = request.args.get("end")
        if not start_s or not end_s:
            return jsonify({"error": "start y end son requeridos (YYYY-MM-DD)"}), 400

        try:
            d_start = datetime.strptime(start_s, "%Y-%m-%d").date()
            d_end = datetime.strptime(end_s, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "formato de fecha inválido (YYYY-MM-DD)"}), 400

        if d_end < d_start:
            return jsonify({"error": "end debe ser >= start"}), 400

        q_devices = request.args.get("device_id", "").strip()
        q_channel = request.args.get("sensor_channel", "ambos").strip()
        q_vars = request.args.get("vars", "pm25,pm10,temp,rh").strip().lower()
        agg = (request.args.get("agg") or "none").lower()

        variables = _parse_vars(q_vars)
        devices = _parse_devices(q_devices)
        channels = _parse_channels(q_channel)

        start_local, end_local = _bounds_of_range_local(d_start, d_end)

        qry = Measurement.query.filter(
            Measurement.fechah_local >= start_local,
            Measurement.fechah_local <= end_local,
            Measurement.sensor_channel.in_(channels),
        )
        if devices:
            qry = qry.filter(Measurement.device_id.in_(devices))

        rows = qry.order_by(Measurement.fechah_local.asc()).all()
        app.logger.info(
            f"/api/series/range -> {start_s}..{end_s} devs={devices or 'ALL'} ch={','.join([c.name for c in channels])} rows={len(rows)} agg={agg}"
        )

        # --- Sin agregación: devolver tal cual (mismo formato que /api/series) ---
        if agg == "none":
            payload = []
            for r in rows:
                item = {
                    "ts": r.fechah_local.isoformat(),
                    "device_id": r.device_id,
                    "Um": r.sensor_channel.name,
                }
                for v in variables:
                    item[v] = getattr(r, v, None)
                payload.append(item)
            return jsonify({"tz": "America/Bogota", "points": payload})

        # --- Con agregación por minuto: pandas resample 1min por device+Um ---
        if agg == "1min":
            try:
                import pandas as pd
            except Exception:
                return jsonify({"error": "pandas requerido para agg=1min"}), 500

            if not rows:
                # Devolver esqueleto vacío con marcas cada minuto
                idx = pd.date_range(start_local, end_local, freq="1min", tz=BOGOTA)
                payload = []
                for ts in idx.to_pydatetime():
                    payload.append({"ts": ts.isoformat(), "device_id": None, "Um": None})
                return jsonify({"tz": "America/Bogota", "points": payload})

            # Construir DataFrame
            recs = []
            for r in rows:
                recs.append(
                    {
                        "ts": r.fechah_local,  # YA está en hora local
                        "device_id": r.device_id,
                        "Um": r.sensor_channel.name,
                        "pm25": getattr(r, "pm25", None),
                        "pm10": getattr(r, "pm10", None),
                        "temp": getattr(r, "temp", None),
                        "rh": getattr(r, "rh", None),
                    }
                )
            df = pd.DataFrame(recs)
            df["ts"] = pd.to_datetime(df["ts"])
            df = df.set_index("ts").sort_index()

            # Reindex min a min por rango solicitado para cada (device_id, Um)
            idx = pd.date_range(start_local, end_local, freq="1min", tz=BOGOTA)

            out_rows = []
            for (dev, um), g in df.groupby(["device_id", "Um"]):
                g1 = (
                    g[list(variables)]
                    .resample("1min")
                    .mean()
                    .reindex(idx)
                )
                for ts, row in g1.iterrows():
                    item = {"ts": ts.isoformat(), "device_id": dev, "Um": um}
                    for v in variables:
                        val = row.get(v, None)
                        if val is not None and isinstance(val, float):
                            # redondeo suave
                            item[v] = round(val, 3)
                        else:
                            item[v] = None if pd.isna(val) else val
                    out_rows.append(item)

            return jsonify({"tz": "America/Bogota", "points": out_rows})

        return jsonify({"error": "agg debe ser 'none' o '1min'"}), 400

    # ------------------ API: Descargar reportes en PDF ------------------ #
    @app.get("/api/reports/pdf")
    def api_reports_pdf():
        """
        Genera y descarga un reporte en PDF.
        Params:
          - period: 'hour' | '24hours' | '7days' | 'year' | 'custom'
          - device_id: CSV opcional (ej: S1_PMTHVD,S2_PMTHVD)
          - sensor_channel: 'um1' | 'um2' | 'ambos' (default: ambos)
          - start_date: YYYY-MM-DD (requerido si period=custom)
          - end_date: YYYY-MM-DD (requerido si period=custom)
        """
        period = request.args.get("period", "24hours").strip().lower()
        q_devices = request.args.get("device_id", "").strip()
        q_channel = request.args.get("sensor_channel", "ambos").strip()
        
        devices = _parse_devices(q_devices)
        channels = _parse_channels(q_channel)
        
        start_date = None
        end_date = None
        
        if period == "custom":
            start_s = request.args.get("start_date")
            end_s = request.args.get("end_date")
            if not start_s or not end_s:
                return jsonify({"error": "start_date y end_date son requeridos para period=custom"}), 400
            try:
                start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "formato de fecha inválido (YYYY-MM-DD)"}), 400
        
        try:
            pdf_buffer = generate_pdf_report(
                period=period,
                devices=devices,
                start_date=start_date,
                end_date=end_date,
                channels=channels
            )
            
            # Generar nombre de archivo
            timestamp = datetime.now(BOGOTA).strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_calidad_aire_{period}_{timestamp}.pdf"
            
            app.logger.info(f"Reporte PDF generado: {filename}")
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Error generando reporte PDF: {e}", exc_info=True)
            return jsonify({"error": f"Error generando reporte: {str(e)}"}), 500

    # ------------------ API: Descargar reportes en Excel (MINUTO A MINUTO) ------------------ #
    @app.get("/api/reports/excel")
    def api_reports_excel():
        """
        Genera y descarga un reporte en Excel con TODOS los datos minuto a minuto.
        Params:
          - period: 'hour' | '24hours' | 'month' | '7days' | 'year' | 'custom'
          - device_id: CSV opcional (ej: S1_PMTHVD,S2_PMTHVD)
          - sensor_channel: 'um1' | 'um2' | 'ambos' (default: ambos)
          - start_date: YYYY-MM-DD (requerido si period=custom)
          - end_date: YYYY-MM-DD (requerido si period=custom)
          - aggregate: 'true' | 'false' (default: true) - Agregar por minuto o datos crudos
        """
        period = request.args.get("period", "24hours").strip().lower()
        q_devices = request.args.get("device_id", "").strip()
        q_channel = request.args.get("sensor_channel", "ambos").strip()
        aggregate = request.args.get("aggregate", "true").strip().lower() == "true"
        
        devices = _parse_devices(q_devices)
        channels = _parse_channels(q_channel)
        
        start_date = None
        end_date = None
        
        if period == "custom":
            start_s = request.args.get("start_date")
            end_s = request.args.get("end_date")
            if not start_s or not end_s:
                return jsonify({"error": "start_date y end_date son requeridos para period=custom"}), 400
            try:
                start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "formato de fecha inválido (YYYY-MM-DD)"}), 400
        
        try:
            excel_buffer = generate_excel_report(
                period=period,
                devices=devices,
                start_date=start_date,
                end_date=end_date,
                channels=channels,
                aggregate_by_minute=aggregate
            )
            
            # Generar nombre de archivo
            timestamp = datetime.now(BOGOTA).strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_calidad_aire_{period}_{timestamp}.xlsx"
            
            app.logger.info(f"Reporte Excel generado: {filename}")
            
            return send_file(
                excel_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Error generando reporte Excel: {e}", exc_info=True)
            return jsonify({"error": f"Error generando reporte: {str(e)}"}), 500

    # ------------------ Dash (tu app actual) ------------------ #
    from dash import Dash
    dash_app = Dash(
        __name__,
        server=app,
        url_base_pathname="/dash/",
        title="Calidad del Aire – Sensores Bajo Costo",
        suppress_callback_exceptions=True,
        assets_folder="static",
    )
    dash_app.layout = build_layout(app)
    register_callbacks(dash_app, app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
