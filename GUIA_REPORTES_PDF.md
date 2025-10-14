# Guía de Reportes en PDF

## Descripción General

El sistema ahora permite generar y descargar reportes en formato PDF con los datos de calidad del aire almacenados en la base de datos. Los reportes incluyen estadísticas, gráficos de tendencias y muestras de datos.

## Tipos de Reportes Disponibles

### 1. **Reporte de Última Hora**
- **Período**: Últimos 60 minutos
- **Uso**: Para revisiones inmediatas y monitoreo en tiempo real
- **Endpoint**: `/api/reports/pdf?period=hour`

### 2. **Reporte de Últimas 24 Horas**
- **Período**: Último día completo (24 horas)
- **Uso**: Análisis diario de la calidad del aire
- **Endpoint**: `/api/reports/pdf?period=24hours`

### 3. **Reporte de Últimos 7 Días**
- **Período**: Última semana (7 días)
- **Uso**: Análisis semanal y tendencias de corto plazo
- **Endpoint**: `/api/reports/pdf?period=7days`

### 4. **Reporte Anual**
- **Período**: Año actual (desde 1 de enero hasta hoy)
- **Uso**: Análisis de largo plazo y tendencias anuales
- **Endpoint**: `/api/reports/pdf?period=year`

### 5. **Reporte Personalizado**
- **Período**: Rango de fechas específico
- **Uso**: Análisis de períodos específicos
- **Endpoint**: `/api/reports/pdf?period=custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

## Contenido de los Reportes

Cada reporte PDF incluye:

1. **Información del Período**
   - Rango de fechas y horas
   - Total de registros analizados
   - Dispositivos incluidos

2. **Estadísticas Generales**
   - **PM2.5**: Valores mínimo, máximo y promedio (µg/m³)
   - **PM10**: Valores mínimo, máximo y promedio (µg/m³)
   - **Temperatura**: Valores mínimo, máximo y promedio (°C)
   - **Humedad Relativa**: Valores mínimo, máximo y promedio (%)

3. **Distribución por Dispositivos**
   - Número de registros por cada sensor
   - Identificación de equipos con más actividad

4. **Muestra de Datos Recientes**
   - Tabla con los últimos 20 registros
   - Incluye fecha/hora, dispositivo, canal y todas las variables

5. **Información Adicional**
   - Nota sobre la naturaleza indicativa de los datos
   - Información del sistema de vigilancia

## Uso desde el Dashboard

### Paso 1: Acceder al Dashboard
Navega a: `http://localhost:5000/dash/`

### Paso 2: Aplicar Filtros (Opcional)
En la sección de controles, puedes:
- **Seleccionar Equipos**: Elige uno o varios sensores específicos
- **Seleccionar Canal**: Sensor 1, Sensor 2 o Ambos
- Los filtros se aplicarán automáticamente a los reportes

### Paso 3: Descargar Reporte
En la sección **"Descargar Reportes en PDF"**, encontrarás 4 botones:
- **Última Hora**: Descarga reporte de la última hora
- **Últimas 24 Horas**: Descarga reporte del último día
- **Últimos 7 Días**: Descarga reporte de la última semana
- **Año Actual**: Descarga reporte del año completo

Haz clic en el botón deseado y el reporte se descargará automáticamente.

## Uso desde la API REST

### Endpoint Principal
```
GET /api/reports/pdf
```

### Parámetros de Query

#### Obligatorios
- **period**: Tipo de período del reporte
  - `hour` - Última hora
  - `24hours` - Últimas 24 horas
  - `7days` - Últimos 7 días
  - `year` - Año actual
  - `custom` - Período personalizado

#### Opcionales
- **device_id**: Lista de dispositivos separados por coma
  - Ejemplo: `S1_PMTHVD,S2_PMTHVD,S3_PMTHVD`
  - Si se omite: incluye todos los dispositivos

- **sensor_channel**: Canal del sensor
  - `um1` - Solo Sensor 1
  - `um2` - Solo Sensor 2
  - `ambos` - Ambos sensores (default)

- **start_date**: Fecha de inicio (solo para period=custom)
  - Formato: `YYYY-MM-DD`
  - Ejemplo: `2025-10-01`

- **end_date**: Fecha de fin (solo para period=custom)
  - Formato: `YYYY-MM-DD`
  - Ejemplo: `2025-10-13`

### Ejemplos de URLs

