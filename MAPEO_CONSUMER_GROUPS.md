# � Arquitectura Azure IoT Hub - Consumer Groups

## 📋 Resumen

Esta aplicación consume datos de **Azure IoT Hub** donde **todos los dispositivos publican al mismo endpoint**. Los consumer groups permiten **múltiples lectores independientes** del mismo stream de datos.

### ✅ **Arquitectura Implementada: Consumer Groups Compartidos**

- Cada consumer group **lee mensajes de TODOS los dispositivos**
- Filtrado por `ALLOWED_DEVICES` para procesar solo sensores autorizados
- Múltiples consumer groups pueden leer en paralelo sin interferencia

---

## 🗺️ Dispositivos en Campo

| Device ID    | Ubicación              | Connection String                          |
|--------------|------------------------|--------------------------------------------|
| `S1_PMTHVD`  | Colegio Parnaso        | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S1_PMTHVD |
| `S2_PMTHVD`  | GRB_LLenadero Ppal     | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S2_PMTHVD |
| `S3_PMTHVD`  | Barrio Yariguies       | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S3_PMTHVD |
| `S4_PMTHVD`  | GRB_B. Rosario         | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S4_PMTHVD |
| `S5_PMTHVD`  | GRB_PTAR               | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S5_PMTHVD |
| `S6_PMTHVD`  | ICPET                  | HostName=IH-AEU-ECP-DEV-SOLUCIONES-NATURALES-CLIMA.azure-devices.net;DeviceId=S6_PMTHVD |

**Todos los dispositivos → Mismo IoT Hub → Mismo Event Hub Endpoint**

---

## 🎯 Consumer Groups Disponibles

Según configuración de Azure:
- `service` - Policy de lectura para aplicaciones (⭐ **RECOMENDADO**)
- `asa-reader`, `asa-reader1-4` - Lectores adicionales para Azure Stream Analytics

### Consumer Group Recomendado para Visualización

```bash
python manage.py ingest --cg service --from latest
```

**Ventajas:**
- ✅ Un solo consumer group lee **todos los dispositivos**
- ✅ Sin duplicación de mensajes
- ✅ Menor overhead de conexiones
- ✅ Escalable para agregar nuevos sensores

---

## 📝 Uso

### 1. **Ingesta con un solo Consumer Group** (⭐ RECOMENDADO)
```bash
python manage.py ingest --cg service --from latest
```
**Resultado:** Lee mensajes de S1, S2, S3, S4, S5, S6 todos juntos

### 2. **Múltiples Consumer Groups en paralelo** (para redundancia)
```bash
# Terminal 1
python manage.py ingest --cg service --from latest

# Terminal 2 (opcional, para testing o backup)
python manage.py ingest --cg asa-reader1 --from latest
```
**Resultado:** Ambos consumer groups leen los mismos mensajes independientemente

---

## 🔍 Cómo Funciona Azure IoT Hub

```
┌─────────────┐
│   S1_PMTHVD │──┐
└─────────────┘  │
┌─────────────┐  │
│   S2_PMTHVD │──┤
└─────────────┘  │
┌─────────────┐  ├──► Azure IoT Hub ──► Event Hub Endpoint
│   S3_PMTHVD │──┤                            │
└─────────────┘  │                            ├──► Consumer Group: service (TODOS los mensajes)
┌─────────────┐  │                            ├──► Consumer Group: asa-reader1 (TODOS los mensajes)
│   S4_PMTHVD │──┤                            └──► Consumer Group: asa-reader2 (TODOS los mensajes)
└─────────────┘  │
┌─────────────┐  │
│   S5_PMTHVD │──┤
└─────────────┘  │
┌─────────────┐  │
│   S6_PMTHVD │──┘
└─────────────┘
```

**Puntos clave:**
- Todos los devices publican al **mismo IoT Hub**
- IoT Hub reenvía a un **Event Hub endpoint compartido**
- Consumer groups son **lectores independientes** del mismo stream
- NO hay mapeo 1:1 entre consumer groups y dispositivos
- El filtrado se hace en la **aplicación** mediante `ALLOWED_DEVICES`

---

## ⚙️ Configuración

### `.env`
```properties
# Policy "service" con permiso de lectura
EVENTHUB_CONNECTION_STRING="Endpoint=sb://...;SharedAccessKeyName=service;SharedAccessKey=...;EntityPath=ih-aeu-ecp-dev-soluciones"

# Dispositivos permitidos (filtra en la aplicación)
ALLOWED_DEVICES=S1_PMTHVD,S2_PMTHVD,S3_PMTHVD,S4_PMTHVD,S5_PMTHVD,S6_PMTHVD
```

---

## 📊 Logs Esperados

```
[INFO] Usando EventHub compatible: host=..., entity=ih-aeu-ecp-dev-soluciones, policy=service
================================================================================
CONSUMER GROUPS ACTIVOS: service
Cada CG procesará TODOS los dispositivos permitidos en ALLOWED_DEVICES
================================================================================
[service] Preparando conexión por AMQP/WebSocket 443…
[service] Conectando… (starting_position='@latest')
[service] Partición 0 inicializada.
[service] Partición 1 inicializada.
[service] Último minuto: 120 mensajes persistidos
```

---

## ❓ FAQ

### ¿Por qué asa-s4 recibe mensajes de S6_PMTHVD?
**R:** Es comportamiento normal. En Azure IoT Hub, todos los consumer groups reciben mensajes de todos los dispositivos. Los consumer groups **NO filtran por dispositivo**.

### ¿Cuántos consumer groups necesito?
**R:** Para visualización en tiempo real: **uno solo** (`service`). Múltiples consumer groups solo si necesitas:
- Procesamiento paralelo independiente
- Redundancia/backup
- Diferentes aplicaciones leyendo simultáneamente

### ¿Cómo filtro por dispositivo?
**R:** La aplicación ya filtra usando `ALLOWED_DEVICES` en el `.env`. Los mensajes de dispositivos no permitidos se ignoran automáticamente.

### ¿Puedo usar múltiples consumer groups?
**R:** Sí, pero **todos leerán los mismos mensajes**. Útil para:
- Diferentes entornos (dev, test, prod)
- Procesamiento paralelo de datos
- Backup/redundancia

---

**Fecha de actualización**: 13 de octubre de 2025  
**Policy recomendado**: `service`  
**Arquitectura**: Consumer Groups Compartidos ✅

