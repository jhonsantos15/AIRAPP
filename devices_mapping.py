# devices_mapping.py
# -----------------------------------------------------
# Mapeo 1:1 entre Consumer Groups y Device IDs
# Garantiza que cada consumer group procese ÚNICAMENTE
# el dispositivo asignado, evitando conflictos y mejorando
# la trazabilidad en Azure IoT Hub.
# -----------------------------------------------------

CONSUMER_GROUP_TO_DEVICE = {
    "asa-s1": "S1_PMTHVD",
    "asa-s2": "S2_PMTHVD",
    "asa-s3": "S3_PMTHVD",
    "asa-s4": "S4_PMTHVD",
    "asa-s5": "S5_PMTHVD",
    "asa-s6": "S6_PMTHVD",
}


def get_device_for_consumer_group(consumer_group: str) -> str | None:
    """
    Obtiene el device ID asignado a un consumer group específico.
    
    Args:
        consumer_group: Nombre del consumer group (ej: 'asa-s4')
    
    Returns:
        Device ID asignado o None si no existe mapeo
    """
    return CONSUMER_GROUP_TO_DEVICE.get(consumer_group)


def get_consumer_group_for_device(device_id: str) -> str | None:
    """
    Obtiene el consumer group asignado a un device ID específico.
    
    Args:
        device_id: ID del dispositivo (ej: 'S4_PMTHVD')
    
    Returns:
        Consumer group asignado o None si no existe mapeo
    """
    for cg, dev in CONSUMER_GROUP_TO_DEVICE.items():
        if dev == device_id:
            return cg
    return None


def validate_consumer_groups(consumer_groups: list[str]) -> dict[str, str]:
    """
    Valida una lista de consumer groups y retorna el mapeo activo.
    
    Args:
        consumer_groups: Lista de consumer groups a validar
    
    Returns:
        Diccionario con {consumer_group: device_id} para CGs válidos
    
    Raises:
        ValueError: Si algún consumer group no tiene mapeo definido
    """
    mapping = {}
    invalid_groups = []
    
    for cg in consumer_groups:
        device = get_device_for_consumer_group(cg)
        if device is None:
            invalid_groups.append(cg)
        else:
            mapping[cg] = device
    
    if invalid_groups:
        available = ", ".join(sorted(CONSUMER_GROUP_TO_DEVICE.keys()))
        raise ValueError(
            f"Consumer groups sin mapeo definido: {', '.join(invalid_groups)}. "
            f"Consumer groups disponibles: {available}"
        )
    
    return mapping