#### Reporte de última hora (todos los dispositivos)
```
http://localhost:5000/api/reports/pdf?period=hour
```

#### Reporte de 24 horas (solo sensores S1 y S2)
```
http://localhost:5000/api/reports/pdf?period=24hours&device_id=S1_PMTHVD,S2_PMTHVD
```

#### Reporte de 7 días (solo Sensor 1)
```
http://localhost:5000/api/reports/pdf?period=7days&sensor_channel=um1
```

#### Reporte personalizado (rango específico)
```
http://localhost:5000/api/reports/pdf?period=custom&start_date=2025-10-01&end_date=2025-10-07&device_id=S1_PMTHVD
```

#### Reporte anual (todos los parámetros)
```
http://localhost:5000/api/reports/pdf?period=year&device_id=S1_PMTHVD,S2_PMTHVD&sensor_channel=ambos
```

## Formato del Archivo

- **Tipo de archivo**: PDF
- **Nombre del archivo**: `reporte_calidad_aire_{period}_{timestamp}.pdf`
  - Ejemplo: `reporte_calidad_aire_24hours_20251013_204530.pdf`
- **Tamaño de página**: Letter (8.5" x 11")
- **Fuentes**: Helvetica (incluida en PDF estándar)

## Consideraciones Técnicas

### Rendimiento
- Los reportes se generan en tiempo real
- Períodos más largos (año completo) pueden tardar más en generarse
- Se recomienda usar filtros de dispositivos para reportes grandes

### Límites
- Los reportes incluyen hasta 20 registros en la muestra de datos
- Para análisis detallados de grandes volúmenes, considere usar la API JSON

### Zona Horaria
- Todos los reportes usan la zona horaria `America/Bogota`
- Las fechas y horas se muestran en hora local

### Manejo de Errores
- Si no hay datos para el período seleccionado, el reporte lo indicará
- Valores `N/A` aparecen cuando no hay datos disponibles para una variable

## Integración con Otros Sistemas

### Descarga Programática (Python)
```python
import requests

url = "http://localhost:5000/api/reports/pdf"
params = {
    "period": "24hours",
    "device_id": "S1_PMTHVD,S2_PMTHVD",
    "sensor_channel": "ambos"
}

response = requests.get(url, params=params)

if response.status_code == 200:
    with open("reporte.pdf", "wb") as f:
        f.write(response.content)
    print("Reporte descargado exitosamente")
else:
    print(f"Error: {response.status_code}")
```

### Descarga Programática (cURL)
```bash
curl "http://localhost:5000/api/reports/pdf?period=hour" \
  --output reporte.pdf
```

### Descarga Programática (PowerShell)
```powershell
Invoke-WebRequest `
  -Uri "http://localhost:5000/api/reports/pdf?period=hour" `
  -OutFile "reporte.pdf"
```

## Solución de Problemas

### El reporte se descarga vacío
- Verifique que existan datos para el período seleccionado
- Revise los filtros de dispositivos y canales

### Error 400 (Bad Request)
- Verifique el formato de las fechas (YYYY-MM-DD)
- Para period=custom, asegúrese de incluir start_date y end_date

### Error 500 (Internal Server Error)
- Revise los logs del servidor en `logs/aireapp.log`
- Verifique que las dependencias estén instaladas correctamente

### El botón no responde
- Asegúrese de que el servidor Flask esté corriendo
- Verifique la consola del navegador para errores JavaScript

## Dependencias Requeridas

Las siguientes librerías Python son necesarias:
- `reportlab==4.2.0` - Generación de PDFs
- `matplotlib==3.9.0` - Procesamiento de gráficos (opcional)

Instalación:
```bash
pip install reportlab==4.2.0 matplotlib==3.9.0
```

## Archivos Relacionados

- **Backend**: 
  - `reports.py` - Lógica de generación de reportes
  - `app.py` - Endpoint API de reportes
  
- **Frontend**:
  - `dashboards/layout.py` - Botones de reportes en UI
  - `dashboards/callbacks.py` - Actualización dinámica de URLs
  
- **Estilos**:
  - `static/styles.css` - Estilos de botones de reportes

## Mejoras Futuras

Posibles extensiones de la funcionalidad:
- Gráficos integrados en el PDF
- Reportes comparativos entre dispositivos
- Exportación en otros formatos (Excel, CSV)
- Envío automático por correo electrónico
- Reportes programados (diarios, semanales)
- Análisis de calidad del aire vs. normas ambientales
