"""
Configuración para reportes PDF.
Puedes modificar estos valores para personalizar la apariencia de los reportes.
"""

# ========== COLORES ==========
# Colores principales (en formato hexadecimal)
COLOR_PRIMARY = "#2c5aa0"        # Azul primario para encabezados
COLOR_SECONDARY = "#1f4788"      # Azul secundario para títulos
COLOR_TEXT = "#333333"           # Color de texto principal
COLOR_MUTED = "#666666"          # Color de texto secundario

# Colores para tablas
TABLE_HEADER_BG = "#2c5aa0"      # Fondo de encabezados de tabla
TABLE_HEADER_TEXT = "#FFFFFF"    # Texto de encabezados de tabla
TABLE_ROW_BG_1 = "#FFFFFF"       # Fondo de filas impares
TABLE_ROW_BG_2 = "#F5F5F5"       # Fondo de filas pares
TABLE_BORDER = "#000000"         # Color de bordes de tabla

# ========== FUENTES ==========
# Fuentes disponibles en ReportLab sin instalación adicional
FONT_TITLE = "Helvetica-Bold"
FONT_HEADING = "Helvetica-Bold"
FONT_NORMAL = "Helvetica"
FONT_ITALIC = "Helvetica-Oblique"

# Tamaños de fuente
FONT_SIZE_TITLE = 18
FONT_SIZE_HEADING = 14
FONT_SIZE_NORMAL = 10
FONT_SIZE_SMALL = 8

# ========== PÁGINA ==========
# Tamaño de página (usar constantes de reportlab.lib.pagesizes)
# Opciones: letter, A4, legal
PAGE_SIZE = "letter"  # 8.5" x 11"

# Márgenes (en pulgadas)
MARGIN_TOP = 2.0
MARGIN_BOTTOM = 1.0
MARGIN_LEFT = 1.0
MARGIN_RIGHT = 1.0

# ========== CONTENIDO ==========
# Número máximo de registros en la muestra de datos
MAX_SAMPLE_RECORDS = 20

# Incluir secciones opcionales
INCLUDE_DEVICE_DISTRIBUTION = True  # Mostrar distribución por dispositivos
INCLUDE_DATA_SAMPLE = True          # Mostrar muestra de datos recientes
INCLUDE_STATISTICS = True           # Mostrar estadísticas generales

# ========== TEXTOS ==========
# Títulos y textos personalizables
TEXT_MAIN_TITLE = "Reporte de Calidad del Aire"
TEXT_GENERATED = "Generado"
TEXT_PERIOD = "Período"
TEXT_TOTAL_RECORDS = "Total de registros"
TEXT_DEVICES = "Dispositivos"
TEXT_ALL_DEVICES = "Todos"

TEXT_STATISTICS_TITLE = "Estadísticas Generales"
TEXT_DEVICE_DISTRIBUTION_TITLE = "Distribución por Dispositivos"
TEXT_DATA_SAMPLE_TITLE = "Muestra de Datos Recientes (Últimos {} registros)"

TEXT_DISCLAIMER = (
    "<b>Nota:</b> Los datos presentados son indicativos y provienen de sensores "
    "de bajo costo. Sistema de Vigilancia de Calidad del Aire."
)

TEXT_FOOTER = "Sistema de Vigilancia Calidad de Aire - Sensores Bajo Costo"

# ========== VARIABLES ==========
# Configuración de variables a mostrar
VARIABLES_CONFIG = {
    "pm25": {
        "label": "PM2.5",
        "unit": "µg/m³",
        "decimals": 2,
        "include": True
    },
    "pm10": {
        "label": "PM10",
        "unit": "µg/m³",
        "decimals": 2,
        "include": True
    },
    "temp": {
        "label": "Temperatura",
        "unit": "°C",
        "decimals": 2,
        "include": True
    },
    "rh": {
        "label": "Humedad Relativa",
        "unit": "%",
        "decimals": 2,
        "include": True
    }
}

