# 🔧 Troubleshooting - No veo datos en tiempo real

## 🎯 Problema: Dashboard no se actualiza

### Paso 1: Verificar última actualización en BD

```bash
python manage.py inspect
```

**Busca:**
```
max: 2025-10-13 18:17:02  ← Última fecha recibida
```

Si es reciente (< 5 min), los sensores están enviando ✅

---

### Paso 2: Verificar que la ingesta esté corriendo

**Síntomas de ingesta funcionando:**
```
[service] Partición 0 inicializada.
[service] Partición 1 inicializada.
[service] Último minuto: X mensajes persistidos  ← Debe aparecer cada 60s
```

**Si NO ves "mensajes persistidos":**
- Los sensores no están enviando en este momento
- O estás usando `--from latest` y solo lee mensajes nuevos

---

### Paso 3: Opciones de `--from`

#### A) `--from latest` (solo mensajes NUEVOS)
```bash
python manage.py ingest --cg service --from latest
```
- ✅ Útil para producción (no reprocesa históricos)
- ❌ Solo lee mensajes que lleguen DESPUÉS de conectarse
- ❌ Si los sensores no envían justo ahora, no verás nada

#### B) `--from earliest` (desde último checkpoint)
```bash
python manage.py ingest --cg service --from earliest
```
- ✅ Lee desde el último punto guardado en Azure
- ✅ Recupera mensajes perdidos
- ⚠️ Puede tomar tiempo si hay mucho backlog

#### C) `--from "FECHA"` (desde fecha específica)
```bash
python manage.py ingest --cg service --from "2025-10-13 18:00:00"
```
- ✅ Control preciso del punto de inicio
- ✅ Útil para recuperar datos de un rango específico

---

## 🔍 Diagnóstico Completo

### Terminal 1: Monitor de base de datos
```bash
.\.venv\Scripts\Activate.ps1
python monitor_ingesta.py
```

**Resultado esperado cada 10s:**
```
✅ [2025-10-13 18:25:00] +12 nuevos registros (1.2 msg/s)
   S4_PMTHVD: 2025-10-13 18:24:58
   S5_PMTHVD: 2025-10-13 18:24:59
   S6_PMTHVD: 2025-10-13 18:25:00
```

### Terminal 2: Ingesta
```bash
.\.venv\Scripts\Activate.ps1
python manage.py ingest --cg service --from earliest
```

**Logs esperados:**
```
[service] Último minuto: 15 mensajes persistidos  ← Cada 60s
```

### Terminal 3: Servidor web (si no está corriendo)
```bash
.\.venv\Scripts\Activate.ps1
python manage.py runserver --port 5000
```

---

## 🚨 Problemas Comunes

### 1. **"Partición inicializada" pero no llegan mensajes**

**Causa:** `--from latest` + sensores no enviando ahora

**Solución:**
```bash
# Ctrl+C para detener
python manage.py ingest --cg service --from earliest
```

### 2. **"No estoy seguro si los sensores están enviando"**

**Verificar en campo:**
- S4_PMTHVD (GRB_B. Rosario) → ¿LED parpadeando?
- S5_PMTHVD (GRB_PTAR) → ¿LED parpadeando?
- S6_PMTHVD (ICPET) → ¿WiFi conectado? (HUAWEI-141C)

**Verificar en Azure Portal:**
1. Ir a IoT Hub > Métricas
2. Ver "Telemetry messages sent" (últimos 30 min)
3. Debe mostrar actividad

### 3. **"Dashboard no se actualiza pero BD sí"**

**Causa:** El dashboard usa caché o no se refresca

**Solución:**
```bash
# Refrescar navegador (Ctrl+F5)
# O actualizar usando el botón "Actualizar ahora"
```

### 4. **"Error de conexión a Azure"**

**Logs típicos:**
```
ERROR: Connection error...
ERROR: Timeout...
```

**Verificar:**
```bash
# ¿El proxy está activo?
echo $env:HTTPS_PROXY

# Si devuelve algo, desactivar:
$env:FORCE_NO_PROXY = "1"
```

---

## ✅ Checklist de Verificación

- [ ] La ingesta muestra "Partición X inicializada"
- [ ] Cada 60s aparece "Último minuto: X mensajes"
- [ ] `python manage.py inspect` muestra datos recientes (< 5 min)
- [ ] El monitor muestra "+X nuevos registros"
- [ ] El servidor web está corriendo (puerto 5000)
- [ ] El navegador muestra datos en el dashboard

---

## 🎯 Solución Rápida (Si todo falla)

```bash
# Terminal 1: Detener todo (Ctrl+C en todas las ventanas)

# Terminal 2: Limpiar y reiniciar ingesta desde earliest
.\.venv\Scripts\Activate.ps1
python manage.py ingest --cg service --from earliest

# Terminal 3: Monitor (en otra ventana)
.\.venv\Scripts\Activate.ps1
python monitor_ingesta.py

# Terminal 4: Servidor web (si no está)
.\.venv\Scripts\Activate.ps1
python manage.py runserver --port 5000

# Navegador: http://127.0.0.1:5000/dash/
# Refrescar con Ctrl+F5
```

**Espera 2-3 minutos y verifica:**
1. Monitor muestra "+X nuevos registros" ✅
2. Ingesta muestra "mensajes persistidos" ✅
3. Dashboard se actualiza ✅

---

## 📞 Si aún no funciona

**Datos para compartir:**
1. Output de `python manage.py inspect`
2. Últimos 20 logs de la ingesta
3. Captura del monitor_ingesta.py
4. ¿Los sensores tienen LED encendido?

---

**Última actualización**: 13 de octubre de 2025
