# 📡 Arquitectura IoT - Conexión Azure y Sensores

## 🎯 Resumen Ejecutivo

Tu aplicación **AireApp** tiene **6 sensores de calidad del aire** conectados a **Azure IoT Hub** que envían datos de material particulado (PM2.5 y PM10), temperatura y humedad en tiempo real.

---

## 🌐 Los 6 Sensores de Campo

### Dispositivos Configurados

| ID Dispositivo | Ubicación | Consumer Group | Color |
|---------------|-----------|----------------|-------|
| **S1_PMTHVD** | Colegio Parnaso | $Default | 🔴 #FF6B6B |
| **S2_PMTHVD** | GRB_LLenadero Ppal | $Default | 🟠 #FFA500 |
| **S3_PMTHVD** | GRB_B. Yariguies | $Default | 🟡 #FFD700 |
| **S4_PMTHVD** | GRB_B. Rosario | asa-s4 | 🔴 #E74C3C |
| **S5_PMTHVD** | GRB_PTAR | asa-s5 | 🟠 #F39C12 |
| **S6_PMTHVD** | ICPET | asa-s6 | 🔵 #3498DB |

> 📍 **Definidos en:** `src/utils/labels.py` y `src/utils/constants.py`

---

## 📊 Variables que Mide Cada Sensor

### Datos por Sensor

Cada sensor físico tiene **2 canales de medición** (Um1 y Um2) con las siguientes variables:

```python
# 🌡️ Variables Ambientales (compartidas por ambos canales)
temp  : float  # Temperatura en °C
rh    : float  # Humedad relativa (%)

# 💨 Material Particulado (específico por canal)
# Canal Um1 (Sensor 1):
n1025Um1   : float  # PM2.5 del sensor 1 (partículas 1.0-2.5 µm)
n25100Um1  : float  # PM10 del sensor 1 (partículas 2.5-10 µm)

# Canal Um2 (Sensor 2):
n1025Um2   : float  # PM2.5 del sensor 2 (partículas 1.0-2.5 µm)
n25100Um2  : float  # PM10 del sensor 2 (partículas 2.5-10 µm)

# 🏭 Gases Contaminantes
n0310Um1   : float  # NO2 - Dióxido de Nitrógeno (partículas 0.3-1.0 µm)
n0310Um2   : float  # CO2 - Dióxido de Carbono (partículas 0.3-1.0 µm)

# 🌬️ Variables de Viento
vel        : float  # Velocidad del viento (m/s o km/h)
dir        : float  # Dirección del viento en grados (0-360°)
```

### Variables Adicionales del Payload

```python
DeviceId  : str       # ID del dispositivo (ej: "S4_PMTHVD")
Fecha     : str       # Fecha "YYYY-MM-DD" o "DD/MM/YYYY"
Hora      : str       # Hora "HH:MM:SS"
FechaH    : str       # Timestamp combinado "YYYY-MM-DDTHH:MM:SS"
DOY       : int       # Día del año (1-366)
W         : float     # Peso o factor adicional
```

> 📍 **Definidos en:** `src/iot/processor.py` (líneas 104-136)

---

## 🔄 Flujo de Datos IoT

### 1️⃣ Dispositivos de Campo → Azure IoT Hub

```
[Sensor S1-S6] --JSON--> [Azure IoT Hub] --Event Hub--> [Consumer]
```

Cada sensor envía un **payload JSON** cada minuto aproximadamente.

**Ejemplo de Payload:**
```json
{
  "DeviceId": "S4_PMTHVD",
  "FechaH": "2025-10-15T10:30:00",
  "Fecha": "2025-10-15",
  "Hora": "10:30:00",
  "temp": 24.5,
  "hr": 65.2,
  "n1025Um1": 12.3,
  "n25100Um1": 18.7,
  "n1025Um2": 11.8,
  "n25100Um2": 17.9,
  "n0310Um1": 45.2,
  "n0310Um2": 410.5,
  "vel": 3.5,
  "dir": 180.0,
  "DOY": 288,
  "W": 1.0
}
```

---

### 2️⃣ Azure IoT Hub → Event Hub Consumer

**Archivo:** `src/iot/consumer.py`

```python
class EventHubConsumer:
    """Consumidor de Azure Event Hub compatible con IoT Hub"""
    
    def __init__(self, connection_string, consumer_group="$Default"):
        # 🔌 Conexión vía EVENTHUB_CONNECTION_STRING
        # 🔐 Maneja autenticación, proxy, TLS
        # 📡 Consumer groups para paralelizar lectura
```

