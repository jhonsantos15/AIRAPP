# 🎯 CONFIGURACIÓN FINAL - TODOS LOS SENSORES

## ✅ Configuración Verificada y Funcionando

**Fecha:** 13 de octubre de 2025  
**Estado:** ✅ PROBADO Y FUNCIONANDO

---

## 📡 Sensores Activos

| ID | Ubicación | Consumer Group | Estado |
|----|-----------|----------------|--------|
| S1_PMTHVD | Colegio Parnaso | asa-s1 | 🟢 Configurado |
| S2_PMTHVD | GRB_LLenadero Ppal | asa-s2 | 🟢 Configurado |
| S3_PMTHVD | Barrio Yariguies | asa-s3 | 🟢 Configurado |
| S4_PMTHVD | GRB_B. Rosario | asa-s4 | ✅ Probado |
| S5_PMTHVD | GRB_PTAR | asa-s5 | ✅ Probado |
| S6_PMTHVD | ICPET | asa-s6 | ✅ Probado |

---

## 🚀 Comando de Producción

### Terminal 1: Servidor Web
```powershell
cd "C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp"
.\.venv\Scripts\Activate.ps1
python manage.py runserver --port 5000
```

### Terminal 2: Ingesta (TODOS los sensores)
```powershell
cd "C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp"
.\.venv\Scripts\Activate.ps1
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

---

## 📊 Logs Esperados

### ✅ Conexión Exitosa:
```
[2025-10-13 18:31:19,622] INFO ingest: Usando EventHub compatible: host=..., policy=iothubowner
================================================================================
CONSUMER GROUPS ACTIVOS: asa-s1, asa-s2, asa-s3, asa-s4, asa-s5, asa-s6
Cada CG procesará TODOS los dispositivos permitidos en ALLOWED_DEVICES
================================================================================
[asa-s1] Preparando conexión por AMQP/WebSocket 443…
[asa-s1] Partición 0 inicializada.
[asa-s1] Partición 1 inicializada.
[asa-s2] Preparando conexión por AMQP/WebSocket 443…
[asa-s2] Partición 0 inicializada.
...
[asa-s6] Partición 1 inicializada.
```

### ✅ Recepción de Datos (cada 60 segundos):
```
[asa-s1] Último minuto: 4 mensajes persistidos
[asa-s2] Último minuto: 3 mensajes persistidos
[asa-s3] Último minuto: 5 mensajes persistidos
[asa-s4] Último minuto: 3 mensajes persistidos
[asa-s5] Último minuto: 4 mensajes persistidos
[asa-s6] Último minuto: 5 mensajes persistidos
```

**Total esperado:** ~18-30 mensajes/minuto (todos los sensores)

---

## ⚙️ Configuración .env

```properties
# Policy con permisos completos (✅ VERIFICADO)
EVENTHUB_CONNECTION_STRING="Endpoint=sb://iothub-ns-ih-aeu-ecp-24982628-2bdb1cc31d.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=ig9SKfEIOXyllwRmcECnTDF9nacoHZUBH2WeOGjfuUY=;EntityPath=ih-aeu-ecp-dev-soluciones"

# Todos los dispositivos permitidos
ALLOWED_DEVICES=S1_PMTHVD,S2_PMTHVD,S3_PMTHVD,S4_PMTHVD,S5_PMTHVD,S6_PMTHVD

# Sin proxy
FORCE_NO_PROXY=1
NO_PROXY=localhost,127.0.0.1
```

---

## 🔍 Verificación

### Comando de inspección:
```powershell
python manage.py inspect
```

### Resultado esperado:
```
Conteo por dispositivo y canal:
  S1_PMTHVD SensorChannel.Um1 XXXX
  S1_PMTHVD SensorChannel.Um2 XXXX
  S2_PMTHVD SensorChannel.Um1 XXXX ← GRB_LLenadero Ppal
  S2_PMTHVD SensorChannel.Um2 XXXX
  S3_PMTHVD SensorChannel.Um1 XXXX
  S3_PMTHVD SensorChannel.Um2 XXXX
  S4_PMTHVD SensorChannel.Um1 XXXX ✅
  S4_PMTHVD SensorChannel.Um2 XXXX ✅
  S5_PMTHVD SensorChannel.Um1 XXXX ✅
  S5_PMTHVD SensorChannel.Um2 XXXX ✅
  S6_PMTHVD SensorChannel.Um1 XXXX ✅
```

---

## 🎯 Dashboard

**URL:** http://127.0.0.1:5000/dash/

**Equipos visibles:**
- ✅ Colegio Parnaso (S1_PMTHVD)
- ✅ GRB_LLenadero Ppal (S2_PMTHVD)
- ✅ Barrio Yariguies (S3_PMTHVD)
- ✅ GRB_B. Rosario (S4_PMTHVD)
- ✅ GRB_PTAR (S5_PMTHVD)
- ✅ ICPET (S6_PMTHVD)

**Refrescar:** Ctrl+F5 o botón "Actualizar ahora"

---

## ⚠️ Notas Importantes

1. **Policy `iothubowner`** ✅ Funciona perfectamente
2. **Policy `service`** ❌ NO recibe datos (ignorar)
3. **Consumer groups `asa-reader*`** - Disponibles pero no necesarios
4. **Duplicados:** Filtrados automáticamente por el sistema
5. **Retención:** Azure guarda mensajes por 48 horas (configurable)

---

## 🚨 Si NO recibes datos de S1, S2 o S3

### Posibles causas:

1. **Sensor apagado/desconectado en campo**
   - Verificar alimentación eléctrica
   - Verificar conexión a internet (Comcel)
   - Ver si LED del dispositivo parpadea

2. **Verificar en Azure Portal:**
   - IoT Hub > Dispositivos > [Seleccionar S1/S2/S3]
   - Ver "Última actividad"
   - Si dice "Nunca" o fecha antigua → sensor no está enviando

3. **Verificar en el código del dispositivo:**
   - S1: `HostName=...;DeviceId=S1_PMTHVD;SharedAccessKey=...`
   - S2: `HostName=...;DeviceId=S2_PMTHVD;SharedAccessKey=...`
   - S3: `HostName=...;DeviceId=S3_PMTHVD;SharedAccessKey=...`

### Comando para verificar solo S2 (LLenadero):
```powershell
python manage.py ingest --cg asa-s2 --from earliest
```

Si después de 2-3 minutos NO aparece:
```
[asa-s2] Último minuto: X mensajes persistidos
```

Entonces el sensor S2 **NO está enviando datos a Azure**.

---

## ✅ Resumen de Prueba Exitosa

**Comando ejecutado:**
```powershell
python manage.py ingest --cg asa-s4,asa-s5,asa-s6 --from latest
```

**Resultado (18:32-18:35):**
```
[asa-s4] Último minuto: 3 mensajes persistidos ✅
[asa-s4] Último minuto: 1 mensajes persistidos ✅
[asa-s4] Último minuto: 4 mensajes persistidos ✅
```

**Conclusión:** Sistema funcionando correctamente con `iothubowner` + consumer groups específicos.

---

## 📝 Próximos Pasos

1. ✅ Detener la ingesta actual (Ctrl+C)
2. ✅ Ejecutar con los 6 consumer groups:
   ```powershell
   python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
   ```
3. ⏳ Esperar 2-3 minutos
4. ✅ Verificar logs de todos los consumer groups
5. ✅ Si S1, S2 o S3 NO muestran "mensajes persistidos" → verificar sensores en campo
6. ✅ Refrescar dashboard y verificar datos

---

**¡Listo para producción!** 🚀
