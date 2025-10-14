# 📊 Guía de Reportes en Excel - Datos Minuto a Minuto

## ✨ ¿Qué ha Cambiado?

Los reportes ahora se generan en **formato Excel (.xlsx)** con **TODOS los datos minuto a minuto** del período seleccionado, no solo una muestra de 20 registros.

### 🎯 Características Principales

✅ **Todos los datos** - No hay límite de registros  
✅ **Minuto a minuto** - Agregación automática por minuto  
✅ **Múltiples hojas** - Información, Estadísticas, Datos Completos, Resumen  
✅ **Formato profesional** - Tablas con estilos, colores y bordes  
✅ **Auto-ajuste** - Columnas se ajustan automáticamente  
✅ **Filtros aplicados** - Los filtros del dashboard se aplican automáticamente

---

## 📥 Cómo Descargar Reportes

### Desde el Dashboard Web

1. **Accede a:** `http://localhost:5000/dash/`

2. **(Opcional) Aplica filtros:**
   - Selecciona dispositivos específicos
   - Elige el canal (Sensor 1, Sensor 2 o Ambos)

3. **Busca la sección:** "Descargar Reportes en Excel (Minuto a Minuto)"

4. **Haz clic en el botón deseado:**
   - 🕐 **Última Hora**
   - 📅 **Últimas 24 Horas**
   - 📆 **Últimos 7 Días**
   - 📊 **Mes Actual** *(NUEVO)*

5. **¡El archivo Excel se descarga automáticamente!**

---

## 📋 Contenido del Reporte Excel

Cada archivo Excel contiene **4 hojas**:

### 📄 Hoja 1: Información General
- Título del reporte
- Período analizado (fecha/hora inicio y fin)
- Fecha de generación
- Zona horaria (America/Bogota)
- Total de registros incluidos
- Dispositivos incluidos
- Canales seleccionados

### 📊 Hoja 2: Estadísticas
Tabla con estadísticas descriptivas por variable:
- **PM2.5**: Mínimo, Máximo, Promedio, Mediana, Desv. Estándar, Registros
- **PM10**: Mínimo, Máximo, Promedio, Mediana, Desv. Estándar, Registros
- **Temperatura**: Mínimo, Máximo, Promedio, Mediana, Desv. Estándar, Registros
- **Humedad**: Mínimo, Máximo, Promedio, Mediana, Desv. Estándar, Registros

### 📈 Hoja 3: Datos Completos (Minuto a Minuto)
Tabla con **TODOS los registros** agregados por minuto:
- Fecha/Hora (formato: YYYY-MM-DD HH:MM:00)
- Dispositivo (nombre amigable)
- Device_ID (identificador técnico)
- Canal (Um1 o Um2)
- PM2.5 (µg/m³)
- PM10 (µg/m³)
- Temperatura (°C)
- Humedad (%)

**Nota:** Los datos se promedian por minuto, dispositivo y canal.

### 🎯 Hoja 4: Resumen por Dispositivos
Tabla resumen con estadísticas por cada dispositivo:
- Dispositivo
- PM2.5: Promedio, Mínimo, Máximo
- PM10: Promedio, Mínimo, Máximo
- Temperatura: Promedio, Mínimo, Máximo
- Humedad: Promedio, Mínimo, Máximo
- Total de Registros

---

## 🔗 API REST - Endpoints

### Endpoint Principal
```
GET /api/reports/excel
```

### Parámetros

| Parámetro | Requerido | Valores | Descripción |
|-----------|-----------|---------|-------------|
| `period` | ✅ Sí | `hour`, `24hours`, `7days`, `month`, `year`, `custom` | Período del reporte |
| `device_id` | ⚪ No | CSV de IDs | Filtro por dispositivos específicos |
| `sensor_channel` | ⚪ No | `um1`, `um2`, `ambos` | Canal del sensor (default: ambos) |
| `start_date` | ⚪ Solo custom | `YYYY-MM-DD` | Fecha de inicio |
| `end_date` | ⚪ Solo custom | `YYYY-MM-DD` | Fecha de fin |
| `aggregate` | ⚪ No | `true`, `false` | Agregar por minuto (default: true) |

