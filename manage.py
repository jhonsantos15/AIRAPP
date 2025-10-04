#!/usr/bin/env python
from __future__ import annotations
import os
import sys
import click
from dotenv import load_dotenv, find_dotenv

# Carga variables de entorno desde .env (sin sobrescribir las ya definidas)
load_dotenv(find_dotenv(), override=False)

# Importes locales
from ingest import consume  # servicio de ingesta
from app import create_app  # fábrica de Flask/Dash


@click.group()
def cli():
    """Herramientas de la app."""
    pass


# ---------------------------------------------------------------------
# runserver: levanta el servidor Flask (con Dash montado)
# ---------------------------------------------------------------------
@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Host de escucha")
@click.option("--port", default=5000, show_default=True, help="Puerto de escucha")
@click.option("--debug/--no-debug", default=False, show_default=True, help="Modo debug")
def runserver(host: str, port: int, debug: bool):
    """Inicia el servidor web (Flask + Dash)."""
    app = create_app()
    app.run(host=host, port=port, debug=debug)


# ---------------------------------------------------------------------
# ingest: consume desde IoT Hub (compat. Event Hub)
# ---------------------------------------------------------------------
@cli.command()
@click.option(
    "--cg",
    "groups_csv",
    required=True,
    help="Consumer groups separados por coma. Ej: 'asa-s6' o 'asa-s1,asa-s2'",
)
@click.option(
    "--from",
    "from_pos",
    type=click.Choice(["earliest", "latest"]),  # si luego quieres permitir fecha, cambia esto
    default="earliest",
    show_default=True,
    help="Posición inicial: 'earliest' (histórico) o 'latest' (solo nuevos).",
)
def ingest(groups_csv: str, from_pos: str):
    """
    Inicia el consumidor de Event Hub compatible con IoT Hub.
    Ejemplos:
      python manage.py ingest --cg asa-s6
      python manage.py ingest --cg asa-s1,asa-s2 --from latest
    """
    # Normaliza grupos (permite coma y espacios)
    groups = [g.strip() for g in groups_csv.split(",") if g.strip()]

    # >>> IMPORTANTE: pasar el valor TAL CUAL ('earliest' | 'latest') <<<
    consume(groups, start_position=from_pos)


# ---------------------------------------------------------------------
# inspect: imprime resumen rápido de la base (rango fechas, conteos)
# ---------------------------------------------------------------------
@cli.command()
def inspect():
    """Muestra un resumen de los datos en la base local."""
    from sqlalchemy import select, func
    from db import db
    from models import Measurement

    app = create_app()
    with app.app_context():
        mn, mx = db.session.execute(
            select(func.min(Measurement.fechah_local), func.max(Measurement.fechah_local))
        ).one()
        click.echo("Rango de fechah_local (America/Bogota):")
        click.echo(f"  min: {mn}")
        click.echo(f"  max: {mx}")

        click.echo("\nConteo por dispositivo y canal:")
        rows = db.session.execute(
            select(Measurement.device_id, Measurement.sensor_channel, func.count())
            .group_by(Measurement.device_id, Measurement.sensor_channel)
            .order_by(Measurement.device_id, Measurement.sensor_channel)
        ).all()
        for device_id, channel, cnt in rows:
            click.echo(f"  {device_id} {channel} {cnt}")

        click.echo("\nConteo por día:")
        rows = db.session.execute(
            select(func.date(Measurement.fechah_local), func.count())
            .group_by(func.date(Measurement.fechah_local))
            .order_by(func.date(Measurement.fechah_local))
        ).all()
        for day, cnt in rows:
            click.echo(f"  {day} {cnt}")


# ---------------------------------------------------------------------
# seed: pobla datos sintéticos (si existe seed.py)
# ---------------------------------------------------------------------
@cli.command()
@click.option(
    "--date",
    "seed_date",
    default=None,
    help="Fecha AAAA-MM-DD para generar datos (por defecto, hoy en America/Bogota).",
)
def seed(seed_date: str | None):
    """Genera datos sintéticos para pruebas (usa seed.py si está disponible)."""
    try:
        import seed as seed_mod  # type: ignore
    except Exception:
        click.echo("No se encontró seed.py; omitiendo.")
        sys.exit(0)
    # Si seed.py expone una función main, la usamos; si no, intentamos run(seed_date)
    if hasattr(seed_mod, "main"):
        seed_mod.main(seed_date)  # type: ignore[attr-defined]
    elif hasattr(seed_mod, "run"):
        seed_mod.run(seed_date)  # type: ignore[attr-defined]
    else:
        click.echo("seed.py no expone main() ni run(); nada que ejecutar.")


# ---------------------------------------------------------------------
if __name__ == "__main__":
    cli()
