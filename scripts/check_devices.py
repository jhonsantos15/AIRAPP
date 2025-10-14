#!/usr/bin/env python3
"""Script temporal para verificar dispositivos en la base de datos."""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import db
from src.core.models import Measurement
from src.main import create_app

def main():
    app = create_app()
    with app.app_context():
        # Consultar dispositivos únicos
        devices = db.session.query(Measurement.device_id).distinct().all()
        device_list = [d[0] for d in devices]
        
        print(f"Total de dispositivos únicos en BD: {len(device_list)}")
        print(f"Dispositivos: {device_list}")
        
        # Contar registros por dispositivo
        from sqlalchemy import func
        counts = db.session.query(
            Measurement.device_id,
            func.count(Measurement.id).label('count')
        ).group_by(Measurement.device_id).all()
        
        print("\nRegistros por dispositivo:")
        for dev, count in counts:
            print(f"  {dev}: {count} registros")

if __name__ == "__main__":
    main()
