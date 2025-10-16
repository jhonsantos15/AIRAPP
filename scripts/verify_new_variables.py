"""
Script para verificar la implementación de las nuevas variables.
Verifica que los campos existan en el modelo y puedan procesarse correctamente.
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import Measurement
from src.core.database import db
from src.main import create_app


def verify_model_fields():
    """Verifica que los nuevos campos existan en el modelo."""
    print("=" * 80)
    print("🔍 Verificando campos del modelo Measurement")
    print("=" * 80)
    
    expected_fields = ['no2', 'co2', 'vel_viento', 'dir_viento']
    model_columns = [c.name for c in Measurement.__table__.columns]
    
    print("\n✅ Campos existentes en el modelo:")
    for field in expected_fields:
        status = "✓" if field in model_columns else "✗"
        print(f"  {status} {field}")
    
    all_present = all(field in model_columns for field in expected_fields)
    
    if all_present:
        print("\n✅ Todos los campos nuevos están presentes en el modelo")
    else:
        print("\n❌ Faltan algunos campos en el modelo")
        return False
    
    return True


def verify_database_schema():
    """Verifica que las columnas existan en la base de datos."""
    print("\n" + "=" * 80)
    print("🗄️  Verificando esquema de base de datos")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Intentar consultar usando las nuevas columnas
            result = db.session.query(
                Measurement.id,
                Measurement.no2,
                Measurement.co2,
                Measurement.vel_viento,
                Measurement.dir_viento
            ).limit(1).all()
            
            print("\n✅ Las columnas existen en la base de datos")
            print(f"✓ Consulta ejecutada exitosamente")
            
            if result:
                print(f"✓ Se encontraron {len(result)} registro(s)")
            else:
                print("ℹ️  No hay datos aún (esto es normal si no se ha ejecutado el consumer)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error al consultar la base de datos: {e}")
            print("\nℹ️  Esto indica que la migración NO se ha aplicado.")
            print("   Ejecuta: alembic upgrade head")
            return False


def verify_payload_processing():
    """Verifica que el procesamiento de payload funcione correctamente."""
    print("\n" + "=" * 80)
    print("📦 Verificando procesamiento de payload")
    print("=" * 80)
    
    from src.core.models import row_from_payload
    
    # Payload de prueba con las nuevas variables
    test_payload = {
        "DeviceId": "TEST_DEVICE",
        "FechaH": "2025-10-15T10:30:00",
        "Fecha": "2025-10-15",
        "Hora": "10:30:00",
        "temp": 24.5,
        "hr": 65.2,
        "n1025Um1": 12.3,
        "n25100Um1": 18.7,
        "n0310Um1": 45.2,   # NO2
        "n0310Um2": 410.5,  # CO2
        "vel": 3.5,         # Velocidad viento
        "dir": 180.0,       # Dirección viento
        "DOY": 288,
        "W": 1.0
    }
    
    try:
        result = row_from_payload(test_payload)
        
        print("\n✅ Payload procesado exitosamente")
        print("\n📊 Valores extraídos:")
        print(f"  • NO2:          {result.get('no2')}")
        print(f"  • CO2:          {result.get('co2')}")
        print(f"  • Vel. Viento:  {result.get('vel_viento')}")
        print(f"  • Dir. Viento:  {result.get('dir_viento')}")
        
        # Verificar que las nuevas variables estén presentes
        expected_keys = ['no2', 'co2', 'vel_viento', 'dir_viento']
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            print(f"\n❌ Faltan claves en el resultado: {missing_keys}")
            return False
        
        # Verificar que los valores sean correctos
        checks = [
            (result.get('no2') == 45.2, "NO2"),
            (result.get('co2') == 410.5, "CO2"),
            (result.get('vel_viento') == 3.5, "Velocidad viento"),
            (result.get('dir_viento') == 180.0, "Dirección viento"),
        ]
        
        all_correct = True
        for check, name in checks:
            if not check:
                print(f"❌ Valor incorrecto para {name}")
                all_correct = False
        
        if all_correct:
            print("\n✅ Todos los valores son correctos")
        
        return all_correct
        
    except Exception as e:
        print(f"\n❌ Error al procesar payload: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_constants():
    """Verifica que las constantes estén actualizadas."""
    print("\n" + "=" * 80)
    print("📋 Verificando constantes")
    print("=" * 80)
    
    from src.utils.constants import AVAILABLE_VARIABLES
    
    expected_vars = ['no2', 'co2', 'vel_viento', 'dir_viento']
    
    print(f"\n✅ Variables disponibles: {AVAILABLE_VARIABLES}")
    
    all_present = all(var in AVAILABLE_VARIABLES for var in expected_vars)
    
    if all_present:
        print("\n✅ Todas las nuevas variables están en AVAILABLE_VARIABLES")
    else:
        missing = [var for var in expected_vars if var not in AVAILABLE_VARIABLES]
        print(f"\n❌ Faltan variables: {missing}")
    
    return all_present


def main():
    """Ejecuta todas las verificaciones."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "VERIFICACIÓN DE NUEVAS VARIABLES" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = {
        "Modelo": verify_model_fields(),
        "Constantes": verify_constants(),
        "Procesamiento": verify_payload_processing(),
        "Base de Datos": verify_database_schema(),
    }
    
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 80)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 TODAS LAS VERIFICACIONES PASARON")
        print("=" * 80)
        print("\n✅ El sistema está listo para usar las nuevas variables")
        print("\n📝 Próximos pasos:")
        print("   1. Reiniciar el IoT Consumer")
        print("   2. Verificar que los sensores envían las nuevas variables")
        print("   3. Actualizar dashboard para visualizar NO2, CO2, viento")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("=" * 80)
        print("\n❌ Revisa los errores arriba y:")
        if not results["Base de Datos"]:
            print("   1. Ejecuta la migración: alembic upgrade head")
        print("   2. Verifica que todos los archivos estén guardados")
        print("   3. Reinicia los servicios")
    
    print("\n")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
