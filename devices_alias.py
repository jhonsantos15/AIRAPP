# devices_alias.py
# -----------------------------------------------------
# Mapea el ID real del dispositivo a un nombre amigable.
# Cambia libremente los valores a tus nombres preferidos.
# -----------------------------------------------------

DEV_ALIAS = {
    "S1_PMTHVD": "Colegio Parnaso",
    "S2_PMTHVD": "GRB_LLenadero Ppal",
    "S3_PMTHVD": "Barrio Yariguies",
    "S4_PMTHVD": "GRB_B. Rosario",
    "S5_PMTHVD": "GRB_PTAR",
    "S6_PMTHVD": "ICPET",
}

def alias_of(device_id: str) -> str:
    """Devuelve el alias amigable; si no existe, retorna el ID tal cual."""
    return DEV_ALIAS.get(device_id, device_id)
