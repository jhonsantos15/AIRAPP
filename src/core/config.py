"""
Configuración centralizada de la aplicación usando Pydantic Settings.
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
INSTANCE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Configuración de la aplicación con validación de Pydantic."""
    
    # Aplicación
    app_name: str = Field(default="AireApp", description="Nombre de la aplicación")
    debug: bool = Field(default=False, description="Modo debug")
    host: str = Field(default="0.0.0.0", description="Host del servidor")
    port: int = Field(default=5000, description="Puerto del servidor")
    
    # Base de datos
    database_url: str = Field(
        default=f"sqlite:///{INSTANCE_DIR / 'aireapp.db'}",
        description="URL de conexión a la base de datos"
    )
    
    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092",
        description="Servidores Kafka"
    )
    kafka_consumer_group_s4: str = Field(default="asa-s4", description="Consumer group S4")
    kafka_consumer_group_s5: str = Field(default="asa-s5", description="Consumer group S5")
    kafka_consumer_group_s6: str = Field(default="asa-s6", description="Consumer group S6")
    kafka_auto_offset_reset: str = Field(default="latest", description="Auto offset reset")
    
    # Logging
    log_level: str = Field(default="INFO", description="Nivel de logging")
    log_file: str = Field(
        default=str(LOGS_DIR / "aireapp.log"),
        description="Archivo de log"
    )
    log_max_bytes: int = Field(default=10_485_760, description="Tamaño máximo del log (10MB)")
    log_backup_count: int = Field(default=5, description="Número de backups del log")
    
    # Timezone
    timezone: str = Field(default="America/Bogota", description="Zona horaria")
    
    # Dashboard
    dash_update_interval: int = Field(default=60000, description="Intervalo de actualización del dashboard (ms)")
    
    # Reportes
    reports_max_days: int = Field(default=31, description="Días máximos para reportes")
    
    # Azure EventHub / IoT Hub
    eventhub_connection_string: str | None = Field(default=None, description="EventHub connection string")
    allowed_devices: str | None = Field(default=None, description="Allowed devices CSV")
    
    # Proxy settings
    force_no_proxy: str | None = Field(default=None, description="Force no proxy flag")
    no_proxy: str | None = Field(default=None, description="No proxy hosts")
    
    # API CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5000", "http://localhost:8050"],
        description="Allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache
def get_settings() -> Settings:
    """Obtiene la configuración singleton."""
    return Settings()


# Instancia global de configuración
settings = get_settings()