# ========== ENCABEZADOS DE TABLAS ==========
STATS_TABLE_HEADERS = ["Variable", "Mínimo", "Máximo", "Promedio", "Unidad"]
DEVICE_TABLE_HEADERS = ["Dispositivo", "Registros"]
SAMPLE_TABLE_HEADERS = ["Fecha/Hora", "Dispositivo", "Canal", "PM2.5", "PM10", "Temp", "HR"]

# ========== ANCHOS DE COLUMNAS ==========
# Anchos para tabla de estadísticas (en pulgadas)
STATS_TABLE_WIDTHS = [2.0, 1.0, 1.0, 1.0, 1.0]

# Anchos para tabla de dispositivos (en pulgadas)
DEVICE_TABLE_WIDTHS = [3.0, 2.0]

# Anchos para tabla de muestra de datos (en pulgadas)
SAMPLE_TABLE_WIDTHS = [1.3, 1.2, 0.7, 0.8, 0.8, 0.7, 0.7]

# ========== FORMATOS ==========
# Formato de fecha y hora
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

# Formato de números
NUMBER_FORMAT = "{:.2f}"  # 2 decimales por defecto

# ========== ZONA HORARIA ==========
TIMEZONE = "America/Bogota"

# ========== LOGO / IMAGEN ==========
# Ruta al logo (opcional, dejar None si no se usa)
LOGO_PATH = None
LOGO_WIDTH = 1.5  # Pulgadas
LOGO_HEIGHT = 0.75  # Pulgadas

# ========== EXPORTAR CONFIGURACIÓN ==========
def get_config():
    """Retorna un diccionario con toda la configuración."""
    return {
        "colors": {
            "primary": COLOR_PRIMARY,
            "secondary": COLOR_SECONDARY,
            "text": COLOR_TEXT,
            "muted": COLOR_MUTED,
            "table_header_bg": TABLE_HEADER_BG,
            "table_header_text": TABLE_HEADER_TEXT,
            "table_row_bg_1": TABLE_ROW_BG_1,
            "table_row_bg_2": TABLE_ROW_BG_2,
            "table_border": TABLE_BORDER,
        },
        "fonts": {
            "title": FONT_TITLE,
            "heading": FONT_HEADING,
            "normal": FONT_NORMAL,
            "italic": FONT_ITALIC,
            "sizes": {
                "title": FONT_SIZE_TITLE,
                "heading": FONT_SIZE_HEADING,
                "normal": FONT_SIZE_NORMAL,
                "small": FONT_SIZE_SMALL,
            }
        },
        "page": {
            "size": PAGE_SIZE,
            "margins": {
                "top": MARGIN_TOP,
                "bottom": MARGIN_BOTTOM,
                "left": MARGIN_LEFT,
                "right": MARGIN_RIGHT,
            }
        },
        "content": {
            "max_sample_records": MAX_SAMPLE_RECORDS,
            "include_device_distribution": INCLUDE_DEVICE_DISTRIBUTION,
            "include_data_sample": INCLUDE_DATA_SAMPLE,
            "include_statistics": INCLUDE_STATISTICS,
        },
        "texts": {
            "main_title": TEXT_MAIN_TITLE,
            "generated": TEXT_GENERATED,
            "period": TEXT_PERIOD,
            "total_records": TEXT_TOTAL_RECORDS,
            "devices": TEXT_DEVICES,
            "all_devices": TEXT_ALL_DEVICES,
            "statistics_title": TEXT_STATISTICS_TITLE,
            "device_distribution_title": TEXT_DEVICE_DISTRIBUTION_TITLE,
            "data_sample_title": TEXT_DATA_SAMPLE_TITLE,
            "disclaimer": TEXT_DISCLAIMER,
            "footer": TEXT_FOOTER,
        },
        "variables": VARIABLES_CONFIG,
        "formats": {
            "datetime": DATETIME_FORMAT,
            "date": DATE_FORMAT,
            "time": TIME_FORMAT,
            "number": NUMBER_FORMAT,
        },
        "timezone": TIMEZONE,
        "logo": {
            "path": LOGO_PATH,
            "width": LOGO_WIDTH,
            "height": LOGO_HEIGHT,
        }
    }
