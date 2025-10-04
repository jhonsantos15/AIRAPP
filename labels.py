# labels.py — Nombres visibles para los usuarios

FRIENDLY_LABELS = {
    "S1_PMTHVD": "Colegio Parnaso",
    "S2_PMTHVD": "GRB_LLenadero Ppal",
    "S3_PMTHVD": "Barrio Yariguies",
    "S4_PMTHVD": "GRB_B. Rosario",
    "S5_PMTHVD": "GRB_PTAR",
    "S6_PMTHVD": "ICPET",
}

def label_for(device_id: str) -> str:
    """Devuelve el nombre amigable si existe; en su defecto, el ID original."""
    return FRIENDLY_LABELS.get(str(device_id), str(device_id))
