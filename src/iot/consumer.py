"""
Consumer de Azure Event Hub para IoT Hub.
Gestiona la conexión, autenticación, proxy y TLS.
"""
import os
import os.path as osp
import logging
from typing import Dict, Optional, Union, Callable
from urllib.parse import urlparse
from datetime import datetime, timezone

from azure.eventhub import EventHubConsumerClient, TransportType
from dotenv import load_dotenv

try:
    import certifi
    _DEFAULT_CAFILE = certifi.where()
except Exception:
    _DEFAULT_CAFILE = None

from src.core.config import settings

logger = logging.getLogger(__name__)


class EventHubConsumer:
    """
    Consumidor de Azure Event Hub compatible con IoT Hub.
    Gestiona conexión, proxy, TLS y consumer groups.
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        consumer_group: str = "asa",
    ):
        self.connection_string = connection_string or os.getenv("EVENTHUB_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("EVENTHUB_CONNECTION_STRING no está definido")

        self.consumer_group = consumer_group
        self.metadata = self._parse_connection_string(self.connection_string)
        self._validate_connection_string()

        logger.info(
            f"EventHub configurado: host={self.metadata['host']}, "
            f"entity={self.metadata['entity_path']}, policy={self.metadata['sak_name']}"
        )

    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """Extrae metadatos del connection string."""
        parts: Dict[str, str] = {}
        for kv in conn_str.split(";"):
            if "=" in kv:
                k, v = kv.split("=", 1)
                parts[k.strip()] = v.strip()

        endpoint = parts.get("Endpoint", "")
        if endpoint.lower().startswith("sb://"):
            host = endpoint[len("sb://"):].strip("/ ")
        else:
            host = endpoint

        return {
            "endpoint": endpoint,
            "host": host.replace("/", ""),
            "entity_path": parts.get("EntityPath", ""),
            "sak_name": parts.get("SharedAccessKeyName", ""),
        }

    def _validate_connection_string(self):
        """Valida que el connection string tenga EntityPath."""
        if not self.metadata["entity_path"]:
            raise ValueError(
                "Connection string NO tiene EntityPath. "
                "Copie el Extremo compatible con Event Hub desde IoT Hub "
                "(Puntos de conexión integrados)."
            )

    def _get_proxy_config(self) -> Optional[Dict[str, Union[str, int]]]:
        """
        Obtiene configuración de proxy desde variables de entorno.
        Respeta NO_PROXY y FORCE_NO_PROXY.
        """
        if os.getenv("FORCE_NO_PROXY") == "1":
            logger.info("FORCE_NO_PROXY=1: sin proxy")
            return None

        if self._host_in_no_proxy(self.metadata["host"]):
            logger.info(f"NO_PROXY activo para {self.metadata['host']}")
            return None

        proxy = (
            os.getenv("EVENTHUB_PROXY")
            or os.getenv("HTTPS_PROXY")
            or os.getenv("HTTP_PROXY")
        )
        if not proxy:
            return None

        u = urlparse(proxy)
        if not u.hostname or not u.port:
            logger.warning("Proxy inválido (falta host o puerto)")
            return None

        config: Dict[str, Union[str, int]] = {
            "proxy_hostname": u.hostname,
            "proxy_port": int(u.port),
        }
        if u.username:
            config["username"] = u.username
        if u.password:
            config["password"] = u.password

        logger.info(f"Proxy configurado: {u.hostname}:{u.port}")
        return config

    def _host_in_no_proxy(self, host: str) -> bool:
        """Verifica si el host está en NO_PROXY."""
        raw = os.getenv("NO_PROXY") or os.getenv("no_proxy") or ""
        if not raw:
            return False

        items = [x.strip() for x in raw.split(",") if x.strip()]
        host_l = host.lower()

        for pat in items:
            pat_l = pat.lower()
            if pat_l == "*":
                return True
            if host_l == pat_l:
                return True
            if pat_l.startswith(".") and host_l.endswith(pat_l):
                return True
            if host_l.endswith("." + pat_l):
                return True
        return False

    def _get_tls_verify(self) -> Union[bool, str]:
        """
        Obtiene configuración de verificación TLS.
        false/0/no -> False (solo pruebas)
        true/1/yes -> certifi CA o True
        ruta -> ruta personalizada
        """
        v = os.getenv("EVENTHUB_VERIFY")
        if not v or not v.strip():
            if _DEFAULT_CAFILE:
                logger.info(f"TLS verify usando certifi: {_DEFAULT_CAFILE}")
                return _DEFAULT_CAFILE
            logger.info("TLS verify usando store del sistema")
            return True

        vv = v.strip().lower()
        if vv in ("false", "0", "no"):
            logger.warning("TLS verify DESACTIVADO (solo pruebas)")
            return False
        if vv in ("true", "1", "yes"):
            if _DEFAULT_CAFILE:
                logger.info(f"TLS verify usando certifi: {_DEFAULT_CAFILE}")
                return _DEFAULT_CAFILE
            return True

        if osp.isfile(v):
            logger.info(f"TLS verify usando CA personalizada: {v}")
            return v

        logger.warning(
            f"EVENTHUB_VERIFY='{v}' inválido; usando certifi/store por defecto"
        )
        return _DEFAULT_CAFILE if _DEFAULT_CAFILE else True

    def create_client(self) -> EventHubConsumerClient:
        """Crea instancia del cliente Event Hub con configuración completa."""
        http_proxy = self._get_proxy_config()
        connection_verify = self._get_tls_verify()

        logger.info(
            f"Creando cliente para CG '{self.consumer_group}' "
            f"con AMQP over WebSocket (puerto 443)"
        )

        return EventHubConsumerClient.from_connection_string(
            conn_str=self.connection_string,
            consumer_group=self.consumer_group,
            transport_type=TransportType.AmqpOverWebsocket,
            http_proxy=http_proxy,
            connection_verify=connection_verify,
        )

    def consume(
        self,
        on_event: Callable,
        on_partition_initialize: Optional[Callable] = None,
        starting_position: str = "-1",
        max_wait_time: int = 60,
    ):
        """
        Inicia consumo de mensajes.
        
        Args:
            on_event: Callback para procesar cada evento
            on_partition_initialize: Callback cuando se inicializa partición
            starting_position: earliest (-1), latest (@latest), o datetime UTC
            max_wait_time: Timeout en segundos para heartbeat
        """
        client = self.create_client()
        
        logger.info(
            f"[{self.consumer_group}] Iniciando consumo "
            f"(starting_position={starting_position})"
        )

        try:
            with client:
                client.receive(
                    on_event=on_event,
                    on_partition_initialize=on_partition_initialize,
                    starting_position=starting_position,
                    max_wait_time=max_wait_time,
                )
        except KeyboardInterrupt:
            logger.info(f"[{self.consumer_group}] Consumo interrumpido por usuario")
            raise
        except Exception as e:
            logger.exception(
                f"Error en consumo (host={self.metadata['host']}, "
                f"CG={self.consumer_group}): {e}"
            )
            raise
