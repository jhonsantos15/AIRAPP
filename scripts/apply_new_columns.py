"""
Script para aplicar directamente las nuevas columnas a la base de datos.
Útil cuando la tabla ya existe y solo necesitamos agregar columnas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from sqlalchemy import text
from src.main import create_app
from src.core.database import db


def check_column_exists(column_name: str) -> bool:
    """Verifica si una columna existe en la tabla measurements."""
    query = text("""
        SELECT COUNT(*) as count
        FROM pragma_table_info('measurements')
        WHERE name = :column_name
    """)
    result = db.session.execute(query, {"column_name": column_name}).fetchone()
    return result[0] > 0


@click.command()
def main():
    """Agrega las nuevas columnas directamente a la base de datos."""
    click.echo("=" * 80)
    click.echo("🔧 Aplicando nuevas columnas a la base de datos")
    click.echo("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        columns_to_add = [
            ("no2", "FLOAT"),
            ("co2", "FLOAT"),
            ("vel_viento", "FLOAT"),
            ("dir_viento", "FLOAT"),
        ]
        
        added_count = 0
        skipped_count = 0
        
        for column_name, column_type in columns_to_add:
            if check_column_exists(column_name):
                click.echo(f"  ⏭️  Columna '{column_name}' ya existe, omitiendo...")
                skipped_count += 1
                continue
            
            try:
                sql = f"ALTER TABLE measurements ADD COLUMN {column_name} {column_type}"
                db.session.execute(text(sql))
                db.session.commit()
                click.echo(f"  ✅ Columna '{column_name}' agregada exitosamente")
                added_count += 1
            except Exception as e:
                click.echo(f"  ❌ Error al agregar '{column_name}': {e}")
                db.session.rollback()
        
        click.echo("\n" + "=" * 80)
        click.echo(f"📊 Resumen:")
        click.echo(f"  ✅ Columnas agregadas: {added_count}")
        click.echo(f"  ⏭️  Columnas omitidas: {skipped_count}")
        click.echo("=" * 80)
        
        if added_count > 0:
            click.echo("\n✨ Base de datos actualizada exitosamente")
            click.echo("\n📝 Próximos pasos:")
            click.echo("  1. Ejecuta: python scripts/verify_new_variables.py")
            click.echo("  2. Reinicia el IoT Consumer")
            click.echo("  3. Verifica que los datos se estén guardando correctamente")
        else:
            click.echo("\nℹ️  No se agregaron nuevas columnas (ya existían)")


if __name__ == "__main__":
    main()
