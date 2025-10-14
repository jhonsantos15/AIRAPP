"""
User-friendly labels for devices and constants.
"""

# Device ID to friendly name mapping
FRIENDLY_LABELS = {
    "S1_PMTHVD": "Colegio Parnaso",
    "S2_PMTHVD": "GRB_LLenadero Ppal",
    "S3_PMTHVD": "GRB_B. Yariguies",
    "S4_PMTHVD": "GRB_B. Rosario",
    "S5_PMTHVD": "GRB_PTAR",
    "S6_PMTHVD": "ICPET",
}


def label_for(device_id: str) -> str:
    """
    Returns the friendly name for a device ID.
    Falls back to the original ID if no mapping exists.
    
    Args:
        device_id: Device identifier
        
    Returns:
        Friendly name or original ID
    """
    return FRIENDLY_LABELS.get(str(device_id), str(device_id))


def get_all_devices() -> list[str]:
    """
    Returns list of all known device IDs.
    
    Returns:
        List of device IDs
    """
    return list(FRIENDLY_LABELS.keys())


def get_device_mapping() -> dict[str, str]:
    """
    Returns complete device ID to label mapping.
    
    Returns:
        Dictionary mapping device IDs to friendly names
    """
    return FRIENDLY_LABELS.copy()