---

## 🚀 Ejemplos de Uso

### Ejemplo 1: Última Hora (Todos los dispositivos)
```
http://localhost:5000/api/reports/excel?period=hour
```

### Ejemplo 2: Últimas 24 Horas (Solo S4 y S5)
```
http://localhost:5000/api/reports/excel?period=24hours&device_id=S4_PMTHVD,S5_PMTHVD
```

### Ejemplo 3: Mes Actual (Solo Sensor 1)
```
http://localhost:5000/api/reports/excel?period=month&sensor_channel=um1
```

### Ejemplo 4: Últimos 7 Días (S4, S5, S6 - Canal 2)
```
http://localhost:5000/api/reports/excel?period=7days&device_id=S4_PMTHVD,S5_PMTHVD,S6_PMTHVD&sensor_channel=um2
```

### Ejemplo 5: Rango Personalizado
```
http://localhost:5000/api/reports/excel?period=custom&start_date=2025-10-01&end_date=2025-10-13
```

### Ejemplo 6: Datos Crudos (Sin agregar por minuto)
```
http://localhost:5000/api/reports/excel?period=hour&aggregate=false
```

---

## 💻 Uso Programático

### Python
```python
import requests
from datetime import datetime

# Descargar reporte Excel
response = requests.get(
    "http://localhost:5000/api/reports/excel",
    params={
        "period": "24hours",
        "device_id": "S4_PMTHVD,S5_PMTHVD",
        "sensor_channel": "ambos"
    }
)

# Guardar archivo
if response.status_code == 200:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_{timestamp}.xlsx"
    
    with open(filename, "wb") as f:
        f.write(response.content)
    
    print(f"Reporte descargado: {filename}")
else:
    print(f"Error: {response.status_code}")
```

### PowerShell
```powershell
# Descargar reporte de última hora
Invoke-WebRequest `
  -Uri "http://localhost:5000/api/reports/excel?period=hour" `
  -OutFile "reporte_hora.xlsx"

# Descargar reporte del mes con filtros
$params = @{
    period = "month"
    device_id = "S4_PMTHVD,S5_PMTHVD,S6_PMTHVD"
    sensor_channel = "ambos"
}
$url = "http://localhost:5000/api/reports/excel?" + ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
Invoke-WebRequest -Uri $url -OutFile "reporte_mes.xlsx"
```

### cURL
```bash
# Reporte de 24 horas
curl "http://localhost:5000/api/reports/excel?period=24hours" -o reporte.xlsx

# Reporte del mes con filtros
curl "http://localhost:5000/api/reports/excel?period=month&device_id=S4_PMTHVD,S5_PMTHVD" -o reporte_mes.xlsx"
```

---

## 🎨 Formato del Archivo Excel

