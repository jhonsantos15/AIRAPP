#!/usr/bin/env python
"""
Script de prueba para validar el mapeo 1:1 Consumer Groups → Device IDs
"""
import sys
from devices_mapping import (
    CONSUMER_GROUP_TO_DEVICE,
    validate_consumer_groups,
    get_device_for_consumer_group,
    get_consumer_group_for_device
)

def test_mapeo_basico():
    """Prueba que el mapeo está correctamente definido"""
    print("=" * 80)
    print("TEST 1: Mapeo básico")
    print("=" * 80)
    
    assert len(CONSUMER_GROUP_TO_DEVICE) == 6, "Deben existir 6 consumer groups"
    
    for cg, device in CONSUMER_GROUP_TO_DEVICE.items():
        print(f"✅ {cg:15s} → {device}")
    
    print("✅ TEST 1 PASADO\n")


def test_get_device_for_cg():
    """Prueba la función get_device_for_consumer_group"""
    print("=" * 80)
    print("TEST 2: get_device_for_consumer_group()")
    print("=" * 80)
    
    # Casos válidos
    assert get_device_for_consumer_group("asa-s4") == "S4_PMTHVD"
    print("✅ asa-s4 → S4_PMTHVD")
    
    assert get_device_for_consumer_group("asa-s6") == "S6_PMTHVD"
    print("✅ asa-s6 → S6_PMTHVD")
    
    # Caso inválido
    assert get_device_for_consumer_group("asa-s99") is None
    print("✅ asa-s99 → None (esperado)")
    
    print("✅ TEST 2 PASADO\n")


def test_get_cg_for_device():
    """Prueba la función get_consumer_group_for_device"""
    print("=" * 80)
    print("TEST 3: get_consumer_group_for_device()")
    print("=" * 80)
    
    # Casos válidos
    assert get_consumer_group_for_device("S4_PMTHVD") == "asa-s4"
    print("✅ S4_PMTHVD → asa-s4")
    
    assert get_consumer_group_for_device("S6_PMTHVD") == "asa-s6"
    print("✅ S6_PMTHVD → asa-s6")
    
    # Caso inválido
    assert get_consumer_group_for_device("S99_PMTHVD") is None
    print("✅ S99_PMTHVD → None (esperado)")
    
    print("✅ TEST 3 PASADO\n")


def test_validate_valid_groups():
    """Prueba la validación con consumer groups válidos"""
    print("=" * 80)
    print("TEST 4: validate_consumer_groups() con CGs válidos")
    print("=" * 80)
    
    mapping = validate_consumer_groups(["asa-s4", "asa-s5", "asa-s6"])
    
    assert len(mapping) == 3
    assert mapping["asa-s4"] == "S4_PMTHVD"
    assert mapping["asa-s5"] == "S5_PMTHVD"
    assert mapping["asa-s6"] == "S6_PMTHVD"
    
    print("✅ Validación correcta para ['asa-s4', 'asa-s5', 'asa-s6']")
    for cg, dev in mapping.items():
        print(f"   {cg} → {dev}")
    
    print("✅ TEST 4 PASADO\n")


def test_validate_invalid_groups():
    """Prueba la validación con consumer groups inválidos"""
    print("=" * 80)
    print("TEST 5: validate_consumer_groups() con CGs inválidos")
    print("=" * 80)
    
    try:
        validate_consumer_groups(["asa-s99"])
        print("❌ TEST 5 FALLADO: Debería haber lanzado ValueError")
        sys.exit(1)
    except ValueError as e:
        print(f"✅ ValueError esperado: {e}")
        print("✅ TEST 5 PASADO\n")


def test_message_filtering_simulation():
    """Simula el filtrado de mensajes"""
    print("=" * 80)
    print("TEST 6: Simulación de filtrado de mensajes")
    print("=" * 80)
    
    # Simular consumer group asa-s4
    cg = "asa-s4"
    expected_device = get_device_for_consumer_group(cg)
    print(f"Consumer Group: {cg}")
    print(f"Device esperado: {expected_device}\n")
    
    # Mensajes de prueba
    test_messages = [
        ("S4_PMTHVD", True),   # Correcto
        ("S5_PMTHVD", False),  # Incorrecto
        ("S4_PMTHVD", True),   # Correcto
        ("S6_PMTHVD", False),  # Incorrecto
        ("S4_PMTHVD", True),   # Correcto
    ]
    
    processed = 0
    filtered = 0
    
    for device_id, should_process in test_messages:
        if device_id == expected_device:
            processed += 1
            status = "✅ PROCESADO"
        else:
            filtered += 1
            status = "❌ FILTRADO"
        
        assert (device_id == expected_device) == should_process
        print(f"  Mensaje de {device_id}: {status}")
    
    print(f"\nResumen:")
    print(f"  Procesados: {processed}/5")
    print(f"  Filtrados:  {filtered}/5")
    
    assert processed == 3
    assert filtered == 2
    
    print("✅ TEST 6 PASADO\n")


if __name__ == "__main__":
    print("\n" + "🧪 PRUEBAS DEL SISTEMA DE MAPEO 1:1".center(80))
    print("=" * 80 + "\n")
    
    try:
        test_mapeo_basico()
        test_get_device_for_cg()
        test_get_cg_for_device()
        test_validate_valid_groups()
        test_validate_invalid_groups()
        test_message_filtering_simulation()
        
        print("=" * 80)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE 🎉".center(80))
        print("=" * 80)
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
