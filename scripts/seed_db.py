"""
Script para inicializar/seedear la base de datos con datos de prueba.

Uso:
    python scripts/seed_db.py
    python scripts/seed_db.py --count 1000
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from datetime import datetime, timedelta
import random

from src.main import create_app
from src.core.database import db
from src.core.models import Measurement, SensorChannel
from src.utils.constants import BOGOTA
from src.utils.labels import get_all_devices


@click.command()
@click.option("--count", default=100, type=int, help="Número de mediciones a crear por dispositivo")
@click.option("--devices", default=None, help="Device IDs separados por coma (opcional)")
def main(count: int, devices: str):
    """Seedea la base de datos con datos de prueba."""
    click.echo("=" * 60)
    click.echo("🌱 Seeding Base de Datos")
    click.echo("=" * 60)

    app = create_app()
    
    with app.app_context():
        # Obtener dispositivos
        if devices:
            device_list = [d.strip() for d in devices.split(",")]
        else:
            device_list = list(get_all_devices().keys())[:3]  # Primeros 3

        click.echo(f"Dispositivos: {', '.join(device_list)}")
        click.echo(f"Mediciones por dispositivo: {count}")
        click.echo()

        now = datetime.now(BOGOTA)
        measurements = []

        for device_id in device_list:
            click.echo(f"Generando datos para {device_id}...")
            
            for i in range(count):
                timestamp = now - timedelta(minutes=i)
                
                # Um1
                measurements.append(Measurement(
                    device_id=device_id,
                    sensor_channel=SensorChannel.Um1,
                    fechah_local=timestamp,
                    pm25=random.uniform(5, 50),
                    pm10=random.uniform(10, 100),
                    temp=random.uniform(15, 30),
                    rh=random.uniform(30, 80),
                ))
                
                # Um2
                measurements.append(Measurement(
                    device_id=device_id,
                    sensor_channel=SensorChannel.Um2,
                    fechah_local=timestamp,
                    pm25=random.uniform(5, 50),
                    pm10=random.uniform(10, 100),
                    temp=random.uniform(15, 30),
                    rh=random.uniform(30, 80),
                ))

        click.echo(f"\n📝 Insertando {len(measurements)} mediciones...")
        db.session.bulk_save_objects(measurements)
        db.session.commit()
        click.echo("✓ Seed completado exitosamente")


if __name__ == "__main__":
    main()
