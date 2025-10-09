import os
import sys
import json
import time
import logging
import os.path as osp
from typing import Iterable, List, Dict, Optional, Union
from urllib.parse import urlparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv, find_dotenv

# Cargar .env (sobrescribe para asegurar consistencia de variables)
load_dotenv(find_dotenv(), override=True)

from azure.eventhub import EventHubConsumerClient, TransportType

# Fuente de CAs por defecto (evita errores "cafile debe ser ruta válida")
try:
    import certifi
    _DEFAULT_CAFILE = certifi.where()
except Exception:
    _DEFAULT_CAFILE = None

from db import db
from models import Measurement, SensorChannel, row_from_payload

BOGOTA = ZoneInfo("America/Bogota")

# -------------------------------------------------
# Logging
# -------------------------------------------------
logger = logging.getLogger("ingest")
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)

# Filtro opcional por dispositivos (coma-separados)
ALLOWED = {
    d.strip()
    for d in (os.getenv("ALLOWED_DEVICES") or "").split(",")
    if d.strip()
}

# ---------- Helpers de conexión/proxy ----------
def parse_conn_str(cs: str) -> Dict[str, str]:
    """Extrae Endpoint, EntityPath y SharedAccessKeyName del connection string."""
    parts: Dict[str, str] = {}
    for kv in cs.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            parts[k.strip()] = v.strip()
    ep = parts.get("Endpoint", "")
    if ep.lower().startswith("sb://"):
        host = ep[len("sb://"):].strip("/ ")
    else:
        host = ep
    return {
        "endpoint": ep,
        "host": host.replace("/", ""),
        "entity_path": parts.get("EntityPath", ""),
        "sak_name": parts.get("SharedAccessKeyName", ""),
    }

def _host_in_no_proxy(host: str) -> bool:
    """Respeta NO_PROXY (coma-separado) por coincidencia exacta o por sufijo (.windows.net)."""
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

