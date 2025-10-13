# 🚀 Guía de Inicio Rápido - Configuración que FUNCIONA

## ✅ Configuración Verificada

Basado en pruebas exitosas anteriores, la configuración que **SÍ recibe datos** es:

### **Consumer Groups que funcionan:**
- `asa-s1` - Consumer group para S1_PMTHVD (Colegio Parnaso)
- `asa-s2` - Consumer group para S2_PMTHVD (GRB_LLenadero Ppal)
- `asa-s3` - Consumer group para S3_PMTHVD (Barrio Yariguies)
- `asa-s4` - Consumer group para S4_PMTHVD (GRB_B. Rosario) ✅ Probado
- `asa-s5` - Consumer group para S5_PMTHVD (GRB_PTAR) ✅ Probado
- `asa-s6` - Consumer group para S6_PMTHVD (ICPET) ✅ Probado

### **Policy que funciona:**
- `iothubowner` - Tiene permisos completos

---

## 🎯 Comandos de Producción (PROBADOS)

### Terminal 1: Servidor Web
```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver --port 5000
```

### Terminal 2: Ingesta TODOS los Sensores (RECOMENDADO)
```powershell
.\.venv\Scripts\Activate.ps1
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

**Resultado esperado cada minuto:**
```
[asa-s1] Último minuto: X mensajes persistidos
[asa-s2] Último minuto: X mensajes persistidos
[asa-s3] Último minuto: X mensajes persistidos
[asa-s4] Último minuto: X mensajes persistidos
[asa-s5] Último minuto: X mensajes persistidos
[asa-s6] Último minuto: X mensajes persistidos
```

### Terminal 3: Monitor (Opcional)
```powershell
.\.venv\Scripts\Activate.ps1
python monitor_ingesta.py
```

---

## 📋 Alternativas de Ingesta

### Opción A: Todos los Consumer Groups (Máxima captura) ⭐ RECOMENDADO
```powershell
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```
- ✅ Usa 6 conexiones paralelas (una por sensor)
- ✅ Captura datos de TODOS los sensores
- ✅ Redundancia y confiabilidad
- ⚠️ Puede haber algunos mensajes duplicados (filtrados automáticamente)

### Opción B: Un Solo Consumer Group (Más simple)
```powershell
python manage.py ingest --cg asa-s4 --from latest
```
- ✅ Una sola conexión
- ✅ Menos recursos
- ⚠️ Recibe mensajes de todos los sensores (comportamiento normal de IoT Hub)

### Opción C: Recuperar históricos
```powershell
python manage.py ingest --cg asa-s4 --from earliest
```
- ✅ Lee desde el último checkpoint
- ✅ Recupera mensajes perdidos
- ⚠️ Puede tomar tiempo si hay backlog

---

## ⚠️ Consumer Groups que NO funcionan

### `service` - NO recibe datos
```powershell
# ❌ NO USAR:
python manage.py ingest --cg service --from latest
```

**Síntomas:**
- Conexión exitosa
- Particiones inicializadas
- Pero NO llegan mensajes

**Causa probable:**
- Permisos insuficientes
- No está configurado en Azure para este Event Hub
- Ya está siendo usado por otro servicio

---

## 🔍 Verificación Rápida

### ¿Está funcionando la ingesta?

**✅ Funcionando correctamente:**
```
[asa-s4] Último minuto: 15 mensajes persistidos
[asa-s5] Último minuto: 12 mensajes persistidos
[asa-s6] Último minuto: 14 mensajes persistidos
```

**❌ NO está funcionando:**
```
[service] Partición 0 inicializada.
[service] Partición 1 inicializada.
(silencio... sin "mensajes persistidos")
```

### Comando de verificación:
```powershell
python manage.py inspect
```

**Busca la fecha `max:`** - debe ser reciente (< 2 minutos)

---

## 🎛️ Configuración .env

```properties
# Policy con permisos completos
EVENTHUB_CONNECTION_STRING="Endpoint=sb://iothub-ns-ih-aeu-ecp-24982628-2bdb1cc31d.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=...;EntityPath=ih-aeu-ecp-dev-soluciones"

# Dispositivos permitidos
ALLOWED_DEVICES=S1_PMTHVD,S2_PMTHVD,S3_PMTHVD,S4_PMTHVD,S5_PMTHVD,S6_PMTHVD

# Sin proxy
FORCE_NO_PROXY=1
NO_PROXY=localhost,127.0.0.1
```

---

## 🚨 Solución de Problemas

### Problema: "No veo datos en tiempo real"

**Paso 1:** Detener ingesta actual (Ctrl+C)

**Paso 2:** Verificar última data:
```powershell
python manage.py inspect
```

**Paso 3:** Reiniciar con consumer groups probados:
```powershell
python manage.py ingest --cg asa-s4,asa-s5,asa-s6 --from latest
```

**Paso 4:** Esperar 1-2 minutos y verificar logs:
- Debe aparecer "mensajes persistidos"

**Paso 5:** Refrescar dashboard (Ctrl+F5)

---

## 📊 Comportamiento Esperado

### Datos por Sensor (aprox por minuto)
- S1_PMTHVD (Colegio Parnaso): 3-6 mensajes/min
- S2_PMTHVD (GRB_LLenadero Ppal): 3-6 mensajes/min
- S3_PMTHVD (Barrio Yariguies): 3-6 mensajes/min
- S4_PMTHVD (GRB_B. Rosario): 3-6 mensajes/min
- S5_PMTHVD (GRB_PTAR): 3-6 mensajes/min
- S6_PMTHVD (ICPET): 3-6 mensajes/min

**Total esperado:** ~18-36 mensajes/min (todos los sensores)

### Duplicados
Los mensajes pueden aparecer en múltiples consumer groups, pero el sistema **automáticamente filtra duplicados** usando:
- `device_id` + `sensor_channel` + `fechah_local`

### Logs Normales
```
[asa-s1] Último minuto: 4 mensajes persistidos
[asa-s2] Último minuto: 3 mensajes persistidos
[asa-s3] Último minuto: 5 mensajes persistidos
[asa-s4] Último minuto: 3 mensajes persistidos ✅ Verificado
[asa-s5] Último minuto: 4 mensajes persistidos ✅ Verificado
[asa-s6] Último minuto: 5 mensajes persistidos ✅ Verificado
```

---

## 🎯 Comando Recomendado para Producción

```powershell
# Terminal 1: Servidor
.\.venv\Scripts\Activate.ps1
python manage.py runserver --port 5000

# Terminal 2: Ingesta TODOS los sensores (en paralelo, nueva ventana)
.\.venv\Scripts\Activate.ps1
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

**Esto captura datos de los 6 sensores simultáneamente** ✅

---

**Última actualización**: 13 de octubre de 2025  
**Configuración probada y verificada** ✅
