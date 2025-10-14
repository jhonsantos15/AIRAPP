"""
Monitor de salud y métricas para ingesta IoT.
Trackea mensajes procesados, errores y performance.
"""
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Monitor de salud para el sistema de ingesta IoT.
    Trackea métricas, genera logs periódicos y detecta anomalías.
    """

    def __init__(self, log_interval: int = 60):
        """
        Args:
            log_interval: Intervalo en segundos para log de métricas
        """
        self.log_interval = log_interval
        self.metrics = {
            "messages_received": 0,
            "messages_processed": 0,
            "messages_filtered": 0,
            "messages_saved": 0,
            "duplicates_skipped": 0,
            "errors": 0,
            "batches_saved": 0,
        }
        self.window_start = time.time()
        self.last_checkpoint_time = time.time()
        self.start_time = datetime.now()

    def record_message_received(self):
        """Registra mensaje recibido."""
        self.metrics["messages_received"] += 1

    def record_message_processed(self, count: int = 1):
        """Registra mensajes procesados."""
        self.metrics["messages_processed"] += count

    def record_message_filtered(self):
        """Registra mensaje filtrado por device ID."""
        self.metrics["messages_filtered"] += 1

    def record_messages_saved(self, count: int):
        """Registra mensajes guardados en BD."""
        self.metrics["messages_saved"] += count

    def record_duplicates_skipped(self, count: int):
        """Registra duplicados omitidos."""
        self.metrics["duplicates_skipped"] += count

    def record_error(self):
        """Registra error de procesamiento."""
        self.metrics["errors"] += 1

    def record_batch_saved(self):
        """Registra batch guardado."""
        self.metrics["batches_saved"] += 1

    def should_log_metrics(self) -> bool:
        """Verifica si es momento de loggear métricas."""
        now = time.time()
        return (now - self.window_start) >= self.log_interval

    def log_metrics(self, consumer_group: str, force: bool = False):
        """
        Loggea métricas del último intervalo.
        
        Args:
            consumer_group: Nombre del consumer group
            force: Forzar log aunque no haya pasado el intervalo
        """
        now = time.time()
        if not force and not self.should_log_metrics():
            return

        elapsed = now - self.window_start
        if elapsed > 0:
            msg_rate = self.metrics["messages_processed"] / elapsed
            logger.info(
                f"[{consumer_group}] Métricas ({elapsed:.0f}s): "
                f"recibidos={self.metrics['messages_received']}, "
                f"procesados={self.metrics['messages_processed']}, "
                f"guardados={self.metrics['messages_saved']}, "
                f"duplicados={self.metrics['duplicates_skipped']}, "
                f"filtrados={self.metrics['messages_filtered']}, "
                f"errores={self.metrics['errors']}, "
                f"rate={msg_rate:.1f} msg/s"
            )

        # Reset window metrics
        self.window_start = now
        for key in [
            "messages_received",
            "messages_processed",
            "messages_saved",
            "duplicates_skipped",
            "messages_filtered",
        ]:
            self.metrics[key] = 0

    def should_checkpoint(self, interval: int = 30) -> bool:
        """
        Verifica si es momento de hacer checkpoint.
        
        Args:
            interval: Intervalo en segundos entre checkpoints
        """
        now = time.time()
        if (now - self.last_checkpoint_time) >= interval:
            self.last_checkpoint_time = now
            return True
        return False

    def get_uptime(self) -> timedelta:
        """Retorna tiempo de ejecución."""
        return datetime.now() - self.start_time

    def get_summary(self) -> Dict[str, any]:
        """Retorna resumen completo de métricas."""
        uptime = self.get_uptime()
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_str": str(uptime),
            "metrics": self.metrics.copy(),
            "start_time": self.start_time.isoformat(),
        }

    def log_summary(self, consumer_group: str):
        """Loggea resumen completo al finalizar."""
        summary = self.get_summary()
        logger.info(
            f"[{consumer_group}] RESUMEN FINAL:\n"
            f"  Uptime: {summary['uptime_str']}\n"
            f"  Total batches: {summary['metrics']['batches_saved']}\n"
            f"  Total errores: {summary['metrics']['errors']}\n"
            f"  Inicio: {summary['start_time']}"
        )
