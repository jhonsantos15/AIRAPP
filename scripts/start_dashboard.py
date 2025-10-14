"""
Script para iniciar el Dashboard Dash.
Ejecuta el servidor Flask/Dash.

Uso:
    python scripts/start_dashboard.py
    python scripts/start_dashboard.py --host 0.0.0.0 --port 8050 --debug
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click

from src.main import create_app
from src.core.config import settings


@click.command()
@click.option("--host", default="0.0.0.0", help="Host del servidor")
@click.option("--port", default=8050, type=int, help="Puerto del servidor")
@click.option("--debug", is_flag=True, help="Modo debug")
def main(host: str, port: int, debug: bool):
    """Inicia el Dashboard Dash."""
    click.echo("=" * 60)
    click.echo("📊 Iniciando AireApp Dashboard (Dash)")
    click.echo("=" * 60)
    click.echo(f"Host: {host}")
    click.echo(f"Puerto: {port}")
    click.echo(f"Debug: {'✓' if debug else '✗'}")
    click.echo(f"URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    click.echo("=" * 60)

    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
