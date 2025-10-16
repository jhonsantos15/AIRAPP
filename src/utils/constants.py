"""
Application constants.
"""
from zoneinfo import ZoneInfo

# Timezone
BOGOTA = ZoneInfo("America/Bogota")

# Sistema de colores estándar por equipo (FIJOS - NO ROTAN)
# Cada equipo tiene un color único, distintivo y consistente
DEVICE_COLORS = {
    "S1_PMTHVD": "#FF6B6B",  # Rojo coral - Colegio Parnaso
    "S2_PMTHVD": "#FFA500",  # Naranja - GRB_LLenadero Ppal
    "S3_PMTHVD": "#FFD700",  # Dorado - GRB_B. Yariguies
    "S4_PMTHVD": "#E74C3C",  # Rojo intenso - GRB_B. Rosario
    "S5_PMTHVD": "#F39C12",  # Naranja oscuro - GRB_PTAR
    "S6_PMTHVD": "#3498DB",  # Azul cielo - ICPET
}

# Colores alternativos para casos especiales
FALLBACK_COLORS = [
    "#11B6C7",  # Turquesa principal
    "#59D07A",  # Verde menta
    "#9B59B6",  # Púrpura
    "#1ABC9C",  # Verde agua
    "#95A5A6",  # Gris
    "#34495E",  # Azul oscuro
]

# Colores por tipo de material particulado (para diferenciación visual)
PM_COLORS = {
    "pm25": {
        "opacity": 0.95,
        "width": 2.2,
    },
    "pm10": {
        "opacity": 0.70,
        "width": 1.4,
    }
}

# Plotly color scheme (usado como fallback)
COLORWAY = list(DEVICE_COLORS.values()) + FALLBACK_COLORS

# Dash styles by sensor channel
DASH_BY_UM = {
    "Um1": "solid",      # Sensor 1: línea sólida
    "Um2": "dash"        # Sensor 2: línea punteada (más visible que 'dot')
}

# Sensor channel labels
SENSOR_CHANNEL_LABELS = {
    "Um1": "Sensor 1",
    "Um2": "Sensor 2",
    "ambos": "Ambos"
}

# Particulate matter labels
PM_LABELS = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "ambas": "Ambas"
}

# Variables disponibles
AVAILABLE_VARIABLES = ["pm25", "pm10", "temp", "rh", "no2", "co2", "vel_viento", "dir_viento"]

# Consumer groups Kafka
KAFKA_CONSUMER_GROUPS = {
    "S4_PMTHVD": "asa-s4",
    "S5_PMTHVD": "asa-s5",
    "S6_PMTHVD": "asa-s6",
}
