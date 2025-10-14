"""
Script para identificar y limpiar datos duplicados en la base de datos.

Uso:
    python scripts/fix_duplicates.py --check     # Solo revisar
    python scripts/fix_duplicates.py --fix       # Limpiar duplicados
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from sqlalchemy import func, and_

from src.main import create_app
from src.core.database import db
from src.core.models import Measurement


@click.command()
@click.option("--check", is_flag=True, help="Solo revisar duplicados sin eliminar")
@click.option("--fix", is_flag=True, help="Eliminar duplicados, mantener el más reciente")
def main(check: bool, fix: bool):
    """Identifica y opcionalmente elimina duplicados."""
    click.echo("=" * 60)
    click.echo("🔍 Buscando Duplicados en Mediciones")
    click.echo("=" * 60)

    app = create_app()
    
    with app.app_context():
        # Encontrar duplicados
        duplicates = (
            db.session.query(
                Measurement.device_id,
                Measurement.sensor_channel,
                Measurement.fechah_local,
                func.count(Measurement.id).label("count"),
                func.max(Measurement.id).label("keep_id")
            )
            .group_by(
                Measurement.device_id,
                Measurement.sensor_channel,
                Measurement.fechah_local
            )
            .having(func.count(Measurement.id) > 1)
            .all()
        )

        if not duplicates:
            click.echo("✓ No se encontraron duplicados")
            return

        click.echo(f"⚠️  Encontrados {len(duplicates)} grupos de duplicados")
        
        total_to_delete = 0
        for dup in duplicates:
            count = dup.count
            total_to_delete += (count - 1)
            click.echo(f"  - {dup.device_id} / {dup.sensor_channel.name} / {dup.fechah_local}: {count} copias")

        click.echo(f"\nTotal de registros duplicados a eliminar: {total_to_delete}")

        if check:
            click.echo("\n✓ Modo --check: No se eliminó nada")
            return

        if fix:
            click.echo("\n🔧 Eliminando duplicados...")
            deleted = 0
            
            for dup in duplicates:
                # Eliminar todos excepto el más reciente (mayor ID)
                to_delete = (
                    db.session.query(Measurement)
                    .filter(
                        and_(
                            Measurement.device_id == dup.device_id,
                            Measurement.sensor_channel == dup.sensor_channel,
                            Measurement.fechah_local == dup.fechah_local,
                            Measurement.id != dup.keep_id
                        )
                    )
                    .all()
                )
                
                for record in to_delete:
                    db.session.delete(record)
                    deleted += 1

            db.session.commit()
            click.echo(f"✓ Eliminados {deleted} registros duplicados")
        else:
            click.echo("\n💡 Usa --fix para eliminar los duplicados")
            click.echo("   O --check para solo revisar sin cambios")


if __name__ == "__main__":
    main()
