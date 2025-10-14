"""
Servicio de IoT Hub para ingesta de telemetría.
Integra EventHubConsumer, PayloadProcessor y HealthMonitor.
"""
import os
import logging
from typing import List, Optional, Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import db
from src.iot.consumer import EventHubConsumer
from src.iot.processor import PayloadProcessor
from src.iot.monitoring import HealthMonitor
from src.services.measurement_service import MeasurementService
from src.utils.constants import BOGOTA

logger = logging.getLogger(__name__)


class IoTHubService:
    """
    Servicio de alto nivel para ingesta de telemetría desde IoT Hub.
    Orquesta Consumer, Processor, Monitor y persistencia.
    """

    def __init__(
        self,
        consumer_group: str = "$Default",
        allowed_devices: Optional[set] = None,
        batch_size: int = 50,
        checkpoint_interval: int = 30,
    ):
        """
        Args:
            consumer_group: Consumer group de Event Hub
            allowed_devices: Set de device IDs permitidos. None = todos
            batch_size: Tamaño de batch para guardar en BD
            checkpoint_interval: Intervalo en segundos para checkpoints
        """
        self.consumer_group = consumer_group
        self.batch_size = batch_size
        self.checkpoint_interval = checkpoint_interval

        # Inicializar componentes
        self.consumer = EventHubConsumer(consumer_group=consumer_group)
        self.processor = PayloadProcessor(allowed_devices=allowed_devices)
        self.monitor = HealthMonitor(log_interval=60)

        # Buffer para batch processing
        self.batch_buffer = []

    def _normalize_start_position(self, start_position: Optional[str]) -> str:
        """
        Normaliza start position para el consumer.
        
        Args:
            start_position: 'latest', 'earliest', o 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            '-1' (earliest), '@latest', o datetime UTC
        """
        if not start_position:
            return "-1"

        v = start_position.strip().lower()
        if v in ("latest", "@latest"):
            return "@latest"
        if v in ("earliest", "-1"):
            return "-1"

        # Intentar parsear como datetime local (Bogotá)
        raw = start_position.strip().replace("Z", "")
        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M",
        ):
            try:
                dt_local = datetime.strptime(raw, fmt)
                if dt_local.tzinfo is None:
                    dt_local = dt_local.replace(tzinfo=BOGOTA)
                return dt_local.astimezone(timezone.utc)
            except ValueError:
                continue

        logger.warning(f"No se pudo parsear start_position='{start_position}'. Usando earliest")
        return "-1"

    def _flush_batch(self, partition_context=None, event=None, force: bool = False):
        """Guarda el buffer de mediciones acumuladas."""
        if not self.batch_buffer and not force:
            return

        if self.batch_buffer:
            try:
                from src.main import create_app
                app = create_app()

                with app.app_context():
                    measurement_service = MeasurementService(db.session)
                    inserted = measurement_service.save_measurements(self.batch_buffer)
                    
                    duplicates = len(self.batch_buffer) - inserted
                    self.monitor.record_messages_saved(inserted)
                    self.monitor.record_duplicates_skipped(duplicates)
                    self.monitor.record_batch_saved()
                    
                    self.batch_buffer = []

            except Exception as e:
                logger.exception(f"Error al guardar batch: {e}")
                self.monitor.record_error()
                self.batch_buffer = []

        # Checkpoint periódico
        if partition_context and event and (force or self.monitor.should_checkpoint(self.checkpoint_interval)):
            try:
                partition_context.update_checkpoint(event)
            except Exception as e:
                logger.warning(f"Error en checkpoint: {e}")

    def _on_event(self, partition_context, event):
        """Callback para procesar cada evento."""
        # Heartbeat
        if event is None:
            self._flush_batch(partition_context, event, force=True)
            self.monitor.log_metrics(self.consumer_group)
            return

        try:
            # Procesar evento
            self.monitor.record_message_received()
            measurements = self.processor.process_event(event)

            if measurements:
                self.monitor.record_message_processed(len(measurements))
                self.batch_buffer.extend(measurements)

                # Flush si alcanza batch size
                if len(self.batch_buffer) >= self.batch_size:
                    self._flush_batch(partition_context, event)

            self.monitor.log_metrics(self.consumer_group)

        except Exception as e:
            logger.exception(f"Error procesando evento: {e}")
            self.monitor.record_error()

    def _on_partition_initialize(self, partition_context):
        """Callback cuando se inicializa partición."""
        logger.info(
            f"[{self.consumer_group}] Partición {partition_context.partition_id} inicializada"
        )

    def start_ingestion(self, start_position: Optional[str] = None):
        """
        Inicia ingesta de telemetría.
        
        Args:
            start_position: 'latest', 'earliest', o datetime ISO string
        """
        starting = self._normalize_start_position(start_position)

        logger.info(f"=== Iniciando Ingesta IoT Hub ===")
        logger.info(f"Consumer Group: {self.consumer_group}")
        logger.info(f"Batch Size: {self.batch_size}")
        logger.info(f"Starting Position: {starting}")
        logger.info(f"Allowed Devices: {len(self.processor.allowed_devices) if self.processor.allowed_devices else 'TODOS'}")
        logger.info(f"=================================")

        try:
            self.consumer.consume(
                on_event=self._on_event,
                on_partition_initialize=self._on_partition_initialize,
                starting_position=starting,
                max_wait_time=60,
            )
        except KeyboardInterrupt:
            logger.info("Ingesta interrumpida por usuario. Guardando buffer pendiente...")
            self._flush_batch(force=True)
        except Exception as e:
            logger.exception(f"Error en ingesta: {e}")
            self._flush_batch(force=True)
        finally:
            self._flush_batch(force=True)
            self.monitor.log_summary(self.consumer_group)
            logger.info(f"Ingesta finalizada para CG '{self.consumer_group}'")
