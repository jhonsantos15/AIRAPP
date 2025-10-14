"""
Script para iniciar la API REST con FastAPI.
Ejecuta el servidor con Uvicorn.

Uso:
    python scripts/start_api.py
    python scripts/start_api.py --host 0.0.0.0 --port 8000 --reload
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
import uvicorn

from src.core.config import settings


@click.command()
@click.option("--host", default="0.0.0.0", help="Host del servidor")
@click.option("--port", default=8000, type=int, help="Puerto del servidor")
@click.option("--reload", is_flag=True, help="Auto-reload en cambios de código")
@click.option("--workers", default=1, type=int, help="Número de workers")
def main(host: str, port: int, reload: bool, workers: int):
    """Inicia el servidor FastAPI con Uvicorn."""
    click.echo("=" * 60)
    click.echo("🚀 Iniciando AireApp API REST (FastAPI)")
    click.echo("=" * 60)
    click.echo(f"Host: {host}")
    click.echo(f"Puerto: {port}")
    click.echo(f"Reload: {'✓' if reload else '✗'}")
    click.echo(f"Workers: {workers}")
    click.echo(f"Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    click.echo("=" * 60)

    uvicorn.run(
        "src.api.main:create_api",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # workers no compatible con reload
        factory=True,
    )


if __name__ == "__main__":
    main()
