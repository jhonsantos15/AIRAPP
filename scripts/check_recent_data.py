"""
Script para verificar datos recientes en la base de datos.

Uso:
    python scripts/check_recent_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from datetime import datetime, timedelta

from src.main import create_app
from src.core.database import db
from src.core.models import Measurement
from src.utils.constants import BOGOTA


@click.command()
@click.option("--minutes", default=60, type=int, help="Minutos hacia atrás a revisar")
def main(minutes: int):
    """Muestra las últimas mediciones recibidas."""
    click.echo("=" * 80)
    click.echo("🔍 Verificando Datos Recientes")
    click.echo("=" * 80)

    app = create_app()
    
    with app.app_context():
        # Últimas N mediciones
        latest = (
            db.session.query(Measurement)
            .order_by(Measurement.fechah_local.desc())
            .limit(10)
            .all()
        )

        if not latest:
            click.echo("⚠️  No hay datos en la base de datos")
            return

        click.echo(f"\n📊 Últimas 10 mediciones:")
        click.echo("-" * 80)
        for m in latest:
            click.echo(f"  {m.fechah_local} | {m.device_id:12} | {m.sensor_channel.name:4} | "
                      f"PM2.5: {m.pm25:5.1f} | PM10: {m.pm10:5.1f}")

        # Mediciones en la última hora
        cutoff = datetime.now(BOGOTA) - timedelta(minutes=minutes)
        recent = (
            db.session.query(Measurement)
            .filter(Measurement.fechah_local >= cutoff)
            .count()
        )

        click.echo(f"\n📈 Mediciones en los últimos {minutes} minutos: {recent}")

        # Última medición por dispositivo
        click.echo(f"\n🔌 Última medición por dispositivo:")
        click.echo("-" * 80)
        
        devices = db.session.query(Measurement.device_id).distinct().all()
        for (device_id,) in devices:
            last_measurement = (
                db.session.query(Measurement)
                .filter(Measurement.device_id == device_id)
                .order_by(Measurement.fechah_local.desc())
                .first()
            )
            
            if last_measurement:
                now = datetime.now(BOGOTA)
                last_time = last_measurement.fechah_local
                # Asegurar que ambos sean aware
                if last_time.tzinfo is None:
                    from zoneinfo import ZoneInfo
                    last_time = last_time.replace(tzinfo=ZoneInfo("America/Bogota"))
                
                time_diff = now - last_time
                minutes_ago = int(time_diff.total_seconds() / 60)
                
                status = "🟢" if minutes_ago < 5 else "🟡" if minutes_ago < 30 else "🔴"
                click.echo(f"  {status} {device_id:12} | {last_measurement.fechah_local} "
                          f"({minutes_ago} min atrás)")

        click.echo("=" * 80)


if __name__ == "__main__":
    main()