**Configuración de Conexión:**
- **Connection String:** Variable de entorno `EVENTHUB_CONNECTION_STRING`
- **Consumer Group:** Define qué stream leer (`$Default`, `asa-s4`, `asa-s5`, `asa-s6`)
- **Proxy:** Soporta `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`
- **TLS:** Verificación SSL con certifi

**Métodos Principales:**
- `_parse_connection_string()`: Extrae host, EntityPath, SharedAccessKey
- `_get_proxy_config()`: Configura proxy si es necesario
- `_get_tls_verify()`: Configura certificados SSL
- `receive_events()`: Inicia la escucha de eventos

---

### 3️⃣ Procesamiento de Payloads

**Archivo:** `src/iot/processor.py`

```python
class PayloadProcessor:
    """Procesa payloads JSON y los convierte en Measurements"""
    
    def process_event(self, event) -> List[Measurement]:
        # 1. Parsea JSON del evento
        # 2. Extrae device_id desde system properties o payload
        # 3. Filtra por allowed_devices (opcional)
        # 4. Crea 1-2 Measurements (Um1 y/o Um2)
```

**Lógica de Canales:**
```python
# Si hay datos de Um1 → crea Measurement con sensor_channel=Um1
if "n1025Um1" in payload or "n25100Um1" in payload:
    rows.append(Measurement(
        sensor_channel=SensorChannel.Um1,
        pm25=payload.get("n1025Um1"),
        pm10=payload.get("n25100Um1"),
        temp=payload.get("temp"),
        rh=payload.get("hr"),
        ...
    ))

# Si hay datos de Um2 → crea Measurement con sensor_channel=Um2
if "n1025Um2" in payload or "n25100Um2" in payload:
    rows.append(Measurement(
        sensor_channel=SensorChannel.Um2,
        pm25=payload.get("n1025Um2"),
        pm10=payload.get("n25100Um2"),
        temp=payload.get("temp"),
        rh=payload.get("hr"),
        ...
    ))
```

**Resultado:** Un evento puede generar hasta **2 registros** en la BD (uno por cada canal Um1/Um2).

---

### 4️⃣ Persistencia en Base de Datos

**Archivo:** `src/core/models.py`

```python
class Measurement(db.Model):
    """Modelo de medición de calidad del aire"""
    
    # Identificación
    device_id: str              # ej: "S4_PMTHVD"
    sensor_channel: SensorChannel  # Um1 o Um2
    
    # Mediciones - Material Particulado
    pm25: float                 # Material particulado 2.5 µm
    pm10: float                 # Material particulado 10 µm
    
    # Mediciones - Ambientales
    temp: float                 # Temperatura °C
    rh: float                   # Humedad relativa %
    
    # Mediciones - Gases
    no2: float                  # Dióxido de Nitrógeno (ppb o µg/m³)
    co2: float                  # Dióxido de Carbono (ppm)
    
    # Mediciones - Viento
    vel_viento: float           # Velocidad del viento (m/s)
    dir_viento: float           # Dirección del viento (grados 0-360)
    
    # Timestamps (zona horaria Bogotá)
    fecha: date                 # Fecha local
    hora: time                  # Hora local
    fechah_local: datetime      # Timestamp completo
    
    # Metadatos
    doy: int                    # Día del año
    w: float                    # Peso
    raw_json: str              # Payload original
```

**Constraint de Duplicados:**
```sql
UNIQUE (device_id, sensor_channel, fechah_local)
```
Previene duplicados por dispositivo + canal + timestamp.

---

### 5️⃣ Servicio IoT Hub (Orquestador)

**Archivo:** `src/services/iot_hub_service.py`

```python
class IoTHubService:
    """Orquesta Consumer, Processor, Monitor y BD"""
    
    def __init__(self, consumer_group="$Default", allowed_devices=None):
        self.consumer = EventHubConsumer(consumer_group)
        self.processor = PayloadProcessor(allowed_devices)
        self.monitor = HealthMonitor()
        self.batch_buffer = []  # Buffer para batch inserts
    
    def _on_event(self, partition_context, event):
        # 1. Recibe evento de Event Hub
        # 2. Procesa con PayloadProcessor → List[Measurement]
        # 3. Acumula en batch_buffer
        # 4. Cuando llega a batch_size → guarda en BD
        # 5. Checkpoint periódico para no reprocesar
```

**Batch Processing:**
- Acumula hasta `batch_size` (default: 50) mediciones
- Guarda en bloque con `MeasurementService.save_measurements()`
- Evita duplicados (constraint de BD)
- Checkpoints cada 30 segundos

---

## 🚀 Cómo se Inicia el Consumer

### Script de Inicio

**Archivo:** `scripts/start_iot_consumer.py`

