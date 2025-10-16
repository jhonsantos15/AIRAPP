"""
Script para verificar datos de NO2 y CO2 en la base de datos.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from src.core.database import db, init_engine_and_session
from src.core.models import Measurement
from src.main import create_app
from src.utils.constants import BOGOTA
from sqlalchemy import func

def main():
    """Verificar datos de gases en la base de datos."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("VERIFICACIÓN DE DATOS NO2 Y CO2")
        print("="*70)
        
        # Contar registros totales
        total = db.session.query(func.count(Measurement.id)).scalar()
        print(f"\n📊 Total de mediciones en BD: {total:,}")
        
        # Contar registros con NO2 y CO2
        with_no2 = db.session.query(func.count(Measurement.id)).filter(
            Measurement.no2.isnot(None)
        ).scalar()
        with_co2 = db.session.query(func.count(Measurement.id)).filter(
            Measurement.co2.isnot(None)
        ).scalar()
        
        print(f"🏭 Registros con NO2: {with_no2:,} ({with_no2/total*100:.1f}%)")
        print(f"🌫️  Registros con CO2: {with_co2:,} ({with_co2/total*100:.1f}%)")
        
        # Por dispositivo
        print("\n" + "-"*70)
        print("DATOS POR DISPOSITIVO")
        print("-"*70)
        
        devices = db.session.query(
            Measurement.device_id,
            func.count(Measurement.id).label('total'),
            func.count(Measurement.no2).label('no2_count'),
            func.count(Measurement.co2).label('co2_count'),
            func.avg(Measurement.no2).label('no2_avg'),
            func.avg(Measurement.co2).label('co2_avg')
        ).group_by(Measurement.device_id).all()
        
        for dev in devices:
            print(f"\n📱 Device: {dev.device_id}")
            print(f"   Total registros: {dev.total:,}")
            print(f"   NO2: {dev.no2_count:,} registros (promedio: {dev.no2_avg:.2f} ppb)" if dev.no2_avg else f"   NO2: {dev.no2_count:,} registros")
            print(f"   CO2: {dev.co2_count:,} registros (promedio: {dev.co2_avg:.2f} ppm)" if dev.co2_avg else f"   CO2: {dev.co2_count:,} registros")
        
        # Últimas mediciones
        print("\n" + "-"*70)
        print("ÚLTIMAS 10 MEDICIONES CON NO2 O CO2")
        print("-"*70)
        
        recent = db.session.query(Measurement).filter(
            (Measurement.no2.isnot(None)) | (Measurement.co2.isnot(None))
        ).order_by(Measurement.fechah_local.desc()).limit(10).all()
        
        if recent:
            for m in recent:
                print(f"\n⏰ {m.fechah_local.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Device: {m.device_id} | Sensor: {m.sensor_channel.name}")
                print(f"   NO2: {m.no2:.2f} ppb" if m.no2 else "   NO2: N/A")
                print(f"   CO2: {m.co2:.2f} ppm" if m.co2 else "   CO2: N/A")
        else:
            print("⚠️  No hay mediciones recientes con NO2 o CO2")
        
        # Verificar datos de hoy
        print("\n" + "-"*70)
        print("DATOS DE HOY")
        print("-"*70)
        
        today_start = datetime.now(BOGOTA).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = db.session.query(func.count(Measurement.id)).filter(
            Measurement.fechah_local >= today_start,
            (Measurement.no2.isnot(None)) | (Measurement.co2.isnot(None))
        ).scalar()
        
        print(f"📅 Mediciones con NO2/CO2 hoy: {today_count:,}")
        
        # Por dispositivo hoy
        today_devices = db.session.query(
            Measurement.device_id,
            func.count(Measurement.no2).label('no2_count'),
            func.count(Measurement.co2).label('co2_count')
        ).filter(
            Measurement.fechah_local >= today_start
        ).group_by(Measurement.device_id).all()
        
        if today_devices:
            for dev in today_devices:
                if dev.no2_count > 0 or dev.co2_count > 0:
                    print(f"   {dev.device_id}: NO2={dev.no2_count}, CO2={dev.co2_count}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    main()
