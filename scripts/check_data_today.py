#!/usr/bin/env python3
"""Script para verificar datos disponibles para una fecha específica."""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import db
from src.core.models import Measurement
from src.main import create_app
from src.utils.constants import BOGOTA

def main():
    app = create_app()
    
    # Fecha a consultar (hoy)
    fecha = "2025-10-14"
    
    with app.app_context():
        # Rango completo del día
        start = datetime.strptime(fecha, "%Y-%m-%d").replace(hour=0, minute=0, second=0, tzinfo=BOGOTA)
        end = datetime.strptime(fecha, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=BOGOTA)
        
        print(f"\n📅 Verificando datos para: {fecha}")
        print(f"   Rango: {start} a {end}\n")
        
        # Consultar datos
        rows = db.session.query(Measurement).filter(
            Measurement.fechah_local >= start,
            Measurement.fechah_local <= end
        ).all()
        
        if not rows:
            print(f"❌ NO hay datos para {fecha}\n")
            return
        
        print(f"✅ Encontrados {len(rows)} registros\n")
        
        # Agrupar por dispositivo
        from collections import defaultdict
        by_device = defaultdict(list)
        for r in rows:
            by_device[r.device_id].append(r)
        
        print("📊 Resumen por dispositivo:\n")
        for device, records in sorted(by_device.items()):
            print(f"  {device}:")
            print(f"    - Total registros: {len(records)}")
            
            # Rango de horas
            times = [r.fechah_local for r in records]
            print(f"    - Hora mínima: {min(times).strftime('%H:%M:%S')}")
            print(f"    - Hora máxima: {max(times).strftime('%H:%M:%S')}")
            
            # Sensores
            sensors = set([r.sensor_channel.name for r in records])
            print(f"    - Sensores: {', '.join(sorted(sensors))}")
            
            # Muestra de datos
            sample = records[0]
            print(f"    - Ejemplo: PM2.5={sample.pm25}, PM10={sample.pm10}, Temp={sample.temp}°C, RH={sample.rh}%")
            print()

if __name__ == "__main__":
    main()