```bash
# Consumir desde el principio (todos los datos históricos)
python scripts/start_iot_consumer.py --from earliest

# Consumir solo nuevos datos
python scripts/start_iot_consumer.py --from latest

# Consumir desde fecha específica
python scripts/start_iot_consumer.py --from "2025-10-15 00:00:00"

# Consumer group específico (para S4)
python scripts/start_iot_consumer.py --cg asa-s4 --from latest

# Con configuración personalizada
python scripts/start_iot_consumer.py \
  --cg asa-s5 \
  --from "2025-10-01 00:00:00" \
  --batch-size 100 \
  --checkpoint-interval 60
```

### Variables de Entorno Requeridas

**Archivo:** `.env`

```bash
# ⚡ OBLIGATORIO: Connection string de IoT Hub
EVENTHUB_CONNECTION_STRING="Endpoint=sb://tu-iothub.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=xxxxx;EntityPath=tu-hub-name"

# 🎯 Filtro de dispositivos (opcional, CSV)
ALLOWED_DEVICES="S4_PMTHVD,S5_PMTHVD,S6_PMTHVD"

# 🌐 Proxy (opcional)
HTTP_PROXY="http://proxy.empresa.com:8080"
HTTPS_PROXY="http://proxy.empresa.com:8080"
NO_PROXY="localhost,127.0.0.1,.local"
FORCE_NO_PROXY=0  # 1 para deshabilitar proxy

# 🔒 TLS
EVENTHUB_VERIFY=true  # true/false o ruta a CA bundle
```

---

## 📈 Monitoreo y Métricas

**Archivo:** `src/iot/monitoring.py`

```python
class HealthMonitor:
    """Monitorea la salud del consumer"""
    
    # Métricas rastreadas:
    - messages_received    # Total recibidos
    - messages_processed   # Procesados exitosamente
    - messages_saved       # Guardados en BD
    - duplicates_skipped   # Duplicados omitidos
    - errors               # Errores de procesamiento
    - batches_saved        # Batches guardados
    - last_message_at      # Último mensaje recibido
```

**Logs Automáticos:**
```
📊 [asa-s4] Received: 1250 | Processed: 1200 | Saved: 1180 | Duplicates: 20 | Errors: 0
```

---

## 🎨 Identificación de Sensores en el Sistema

### Por Device ID

```python
from src.utils.labels import label_for, get_all_devices

# Obtener nombre amigable
label_for("S4_PMTHVD")  # → "GRB_B. Rosario"

# Lista de todos los dispositivos
get_all_devices()  # → ["S1_PMTHVD", "S2_PMTHVD", ..., "S6_PMTHVD"]
```

### Por Color (Dashboard)

```python
from src.utils.constants import DEVICE_COLORS

DEVICE_COLORS["S4_PMTHVD"]  # → "#E74C3C" (rojo intenso)
```

### Por Consumer Group

```python
from src.utils.constants import KAFKA_CONSUMER_GROUPS

KAFKA_CONSUMER_GROUPS["S4_PMTHVD"]  # → "asa-s4"
```

---

## 🔍 Extracción del Device ID

El sistema extrae el `device_id` de 2 formas (prioridad descendente):

### 1. Desde System Properties (Azure IoT Hub)
```python
device_id = event.system_properties.get(b"iothub-connection-device-id")
# Ejemplo: b"S4_PMTHVD" → "S4_PMTHVD"
```

### 2. Desde Payload JSON
```python
device_id = payload.get("DeviceId") or payload.get("deviceId")
# Ejemplo: {"DeviceId": "S4_PMTHVD"}
```

**Fallback:** Si no se encuentra, usa `device_id_fallback` o `"UNKNOWN"`

---

## 📦 Estructura de Datos Almacenados

### Tabla: `measurements`

```sql
CREATE TABLE measurements (
    id INTEGER PRIMARY KEY,
    device_id VARCHAR(64),           -- "S4_PMTHVD"
    sensor_channel ENUM,             -- "Um1" o "Um2"
    
    -- Material Particulado
    pm25 FLOAT,                      -- Material particulado 2.5 µm
    pm10 FLOAT,                      -- Material particulado 10 µm
    
    -- Variables Ambientales
    temp FLOAT,                      -- Temperatura °C
    rh FLOAT,                        -- Humedad relativa %
    
    -- Gases Contaminantes
    no2 FLOAT,                       -- Dióxido de Nitrógeno
    co2 FLOAT,                       -- Dióxido de Carbono
    
    -- Variables de Viento
    vel_viento FLOAT,                -- Velocidad del viento
    dir_viento FLOAT,                -- Dirección del viento (grados)
    
    fecha DATE,                      -- Fecha local (Bogotá)
    hora TIME,                       -- Hora local (Bogotá)
    fechah_local TIMESTAMP,          -- Timestamp con zona horaria
    
    doy INTEGER,                     -- Día del año (1-366)
    w FLOAT,                         -- Peso
    
    raw_json TEXT,                   -- Payload JSON original
    created_at TIMESTAMP DEFAULT NOW,
    
    UNIQUE(device_id, sensor_channel, fechah_local)
);

-- Índices para consultas rápidas
CREATE INDEX idx_fechah_local ON measurements(fechah_local);
CREATE INDEX idx_device_fecha ON measurements(device_id, fecha);
CREATE INDEX idx_duplicate_check ON measurements(device_id, sensor_channel, fechah_local);
```