def parse_proxy_env(target_host: Optional[str] = None) -> Optional[Dict[str, Union[str, int]]]:
    """
    Dict de proxy para el SDK:
      {"proxy_hostname": "...", "proxy_port": 8080, "username": "...", "password": "..."}
    Fuentes: EVENTHUB_PROXY > HTTPS_PROXY > HTTP_PROXY
    Kill-switch: FORCE_NO_PROXY=1 o NO_PROXY que coincida con el host.
    """
    if os.getenv("FORCE_NO_PROXY") == "1":
        logger.info("FORCE_NO_PROXY=1: Ignorando cualquier proxy para Event Hub.")
        return None
    if target_host and _host_in_no_proxy(target_host):
        logger.info(f"NO_PROXY activo para host '{target_host}', no se aplicará proxy.")
        return None

    proxy = os.getenv("EVENTHUB_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if not proxy:
        return None

    u = urlparse(proxy)
    if not u.hostname or not u.port:
        logger.warning("Proxy inválido. Revise EVENTHUB_PROXY/HTTPS_PROXY/HTTP_PROXY (host o puerto faltante).")
        return None

    out: Dict[str, Union[str, int]] = {"proxy_hostname": u.hostname, "proxy_port": int(u.port)}
    if u.username:
        out["username"] = u.username
    if u.password:
        out["password"] = u.password
    return out

def _effective_verify() -> Union[bool, str]:
    """
    Valor robusto para connection_verify (evita errores con CA):
      - 'false'/'0'/'no'  -> False (solo pruebas)
      - 'true'/'1'/'yes'  -> CA de certifi (si existe) o True
      - ruta existente     -> se usa esa ruta
      - vacío/inválido     -> CA de certifi (si existe) o True
    """
    v = os.getenv("EVENTHUB_VERIFY")
    if v is None or not v.strip():
        if _DEFAULT_CAFILE:
            logger.info(f"TLS verify usando certifi: {_DEFAULT_CAFILE}")
            return _DEFAULT_CAFILE
        logger.info("TLS verify usando store del sistema (certifi no disponible).")
        return True

    vv = v.strip().lower()
    if vv in ("false", "0", "no"):
        logger.warning("TLS verify DESACTIVADO (solo pruebas).")
        return False
    if vv in ("true", "1", "yes"):
        if _DEFAULT_CAFILE:
            logger.info(f"TLS verify usando certifi: {_DEFAULT_CAFILE}")
            return _DEFAULT_CAFILE
        logger.info("TLS verify usando store del sistema (certifi no disponible).")
        return True

    if osp.isfile(v):
        logger.info(f"TLS verify usando CA personalizada: {v}")
        return v

    logger.warning(f"EVENTHUB_VERIFY='{v}' no es booleano ni ruta válida; usando certifi/store por defecto.")
    if _DEFAULT_CAFILE:
        logger.info(f"TLS verify usando certifi: {_DEFAULT_CAFILE}")
        return _DEFAULT_CAFILE
    return True

# ---------- Persistencia ----------
def _save_rows(rows: List[Measurement]):
    for r in rows:
        exists = (
            Measurement.query.filter_by(
                device_id=r.device_id,
                sensor_channel=r.sensor_channel,
                fechah_local=r.fechah_local,
            ).first()
            is not None
        )
    # sólo agregamos los que no existan
        if not exists:
            db.session.add(r)
    db.session.commit()

# ---------- Start position ----------
def _normalize_start_position(s: Optional[str]) -> Union[str, datetime]:
    """
    Convierte 'latest'|'earliest'|ISO datetime (Bogotá) a formato aceptado por el SDK:
      earliest -> "-1"
      latest   -> "@latest"
      ISO local-> datetime en UTC (tz-aware)
    """
    if not s:
        return "-1"
    v = s.strip().lower()
    if v in ("latest", "@latest"):
        return "@latest"
    if v in ("earliest", "-1"):
        return "-1"

    raw = s.strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            dt_local = datetime.strptime(raw, fmt)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=BOGOTA)
            return dt_local.astimezone(timezone.utc)
        except ValueError:
            continue
    logger.warning(f"No pude interpretar --from='{s}'. Usaré earliest.")
    return "-1"

