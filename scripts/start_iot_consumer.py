"""
Script para iniciar el consumer de IoT Hub.
Consume telemetría de Azure Event Hub e ingesta en la BD.

Uso:
    python scripts/start_iot_consumer.py
    python scripts/start_iot_consumer.py --cg my-consumer-group --from latest
    python scripts/start_iot_consumer.py --cg asa-s4 --from "2024-10-01 00:00:00"
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from dotenv import load_dotenv

load_dotenv()

from src.services.iot_hub_service import IoTHubService
from src.core.config import settings


def parse_allowed_devices() -> set:
    """Parsea ALLOWED_DEVICES desde env."""
    allowed = os.getenv("ALLOWED_DEVICES", "")
    if not allowed.strip():
        return set()
    return {d.strip() for d in allowed.split(",") if d.strip()}


@click.command()
@click.option(
    "--cg",
    "--consumer-group",
    default="$Default",
    help="Consumer Group de Event Hub"
)
@click.option(
    "--from",
    "start_position",
    default="earliest",
    help="Posición de inicio: earliest, latest, o 'YYYY-MM-DD HH:MM:SS'"
)
@click.option(
    "--batch-size",
    default=50,
    type=int,
    help="Tamaño de batch para guardar en BD"
)
@click.option(
    "--checkpoint-interval",
    default=30,
    type=int,
    help="Intervalo en segundos para checkpoints"
)
def main(cg: str, start_position: str, batch_size: int, checkpoint_interval: int):
    """Inicia consumer de IoT Hub para ingesta de telemetría."""
    click.echo("=" * 80)
    click.echo("🌐 Iniciando AireApp IoT Hub Consumer")
    click.echo("=" * 80)
    click.echo(f"Consumer Group: {cg}")
    click.echo(f"Start Position: {start_position}")
    click.echo(f"Batch Size: {batch_size}")
    click.echo(f"Checkpoint Interval: {checkpoint_interval}s")
    
    allowed = parse_allowed_devices()
    if allowed:
        click.echo(f"Allowed Devices: {', '.join(sorted(allowed))}")
    else:
        click.echo("Allowed Devices: TODOS")
    
    click.echo("=" * 80)
    click.echo("Presione Ctrl+C para detener...")
    click.echo()

    # Verificar connection string
    if not os.getenv("EVENTHUB_CONNECTION_STRING"):
        click.echo("❌ ERROR: EVENTHUB_CONNECTION_STRING no está definido en .env")
        sys.exit(1)

    # Iniciar servicio
    try:
        service = IoTHubService(
            consumer_group=cg,
            allowed_devices=allowed if allowed else None,
            batch_size=batch_size,
            checkpoint_interval=checkpoint_interval,
        )
        
        service.start_ingestion(start_position=start_position)
        
    except KeyboardInterrupt:
        click.echo("\n✓ Ingesta detenida por usuario")
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
