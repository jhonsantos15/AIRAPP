"""
Main application entry point.
Refactored Flask application using new modular structure.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, jsonify, request, render_template, send_file, redirect
from flask_migrate import Migrate
from dash import Dash

from src.core.config import settings
from src.core.database import db, init_engine_and_session
from src.core.models import Measurement, SensorChannel
from src.utils.constants import BOGOTA
from src.utils.labels import get_all_devices
from src.dashboard.layout import build_layout
from src.dashboard.callbacks import register_callbacks
from src.services.report_service_legacy import generate_pdf_report
from src.services.report_excel_legacy import generate_excel_report


def _parse_vars(q_vars: str) -> list[str]:
    """Parse and validate variables from query string."""
    raw = [v.strip().lower() for v in (q_vars or "").split(",")]
    valid = {"pm25", "pm10", "temp", "rh"}
    return [v for v in raw if v in valid] or ["pm25", "pm10", "temp", "rh"]


def _parse_devices(q_devices: str | None) -> list[str] | None:
    """Parse device IDs from query string."""
    if not q_devices:
        return None
    return [d.strip() for d in q_devices.split(",") if d.strip()]


def _parse_channels(q_channel: str | None) -> list[SensorChannel]:
    """Parse sensor channels from query string."""
    if not q_channel:
        return [SensorChannel.Um1, SensorChannel.Um2]
    q = q_channel.strip().lower()
    if q in ("um1", "sensor1", "s1"):
        return [SensorChannel.Um1]
    if q in ("um2", "sensor2", "s2"):
        return [SensorChannel.Um2]
    return [SensorChannel.Um1, SensorChannel.Um2]


def _bounds_of_day_local(d: date) -> tuple[datetime, datetime]:
    """Get start and end datetime bounds for a date in Bogota timezone."""
    start_local = datetime.combine(d, time(0, 0, 0)).replace(tzinfo=BOGOTA)
    end_local = datetime.combine(d, time(23, 59, 59)).replace(tzinfo=BOGOTA)
    return start_local, end_local


def _bounds_of_range_local(dstart: date, dend: date) -> tuple[datetime, datetime]:
    """Get start and end datetime bounds for a date range in Bogota timezone."""
    a, _ = _bounds_of_day_local(dstart)
    _, b = _bounds_of_day_local(dend)
    return a, b


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    # Extract directory from log file path
    log_dir = os.path.dirname(settings.log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count
    )
    
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.log_level))
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, settings.log_level))
    
    app.logger.info(f"{settings.app_name} iniciado")
    app.logger.info(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")


def create_app() -> Flask:
    """
    Application factory.
    Creates and configures the Flask application.
    """
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates"
    )

    # Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambie_esto")
    app.config["JSON_SORT_KEYS"] = False

    # Initialize database
    db.init_app(app)
    Migrate(app, db)
    
    with app.app_context():
        init_engine_and_session()
        db.create_all()

    # Setup logging
    setup_logging(app)

    # ==================== ROUTES ==================== #

    @app.route("/")
    def index():
        """Home page - redirect to dashboard."""
        return redirect("/dash/")

    @app.route("/health")
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(BOGOTA).isoformat(),
            "version": "1.0.0"
        })

    # ==================== API ENDPOINTS ==================== #

    @app.get("/api/series")
    def api_series():
        """
        Get measurements for a specific day.
        
        Query Parameters:
            device_id: CSV of device IDs (optional)
            sensor_channel: um1 | um2 | ambos (default: ambos)
            vars: pm25,pm10,temp,rh (CSV, default: all)
            date: YYYY-MM-DD (default: today)
            
        Returns:
            JSON with timezone and measurement points
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
                return jsonify({"error": "date must be YYYY-MM-DD"}), 400
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

        app.logger.info(f"/api/series -> day={sel_day} points={len(payload)}")
        return jsonify({"tz": "America/Bogota", "points": payload})

    @app.get("/api/series/range")
    def api_series_range():
        """
        Get measurements for a date range.
        
        Query Parameters:
            start: YYYY-MM-DD (required)
            end: YYYY-MM-DD (required)
            device_id: CSV of device IDs (optional)
            sensor_channel: um1 | um2 | ambos (default: ambos)
            vars: pm25,pm10,temp,rh (CSV, default: all)
            agg: none | 1min (default: none)
            
        Returns:
            JSON with timezone and measurement points
        """
        start_s = request.args.get("start")
        end_s = request.args.get("end")
        if not start_s or not end_s:
            return jsonify({"error": "start and end are required (YYYY-MM-DD)"}), 400

        try:
            d_start = datetime.strptime(start_s, "%Y-%m-%d").date()
            d_end = datetime.strptime(end_s, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "invalid date format (YYYY-MM-DD)"}), 400

        if d_end < d_start:
            return jsonify({"error": "end must be >= start"}), 400

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
            f"/api/series/range -> {start_s}..{end_s} devs={devices or 'ALL'} "
            f"ch={','.join([c.name for c in channels])} rows={len(rows)} agg={agg}"
        )

        # No aggregation
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

        # 1-minute aggregation
        if agg == "1min":
            import pandas as pd

            if not rows:
                idx = pd.date_range(start_local, end_local, freq="1min", tz=BOGOTA)
                payload = []
                for ts in idx.to_pydatetime():
                    payload.append({"ts": ts.isoformat(), "device_id": None, "Um": None})
                return jsonify({"tz": "America/Bogota", "points": payload})

            # Build DataFrame
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
            df["ts"] = pd.to_datetime(df["ts"])
            df = df.set_index("ts").sort_index()

            idx = pd.date_range(start_local, end_local, freq="1min", tz=BOGOTA)

            out_rows = []
            for (dev, um), g in df.groupby(["device_id", "Um"]):
                g1 = g[list(variables)].resample("1min").mean().reindex(idx)
                for ts, row in g1.iterrows():
                    item = {"ts": ts.isoformat(), "device_id": dev, "Um": um}
                    for v in variables:
                        val = row.get(v, None)
                        if val is not None and isinstance(val, float):
                            item[v] = round(val, 3)
                        else:
                            item[v] = None if pd.isna(val) else val
                    out_rows.append(item)

            return jsonify({"tz": "America/Bogota", "points": out_rows})

        return jsonify({"error": "agg must be 'none' or '1min'"}), 400

    @app.get("/api/reports/pdf")
    def api_reports_pdf():
        """
        Generate and download PDF report.
        
        Query Parameters:
            period: hour | 24hours | 7days | year | custom
            device_id: CSV of device IDs (optional)
            sensor_channel: um1 | um2 | ambos (default: ambos)
            start_date: YYYY-MM-DD (required if period=custom)
            end_date: YYYY-MM-DD (required if period=custom)
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
                return jsonify({
                    "error": "start_date and end_date required for period=custom"
                }), 400
            try:
                start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "invalid date format (YYYY-MM-DD)"}), 400
        
        try:
            pdf_buffer = generate_pdf_report(
                period=period,
                devices=devices,
                start_date=start_date,
                end_date=end_date,
                channels=channels
            )
            
            timestamp = datetime.now(BOGOTA).strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_calidad_aire_{period}_{timestamp}.pdf"
            
            app.logger.info(f"PDF report generated: {filename}")
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Error generating PDF report: {e}", exc_info=True)
            return jsonify({"error": f"Error generating report: {str(e)}"}), 500

    @app.get("/api/reports/excel")
    def api_reports_excel():
        """
        Generate and download Excel report with minute-by-minute data.
        
        Query Parameters:
            period: hour | 24hours | month | 7days | year | custom
            device_id: CSV of device IDs (optional)
            sensor_channel: um1 | um2 | ambos (default: ambos)
            start_date: YYYY-MM-DD (required if period=custom)
            end_date: YYYY-MM-DD (required if period=custom)
            aggregate: true | false (default: true)
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
                return jsonify({
                    "error": "start_date and end_date required for period=custom"
                }), 400
            try:
                start_date = datetime.strptime(start_s, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_s, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "invalid date format (YYYY-MM-DD)"}), 400
        
        try:
            excel_buffer = generate_excel_report(
                period=period,
                devices=devices,
                start_date=start_date,
                end_date=end_date,
                channels=channels,
                aggregate_by_minute=aggregate
            )
            
            timestamp = datetime.now(BOGOTA).strftime("%Y%m%d_%H%M%S")
            filename = f"reporte_calidad_aire_{period}_{timestamp}.xlsx"
            
            app.logger.info(f"Excel report generated: {filename}")
            
            return send_file(
                excel_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            app.logger.error(f"Error generating Excel report: {e}", exc_info=True)
            return jsonify({"error": f"Error generating report: {str(e)}"}), 500

    # ==================== DASH DASHBOARD ==================== #
    
    dash_app = Dash(
        __name__,
        server=app,
        url_base_pathname="/dash/",
        title="Calidad del Aire – Sensores Bajo Costo",
        suppress_callback_exceptions=True,
        assets_folder=os.path.join(os.path.dirname(__file__), "dashboard", "assets"),
    )
    dash_app.layout = build_layout(app)
    register_callbacks(dash_app, app)

    return app


def main():
    """Main entry point."""
    app = create_app()
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )


if __name__ == "__main__":
    main()
