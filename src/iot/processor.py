"""
Procesador de payloads de telemetría IoT.
Extrae y transforma datos de sensores en objetos Measurement.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.models import Measurement, SensorChannel, row_from_payload
from src.utils.logging_config import get_app_logger

logger = get_app_logger()


class PayloadProcessor:
    """
    Procesa payloads JSON de IoT Hub y los convierte en objetos Measurement.
    """

    def __init__(self, allowed_devices: Optional[set] = None):
        """
        Args:
            allowed_devices: Set de device IDs permitidos. None = todos.
        """
        self.allowed_devices = allowed_devices or set()
        self.stats = {"processed": 0, "filtered": 0, "errors": 0}

    def process_event(self, event) -> List[Measurement]:
        """
        Procesa un evento de Event Hub y retorna lista de Measurements.
        
        Args:
            event: Evento de Azure Event Hub
            
        Returns:
            Lista de objetos Measurement (puede estar vacía si se filtra)
        """
        if event is None:
            return []

        try:
            # Parsear JSON
            body = event.body_as_str(encoding="UTF-8")
            payload = json.loads(body)

            # Extraer device_id
            device_id = self._extract_device_id(event, payload)
            
            # Filtrar por dispositivos permitidos
            if self.allowed_devices and device_id:
                if device_id not in self.allowed_devices:
                    self.stats["filtered"] += 1
                    return []

            # Convertir a measurements
            measurements = self._payload_to_measurements(payload, device_id)
            self.stats["processed"] += len(measurements)
            
            return measurements

        except json.JSONDecodeError as e:
            logger.warning(f"Error decodificando JSON: {e}")
            self.stats["errors"] += 1
            return []
        except Exception as e:
            logger.exception(f"Error procesando evento: {e}")
            self.stats["errors"] += 1
            return []

    def _extract_device_id(self, event, payload: Dict[str, Any]) -> Optional[str]:
        """Extrae device_id desde system properties o payload."""
        # Intentar desde system properties (IoT Hub)
        device_from_sys = None
        try:
            if getattr(event, "system_properties", None):
                devb = event.system_properties.get(b"iothub-connection-device-id")
                if devb:
                    device_from_sys = (
                        devb.decode()
                        if isinstance(devb, (bytes, bytearray))
                        else str(devb)
                    )
        except Exception as e:
            logger.debug(f"No se pudo extraer device_id de system properties: {e}")

        # Intentar desde payload
        payload_device = payload.get("DeviceId") or payload.get("deviceId")
        
        return payload_device or device_from_sys

    def _payload_to_measurements(
        self, payload: Dict[str, Any], device_id: Optional[str]
    ) -> List[Measurement]:
        """
        Convierte payload JSON a lista de Measurements.
        Crea un Measurement por cada sensor channel (Um1, Um2) que tenga datos.
        """
        # Extraer campos base (timestamp, temp, rh, etc.)
        base = row_from_payload(payload, device_id_fallback=device_id)
        rows: List[Measurement] = []

        # Canal Um1 (sensor 1)
        if self._has_um1_data(payload):
            rows.append(
                Measurement(
                    **base,
                    sensor_channel=SensorChannel.Um1,
                    pm25=self._safe_float(payload.get("n1025Um1")),
                    pm10=self._safe_float(payload.get("n25100Um1")),
                )
            )

        # Canal Um2 (sensor 2)
        if self._has_um2_data(payload):
            rows.append(
                Measurement(
                    **base,
                    sensor_channel=SensorChannel.Um2,
                    pm25=self._safe_float(payload.get("n1025Um2")),
                    pm10=self._safe_float(payload.get("n25100Um2")),
                )
            )

        # Si no hay datos de PM, crear registro Um1 con temp/rh
        if not rows:
            rows.append(Measurement(**base, sensor_channel=SensorChannel.Um1))

        return rows

    def _has_um1_data(self, payload: Dict[str, Any]) -> bool:
        """Verifica si el payload tiene datos del sensor Um1."""
        return ("n1025Um1" in payload) or ("n25100Um1" in payload)

    def _has_um2_data(self, payload: Dict[str, Any]) -> bool:
        """Verifica si el payload tiene datos del sensor Um2."""
        return ("n1025Um2" in payload) or ("n25100Um2" in payload)

    def _safe_float(self, value: Any) -> Optional[float]:
        """Convierte valor a float de forma segura."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas de procesamiento."""
        return self.stats.copy()

    def reset_stats(self):
        """Reinicia estadísticas."""
        self.stats = {"processed": 0, "filtered": 0, "errors": 0}