### Estilos Aplicados
- ✅ **Encabezados azules** (#2C5AA0) con texto blanco
- ✅ **Bordes en todas las celdas** para mejor legibilidad
- ✅ **Alineación centrada** en todas las celdas
- ✅ **Anchos de columna auto-ajustados** según contenido
- ✅ **Números redondeados** a 2 decimales

### Nombre del Archivo
```
reporte_calidad_aire_{period}_{timestamp}.xlsx
```

Ejemplo:
```
reporte_calidad_aire_24hours_20251013_205600.xlsx
```

---

## ⚡ Diferencias entre Agregado y Crudo

### Agregado por Minuto (Default - `aggregate=true`)
- ✅ Promedia valores por minuto
- ✅ Reduce el tamaño del archivo
- ✅ Más fácil de analizar
- ✅ Recomendado para períodos largos

**Ejemplo:** Si hay 60 registros en un minuto, se promedia a 1 solo registro.

### Datos Crudos (`aggregate=false`)
- ✅ Incluye TODOS los registros sin promediar
- ✅ Útil para análisis detallado
- ⚠️ Archivos pueden ser muy grandes
- ⚠️ Puede ser lento para períodos largos

**Ejemplo:** Si hay 60 registros en un minuto, se incluyen los 60 registros.

---

## 📊 Comparación: PDF vs Excel

| Característica | PDF (Anterior) | Excel (Nuevo) |
|----------------|----------------|---------------|
| **Registros** | Solo 20 (muestra) | TODOS (minuto a minuto) |
| **Editable** | ❌ No | ✅ Sí |
| **Gráficos** | ❌ No | ✅ Fácil crear en Excel |
| **Análisis** | ❌ Limitado | ✅ Completo |
| **Hojas múltiples** | ❌ No | ✅ Sí (4 hojas) |
| **Filtros** | ❌ No | ✅ Sí (en Excel) |
| **Tamaño archivo** | Pequeño | Variable |
| **Formato** | Fijo | Flexible |

---

## 📈 Ejemplos de Cantidad de Datos

### Última Hora
- **Registros esperados:** ~180-360 registros
- **Tamaño archivo:** ~50-100 KB
- **Tiempo generación:** < 2 segundos

### Últimas 24 Horas
- **Registros esperados:** ~4,000-8,000 registros
- **Tamaño archivo:** ~500 KB - 1 MB
- **Tiempo generación:** 2-5 segundos

### Mes Actual (30 días)
- **Registros esperados:** ~120,000-240,000 registros
- **Tamaño archivo:** ~15-30 MB
- **Tiempo generación:** 10-30 segundos

---

## 🛠️ Solución de Problemas

### ❌ El archivo Excel no se abre
**Causa:** Puede estar corrupto o incompleto  
**Solución:** 
1. Verifica que la descarga se completó (tamaño > 0 KB)
2. Intenta descargar nuevamente
3. Revisa los logs en `logs/aireapp.log`

### ❌ El reporte está vacío
**Causa:** No hay datos para el período seleccionado  
**Solución:**
1. Verifica que la ingesta de datos esté activa
2. Selecciona un período diferente
3. Revisa qué dispositivos tienen datos

### ❌ Error "aggregate debe ser true o false"
**Causa:** Valor incorrecto en el parámetro  
**Solución:** Usa `aggregate=true` o `aggregate=false`

### ❌ El archivo es muy grande
**Causa:** Período muy largo con aggregate=false  
**Solución:**
1. Usa `aggregate=true` para promediar por minuto
2. Reduce el período (ej: 7 días en lugar de mes)
3. Filtra por dispositivos específicos

---

## 🔧 Personalización Avanzada

### Cambiar Agregación a 5 Minutos
Edita `reports_excel.py` línea ~75:
```python
# En lugar de:
df['minuto'] = df['timestamp'].dt.floor('min')

# Usa:
df['minuto'] = df['timestamp'].dt.floor('5min')
```

### Agregar Más Variables
Edita `reports_excel.py` línea ~55:
```python
data.append({
    # ... campos existentes ...
    'Presión (hPa)': m.presion,  # Agregar nueva variable
})
```

---

## ✅ Checklist de Verificación

Antes de usar los reportes, verifica:

- [✅] Servidor Flask corriendo (`python app.py`)
- [✅] Ingesta de datos activa
- [✅] Dependencias instaladas (`openpyxl`, `xlsxwriter`, `pandas`)
- [✅] Dashboard accesible en `http://localhost:5000/dash/`
- [✅] Base de datos con registros recientes

---

## 📚 Archivos Relacionados

- **Backend:**
  - `reports_excel.py` - Generación de reportes Excel
  - `app.py` - Endpoint `/api/reports/excel`
  
- **Frontend:**
  - `dashboards/layout.py` - Botones de descarga
  - `dashboards/callbacks.py` - URLs dinámicas

- **Configuración:**
  - `requirements.txt` - Dependencias (openpyxl, xlsxwriter)

---

## 🎉 ¡Listo para Usar!

Los reportes Excel están completamente implementados y operativos. Puedes:

1. ✅ Descargar desde el dashboard con un clic
2. ✅ Usar la API REST para automatizar
3. ✅ Obtener TODOS los datos minuto a minuto
4. ✅ Analizar en Excel con tablas dinámicas
5. ✅ Crear gráficos personalizados
6. ✅ Exportar a otros formatos

**¡Disfruta de tus reportes detallados!** 📊