### Ejemplo de Registros

Un payload con ambos canales genera 2 registros:

```
id | device_id  | sensor_channel | pm25 | pm10 | temp | rh   | no2  | co2   | vel_viento | dir_viento | fechah_local
---|------------|----------------|------|------|------|------|------|-------|------------|------------|------------------
1  | S4_PMTHVD  | Um1            | 12.3 | 18.7 | 24.5 | 65.2 | 45.2 | 410.5 | 3.5        | 180.0      | 2025-10-15 10:30
2  | S4_PMTHVD  | Um2            | 11.8 | 17.9 | 24.5 | 65.2 | 45.2 | 410.5 | 3.5        | 180.0      | 2025-10-15 10:30
```

---

## 🧪 Testing y Debugging

### Verificar Datos Recientes

```bash
python scripts/check_recent_data.py
```

### Verificar Dispositivos Activos

```bash
python scripts/check_devices.py
```

### Verificar Datos del Día

```bash
python scripts/check_data_today.py
```

---

## 🔧 Componentes Clave del Sistema

| Componente | Archivo | Responsabilidad |
|-----------|---------|-----------------|
| **Consumer** | `src/iot/consumer.py` | Conexión con Azure Event Hub |
| **Processor** | `src/iot/processor.py` | Parseo de payloads JSON |
| **Monitor** | `src/iot/monitoring.py` | Métricas y salud del sistema |
| **Service** | `src/services/iot_hub_service.py` | Orquestación de componentes |
| **Models** | `src/core/models.py` | Esquema de BD y enums |
| **Config** | `src/core/config.py` | Configuración centralizada |
| **Labels** | `src/utils/labels.py` | Nombres amigables |
| **Constants** | `src/utils/constants.py` | Colores, grupos, variables |

---

## 📚 Resumen Técnico

### ¿Cómo llama a los sensores de campo?

**No los llama directamente.** Los sensores **envían datos a Azure IoT Hub** de forma continua (push), y la aplicación **consume** estos datos vía Event Hub.

### Flujo simplificado:

```
[Sensor] → Azure IoT Hub → Event Hub → EventHubConsumer 
         → PayloadProcessor → Measurement → Base de Datos
```

### Variables clave por sensor:

```python
# Cada sensor físico tiene 2 canales (Um1, Um2)
# 4 variables de material particulado:
n1025Um1, n25100Um1  # Canal 1: PM2.5 y PM10
n1025Um2, n25100Um2  # Canal 2: PM2.5 y PM10

# 2 variables ambientales (compartidas):
temp  # Temperatura
hr    # Humedad relativa

# 2 variables de gases contaminantes:
n0310Um1  # NO2 - Dióxido de Nitrógeno
n0310Um2  # CO2 - Dióxido de Carbono

# 2 variables de viento:
vel   # Velocidad del viento
dir   # Dirección del viento (0-360°)
```

### Identificación de sensores:

```python
# 6 dispositivos con IDs únicos:
S1_PMTHVD, S2_PMTHVD, S3_PMTHVD
S4_PMTHVD, S5_PMTHVD, S6_PMTHVD

# Cada uno con:
- Nombre amigable (ubicación)
- Color único (visualización)
- Consumer group (paralelización)
```

---

## 🎯 Próximos Pasos Sugeridos

1. **Monitoreo en Tiempo Real**: Dashboard con métricas del consumer
2. **Alertas**: Notificaciones cuando sensores dejan de enviar datos
3. **Validación de Calidad**: Detectar lecturas anómalas o fuera de rango
4. **Redundancia**: Comparar Um1 vs Um2 para detectar sensores defectuosos
5. **Agregación**: Pre-calcular promedios horarios/diarios para consultas rápidas

---

## 📞 Soporte

Para más detalles técnicos, consulta:
- Documentación de Azure IoT Hub: https://docs.microsoft.com/azure/iot-hub/
- Documentación de Event Hub: https://docs.microsoft.com/azure/event-hubs/
- Código fuente: `src/iot/` y `src/services/`

---

**Generado el:** 15 de octubre de 2025  
**Versión:** 1.0
