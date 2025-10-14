"""
Script para gestión de base de datos.

Uso:
    python scripts/manage_db.py init     # Inicializar DB
    python scripts/manage_db.py migrate  # Crear migración
    python scripts/manage_db.py upgrade  # Aplicar migraciones
    python scripts/manage_db.py stats    # Ver estadísticas
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from flask_migrate import init as migrate_init, migrate, upgrade as migrate_upgrade

from src.main import create_app
from src.core.database import db
from src.core.models import Measurement
from sqlalchemy import func


@click.group()
def cli():
    """Herramientas de gestión de base de datos."""
    pass


@cli.command()
def init():
    """Inicializa la base de datos y migraciones."""
    click.echo("🔧 Inicializando base de datos...")
    app = create_app()
    
    with app.app_context():
        db.create_all()
        click.echo("✓ Base de datos inicializada")
        
        # Inicializar Alembic si no existe
        try:
            migrate_init()
            click.echo("✓ Directorio de migraciones creado")
        except Exception as e:
            click.echo(f"ℹ Migraciones ya inicializadas")


@cli.command()
@click.option("--message", "-m", required=True, help="Mensaje de la migración")
def create_migration(message: str):
    """Crea una nueva migración."""
    click.echo(f"📝 Creando migración: {message}")
    app = create_app()
    
    with app.app_context():
        migrate(message=message)
        click.echo("✓ Migración creada")


@cli.command()
def apply():
    """Aplica migraciones pendientes."""
    click.echo("⬆ Aplicando migraciones...")
    app = create_app()
    
    with app.app_context():
        migrate_upgrade()
        click.echo("✓ Migraciones aplicadas")


@cli.command()
def stats():
    """Muestra estadísticas de la base de datos."""
    app = create_app()
    
    with app.app_context():
        click.echo("=" * 60)
        click.echo("📊 Estadísticas de Base de Datos")
        click.echo("=" * 60)
        
        # Total mediciones
        total = db.session.query(func.count(Measurement.id)).scalar()
        click.echo(f"Total mediciones: {total:,}")
        
        # Por dispositivo
        by_device = db.session.query(
            Measurement.device_id,
            func.count(Measurement.id).label("count")
        ).group_by(Measurement.device_id).all()
        
        click.echo("\nPor dispositivo:")
        for device_id, count in by_device:
            click.echo(f"  {device_id}: {count:,}")
        
        # Rango de fechas
        min_date = db.session.query(func.min(Measurement.fechah_local)).scalar()
        max_date = db.session.query(func.max(Measurement.fechah_local)).scalar()
        
        if min_date and max_date:
            click.echo(f"\nRango temporal:")
            click.echo(f"  Desde: {min_date}")
            click.echo(f"  Hasta: {max_date}")
        
        click.echo("=" * 60)


@cli.command()
@click.confirmation_option(prompt="¿Estás seguro de eliminar TODA la data?")
def clear():
    """Elimina todos los datos (requiere confirmación)."""
    app = create_app()
    
    with app.app_context():
        count = db.session.query(Measurement).delete()
        db.session.commit()
        click.echo(f"✓ {count:,} mediciones eliminadas")


if __name__ == "__main__":
    cli()
