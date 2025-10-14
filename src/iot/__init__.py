"""
Módulo IoT Hub para ingestión y procesamiento de datos de sensores.
Gestiona la conexión con Azure Event Hub y procesamiento de telemetría.
"""
from .consumer import EventHubConsumer
from .processor import PayloadProcessor
from .monitoring import HealthMonitor

__all__ = ["EventHubConsumer", "PayloadProcessor", "HealthMonitor"]
