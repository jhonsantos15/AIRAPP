#!/usr/bin/env python
"""
Monitor de ingesta en tiempo real
Muestra estadísticas cada 10 segundos de los datos que van llegando
"""
import time
from datetime import datetime
from app import create_app
from db import db
from models import Measurement
from sqlalchemy import func

def monitor():
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("MONITOR DE INGESTA EN TIEMPO REAL")
        print("="*80)
        print("Presiona Ctrl+C para detener\n")
        
        # Obtener conteo inicial
        prev_count = db.session.query(func.count(Measurement.id)).scalar()
        prev_time = time.time()
        
        print(f"Conteo inicial: {prev_count} registros")
        print(f"Esperando nuevos datos...\n")
        
        try:
            while True:
                time.sleep(10)  # Esperar 10 segundos
                
                # Conteo actual
                curr_count = db.session.query(func.count(Measurement.id)).scalar()
                curr_time = time.time()
                
                # Calcular diferencia
                new_records = curr_count - prev_count
                elapsed = curr_time - prev_time
                rate = new_records / elapsed if elapsed > 0 else 0
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if new_records > 0:
                    print(f"✅ [{now}] +{new_records} nuevos registros ({rate:.1f} msg/s)")
                    
                    # Mostrar últimos datos por dispositivo
                    last_by_device = db.session.query(
                        Measurement.device_id,
                        func.max(Measurement.fechah_local).label('last_time')
                    ).group_by(Measurement.device_id).all()
                    
                    for device, last_time in last_by_device:
                        if last_time:
                            print(f"   {device}: {last_time}")
                else:
                    print(f"⏳ [{now}] Sin nuevos datos (total: {curr_count})")
                
                prev_count = curr_count
                prev_time = curr_time
                
        except KeyboardInterrupt:
            print("\n\n" + "="*80)
            print("Monitor detenido por usuario")
            print("="*80)

if __name__ == "__main__":
    monitor()
