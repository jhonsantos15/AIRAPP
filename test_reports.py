"""
Script de prueba para verificar la funcionalidad de reportes PDF.
"""
import requests
from datetime import datetime

# URL base de la API
BASE_URL = "http://localhost:5000"

def test_report_generation(period, **params):
    """Prueba la generación de un reporte PDF."""
    url = f"{BASE_URL}/api/reports/pdf"
    params['period'] = period
    
    print(f"\n{'='*60}")
    print(f"Probando reporte: {period}")
    print(f"Parámetros: {params}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_reporte_{period}_{timestamp}.pdf"
            
            # Guardar archivo
            with open(filename, "wb") as f:
                f.write(response.content)
            
            print(f"✓ Reporte generado exitosamente")
            print(f"  Archivo: {filename}")
            print(f"  Tamaño: {len(response.content)} bytes")
            return True
        else:
            print(f"✗ Error en la generación del reporte")
            print(f"  Código de estado: {response.status_code}")
            print(f"  Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Excepción al generar reporte: {e}")
        return False


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "="*60)
    print("PRUEBAS DE GENERACIÓN DE REPORTES PDF")
    print("="*60)
    
    tests = [
        # Test 1: Reporte de última hora
        ("hour", {}),
        
        # Test 2: Reporte de 24 horas
        ("24hours", {}),
        
        # Test 3: Reporte de 7 días con filtro de dispositivo
        ("7days", {"device_id": "S4_PMTHVD,S5_PMTHVD"}),
        
        # Test 4: Reporte de año actual con canal específico
        ("year", {"sensor_channel": "um1"}),
        
        # Test 5: Reporte personalizado
        ("custom", {
            "start_date": "2025-10-01",
            "end_date": "2025-10-13",
            "device_id": "S4_PMTHVD"
        }),
    ]
    
    results = []
    for period, params in tests:
        success = test_report_generation(period, **params)
        results.append((period, success))
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for period, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - Reporte: {period}")
    
    print(f"\nTotal: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("\n✓ Todas las pruebas pasaron correctamente!")
    else:
        print(f"\n✗ {total - passed} prueba(s) fallaron")


if __name__ == "__main__":
    main()