# ---------- Consumidor ----------
def consume(consumer_groups: Iterable[str], start_position: Optional[str] = None):
    """
    Consume mensajes de Event Hub compatible con IoT Hub.
    :param consumer_groups: lista de consumer groups.
    :param start_position: 'latest' | 'earliest' | 'YYYY-MM-DDTHH:MM[:SS]' (hora local Bogotá).
    """
    if "EVENTHUB_CONNECTION_STRING" not in os.environ:
        raise RuntimeError("EVENTHUB_CONNECTION_STRING no está definido. Revise su .env.")

    conn_str = os.environ["EVENTHUB_CONNECTION_STRING"]

    meta = parse_conn_str(conn_str)
    logger.info(
        f"Usando EventHub compatible: host={meta['host']}, entity={meta['entity_path']}, policy={meta['sak_name']}"
    )
    if not meta["entity_path"]:
        raise RuntimeError(
            "Su connection string NO tiene EntityPath. Copie el Extremo compatible con Event Hub "
            "desde IoT Hub (Puntos de conexión integrados) y asegúrese de que incluya EntityPath=...."
        )

    http_proxy = parse_proxy_env(target_host=meta["host"])
    if http_proxy:
        logger.info(f"Proxy configurado para WebSocket: {http_proxy['proxy_hostname']}:{http_proxy['proxy_port']}")

    connection_verify = _effective_verify()

    for var in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        if os.getenv(var):
            logger.warning(f"Variable {var} detectada -> {os.getenv(var)} (podría afectar verificación TLS).")

    starting = _normalize_start_position(start_position)

    # Contexto Flask para usar ORM
    from app import create_app
    app = create_app()

    with app.app_context():
        for cg in consumer_groups:
            logger.info(f"[{cg}] Preparando conexión por AMQP/WebSocket 443…")
            logger.info(f"[{cg}] Conectando… (starting_position={starting!r})")

            client = EventHubConsumerClient.from_connection_string(
                conn_str=conn_str,
                consumer_group=cg,
                transport_type=TransportType.AmqpOverWebsocket,  # Fuerza 443
                http_proxy=http_proxy,                            # proxy (o None)
                connection_verify=connection_verify,              # False | ruta CA | True
            )

            # Métricas por minuto
            window_start = time.time()
            msgs_in_window = 0

            def _flush_metrics(force: bool = False):
                nonlocal window_start, msgs_in_window
                now = time.time()
                if force or (now - window_start) >= 60:
                    logger.info(f"[{cg}] Último minuto: {msgs_in_window} mensajes persistidos")
                    window_start = now
                    msgs_in_window = 0

            def on_event(partition_context, event):
                nonlocal msgs_in_window
                if event is None:
                    _flush_metrics()  # heartbeat
                    return
                try:
                    body = event.body_as_str(encoding="UTF-8")
                    payload = json.loads(body)

                    # deviceId desde system properties o payload
                    device_from_sys = None
                    try:
                        if getattr(event, "system_properties", None):
                            devb = event.system_properties.get(b"iothub-connection-device-id")
                            if devb:
                                device_from_sys = devb.decode() if isinstance(devb, (bytes, bytearray)) else str(devb)
                    except Exception:
                        pass

                    payload_device = payload.get("DeviceId") or payload.get("deviceId")
                    device_id = payload_device or device_from_sys

                    # Filtro opcional
                    if ALLOWED and device_id and device_id not in ALLOWED:
                        return

                    base = row_from_payload(payload, device_id_fallback=device_id)
                    rows: List[Measurement] = []

                    # Canal Um1
                    if ("n1025Um1" in payload) or ("n25100Um1" in payload):
                        rows.append(
                            Measurement(
                                **base,
                                sensor_channel=SensorChannel.Um1,
                                pm25=float(payload.get("n1025Um1")) if payload.get("n1025Um1") is not None else None,
                                pm10=float(payload.get("n25100Um1")) if payload.get("n25100Um1") is not None else None,
                            )
                        )
                    # Canal Um2
                    if ("n1025Um2" in payload) or ("n25100Um2" in payload):
                        rows.append(
                            Measurement(
                                **base,
                                sensor_channel=SensorChannel.Um2,
                                pm25=float(payload.get("n1025Um2")) if payload.get("n1025Um2") is not None else None,
                                pm10=float(payload.get("n25100Um2")) if payload.get("n25100Um2") is not None else None,
                            )
                        )

                    # Si no llegaron campos de PM, aún persistimos temp/rh en Um1
                    if not rows:
                        rows.append(Measurement(**base, sensor_channel=SensorChannel.Um1))

                    _save_rows(rows)
                    msgs_in_window += 1

                    # checkpoint solo tras persistir
                    partition_context.update_checkpoint(event)

                    _flush_metrics()
                except Exception as e:
                    logger.exception(f"Error procesando mensaje: {e}")

            def on_partition_initialize(partition_context):
                logger.info(f"[{cg}] Partición {partition_context.partition_id} inicializada.")

            try:
                with client:
                    client.receive(
                        on_event=on_event,
                        on_partition_initialize=on_partition_initialize,
                        starting_position=starting,  # "-1" earliest | "@latest" | datetime(UTC)
                        max_wait_time=60,           # heartbeat/métricas cada 60s
                    )
            except KeyboardInterrupt:
                logger.info("Ingesta interrumpida por usuario")
            except Exception as e:
                logger.exception(
                    f"Fallo de conexión (host={meta['host']}, CG={cg}, policy={meta['sak_name']}): {e}"
                )
            finally:
                try:
                    _flush_metrics(force=True)
                except Exception:
                    pass
