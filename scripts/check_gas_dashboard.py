"""
Script para ver muestra de datos NO2/CO2 disponibles para el dashboard.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from src.core.database import db
from src.core.models import Measurement, SensorChannel
from src.main import create_app
from src.utils.constants import BOGOTA
import pandas as pd

def main():
    """Ver datos de NO2/CO2 para dashboard."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("DATOS NO2/CO2 PARA DASHBOARD (ÚLTIMAS 24 HORAS)")
        print("="*80)
        
        # Rango: últimas 24 horas
        end = datetime.now(BOGOTA)
        start = end - timedelta(hours=24)
        
        print(f"\n📅 Rango: {start.strftime('%Y-%m-%d %H:%M')} → {end.strftime('%Y-%m-%d %H:%M')}")
        
        # Todos los dispositivos con datos de gases
        devices = ['S4_PMTHVD', 'S5_PMTHVD', 'S6_PMTHVD']
        channels = [SensorChannel.Um1, SensorChannel.Um2]
        
        for device in devices:
            print(f"\n{'─'*80}")
            print(f"📱 DISPOSITIVO: {device}")
            print(f"{'─'*80}")
            
            for channel in channels:
                rows = db.session.query(Measurement).filter(
                    Measurement.device_id == device,
                    Measurement.sensor_channel == channel,
                    Measurement.fechah_local >= start,
                    Measurement.fechah_local <= end,
                ).order_by(Measurement.fechah_local.desc()).limit(20).all()
                
                if not rows:
                    print(f"\n  🔌 {channel.name}: Sin datos")
                    continue
                
                print(f"\n  🔌 {channel.name}: {len(rows)} registros recientes")
                
                # Contar valores no nulos
                no2_values = [r.no2 for r in rows if r.no2 is not None]
                co2_values = [r.co2 for r in rows if r.co2 is not None]
                
                print(f"     NO2: {len(no2_values)} no-nulos")
                if no2_values:
                    print(f"          Min: {min(no2_values):.2f} ppb")
                    print(f"          Max: {max(no2_values):.2f} ppb")
                    print(f"          Avg: {sum(no2_values)/len(no2_values):.2f} ppb")
                
                print(f"     CO2: {len(co2_values)} no-nulos")
                if co2_values:
                    print(f"          Min: {min(co2_values):.2f} ppm")
                    print(f"          Max: {max(co2_values):.2f} ppm")
                    print(f"          Avg: {sum(co2_values)/len(co2_values):.2f} ppm")
                
                # Mostrar últimas 5 mediciones
                print(f"\n     📊 Últimas 5 mediciones:")
                for r in rows[:5]:
                    ts = r.fechah_local.strftime('%H:%M:%S')
                    no2_str = f"{r.no2:.2f}" if r.no2 is not None else "N/A"
                    co2_str = f"{r.co2:.2f}" if r.co2 is not None else "N/A"
                    print(f"        {ts} → NO2: {no2_str:>8} ppb | CO2: {co2_str:>8} ppm")
        
        print("\n" + "="*80)
        print("RESUMEN GENERAL")
        print("="*80)
        
        # Query total para las 24 horas
        all_data = []
        for device in devices:
            for channel in channels:
                rows = db.session.query(Measurement).filter(
                    Measurement.device_id == device,
                    Measurement.sensor_channel == channel,
                    Measurement.fechah_local >= start,
                    Measurement.fechah_local <= end,
                ).all()
                
                for row in rows:
                    all_data.append({
                        'device_id': row.device_id,
                        'sensor_channel': row.sensor_channel.name,
                        'fechah_local': row.fechah_local,
                        'no2': row.no2,
                        'co2': row.co2,
                    })
        
        if all_data:
            df = pd.DataFrame(all_data)
            print(f"\n📊 Total registros: {len(df)}")
            
            df_no2 = df[df['no2'].notna()]
            df_co2 = df[df['co2'].notna()]
            
            print(f"🏭 Registros con NO2: {len(df_no2)} ({len(df_no2)/len(df)*100:.1f}%)")
            if len(df_no2) > 0:
                print(f"   Rango NO2: {df_no2['no2'].min():.2f} - {df_no2['no2'].max():.2f} ppb")
                print(f"   Promedio: {df_no2['no2'].mean():.2f} ppb")
            
            print(f"🌫️  Registros con CO2: {len(df_co2)} ({len(df_co2)/len(df)*100:.1f}%)")
            if len(df_co2) > 0:
                print(f"   Rango CO2: {df_co2['co2'].min():.2f} - {df_co2['co2'].max():.2f} ppm")
                print(f"   Promedio: {df_co2['co2'].mean():.2f} ppm")
        else:
            print("\n⚠️  No hay datos en las últimas 24 horas")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    main()
