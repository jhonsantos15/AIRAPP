# 🔄 Actualización: Reportes en Excel con Datos Minuto a Minuto

## ✅ Cambios Implementados

### 🎯 Objetivo Principal
Convertir los reportes de PDF a Excel con **TODOS los datos minuto a minuto** en lugar de solo una muestra de 20 registros.

---

## 📋 Resumen de Cambios

### 1. **Nuevo Formato: Excel (.xlsx)**
- ❌ **Anterior:** Reportes en PDF con solo 20 registros (muestra)
- ✅ **Ahora:** Reportes en Excel con TODOS los registros minuto a minuto

### 2. **Nuevo Módulo:** `reports_excel.py`
Módulo completo para generación de reportes Excel con:
- Agregación por minuto automática
- Estadísticas descriptivas completas
- Múltiples hojas (4 hojas por archivo)
- Formato profesional con estilos
- Manejo de celdas fusionadas corregido

### 3. **Nuevo Endpoint API:** `/api/reports/excel`
```
GET /api/reports/excel
```

#### Parámetros:
- `period`: `hour`, `24hours`, `7days`, `month`, `year`, `custom`
- `device_id`: CSV de IDs (opcional)
- `sensor_channel`: `um1`, `um2`, `ambos` (opcional)
- `start_date`: YYYY-MM-DD (requerido para custom)
- `end_date`: YYYY-MM-DD (requerido para custom)
- `aggregate`: `true`, `false` (default: true)

### 4. **Interfaz Actualizada**
Dashboard ahora muestra:
```
📊 Descargar Reportes en Excel (Minuto a Minuto)
[Última Hora] [Últimas 24 Horas] [Últimos 7 Días] [Mes Actual]
```

---

## 📊 Estructura del Archivo Excel

Cada reporte Excel contiene **4 hojas**:

### 📄 Hoja 1: Información General
- Título del reporte
- Período (fecha/hora inicio - fin)
- Fecha de generación
- Zona horaria
- Total de registros
- Dispositivos incluidos
- Canales seleccionados

### 📈 Hoja 2: Estadísticas
Tabla con estadísticas por variable:
| Variable | Mínimo | Máximo | Promedio | Mediana | Desv. Estándar | Registros |
|----------|--------|--------|----------|---------|----------------|-----------|
| PM2.5    | ...    | ...    | ...      | ...     | ...            | ...       |
| PM10     | ...    | ...    | ...      | ...     | ...            | ...       |
| Temperatura | ... | ...    | ...      | ...     | ...            | ...       |
| Humedad  | ...    | ...    | ...      | ...     | ...            | ...       |

### 📋 Hoja 3: Datos Completos
Tabla con TODOS los registros minuto a minuto:
| Fecha/Hora | Dispositivo | Device_ID | Canal | PM2.5 | PM10 | Temp | HR |
|------------|-------------|-----------|-------|-------|------|------|----|
| ...        | ...         | ...       | ...   | ...   | ...  | ...  | ...|

**Agregación:** Los valores se promedian por minuto para cada combinación de dispositivo y canal.

### 🎯 Hoja 4: Resumen por Dispositivos
Tabla resumen por dispositivo:
| Dispositivo | PM2.5 Prom | PM2.5 Min | PM2.5 Max | ... | Total Registros |
|-------------|------------|-----------|-----------|-----|-----------------|
| ...         | ...        | ...       | ...       | ... | ...             |

---

## 🎨 Estilos Aplicados

### Formato Profesional
- ✅ Encabezados con fondo azul (#2C5AA0) y texto blanco
- ✅ Títulos en azul oscuro (#1F4788) y negrita
- ✅ Bordes finos en todas las celdas
- ✅ Alineación centrada
- ✅ Anchos de columna auto-ajustados
- ✅ Números redondeados a 2 decimales

### Manejo Correcto de Celdas
- ✅ Detección y omisión de celdas fusionadas
- ✅ No se aplican estilos a `MergedCell`
- ✅ Uso de `hasattr()` para validar atributos
- ✅ Manejo robusto de excepciones

---

## 🔧 Correcciones Técnicas

### Problema Original
```python
AttributeError: 'MergedCell' object has no attribute 'column_letter'
```

### Causa
Al iterar sobre columnas con `ws.columns`, las celdas fusionadas no tienen el atributo `column_letter`.

### Solución Implementada
```python
# Antes (error):
for column in ws.columns:
    column_letter = column[0].column_letter  # ❌ Falla con MergedCell

# Ahora (correcto):
for col_idx in range(1, ws.max_column + 1):
    column_letter = get_column_letter(col_idx)  # ✅ Funciona siempre
    for row_idx in range(1, ws.max_row + 1):
        cell = ws.cell(row_idx, col_idx)
        if hasattr(cell, 'value') and cell.value:  # ✅ Valida antes de usar
            ...
```

### Mejoras Adicionales
1. Validación con `hasattr()` antes de acceder a atributos
2. Bloques `try-except` para manejo robusto
3. Uso de `get_column_letter()` de `openpyxl.utils`
4. Iteración por índices en lugar de objetos

---

## 📦 Dependencias Agregadas

### Nuevas Librerías
```txt
openpyxl==3.1.5      # Lectura/escritura de archivos Excel
xlsxwriter==3.2.9    # Generación optimizada de Excel
et-xmlfile==2.0.0    # Dependencia de openpyxl
```

### Instalación
```bash
pip install openpyxl xlsxwriter
```

---

## 🚀 Ejemplos de Uso

### Desde el Dashboard
1. Ve a `http://localhost:5000/dash/`
2. (Opcional) Selecciona dispositivos y canales
3. Click en "Última Hora", "Últimas 24 Horas", "Últimos 7 Días", o "Mes Actual"
4. El archivo Excel se descarga automáticamente

### Desde la API (Python)
```python
import requests

# Reporte de última hora
response = requests.get(
    "http://localhost:5000/api/reports/excel",
    params={"period": "hour"}
)

with open("reporte_hora.xlsx", "wb") as f:
    f.write(response.content)
```

### Desde PowerShell
```powershell
Invoke-WebRequest `
  -Uri "http://localhost:5000/api/reports/excel?period=24hours" `
  -OutFile "reporte_24h.xlsx"
```

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | PDF (Anterior) | Excel (Ahora) |
|---------|----------------|---------------|
| **Formato** | PDF | XLSX |
| **Registros** | 20 (muestra) | TODOS (miles) |
| **Minuto a minuto** | ❌ No | ✅ Sí |
| **Editable** | ❌ No | ✅ Sí |
| **Múltiples hojas** | ❌ No | ✅ Sí (4 hojas) |
| **Estadísticas** | Básicas | Completas |
| **Resumen por dispositivo** | ❌ No | ✅ Sí |
| **Gráficos** | ❌ No | ✅ Fácil crear |
| **Filtros** | ❌ No | ✅ En Excel |
| **Análisis** | Limitado | Completo |

---

## 📈 Rendimiento

### Cantidad de Datos Esperada

| Período | Registros Aprox. | Tamaño Archivo | Tiempo Generación |
|---------|------------------|----------------|-------------------|
| Última Hora | 180-360 | 50-100 KB | < 2 seg |
| 24 Horas | 4,000-8,000 | 500 KB - 1 MB | 2-5 seg |
| 7 Días | 28,000-56,000 | 3-7 MB | 5-15 seg |
| Mes Actual | 120,000-240,000 | 15-30 MB | 10-30 seg |

**Nota:** Con `aggregate=false`, los tamaños pueden ser 10-20x mayores.

---

## ✅ Archivos Modificados

### Nuevos Archivos
- ✅ `reports_excel.py` (398 líneas)
- ✅ `GUIA_REPORTES_EXCEL.md` (documentación completa)
- ✅ `ACTUALIZACION_REPORTES_EXCEL.md` (este archivo)

### Archivos Modificados
- ✅ `app.py` (+ endpoint `/api/reports/excel`)
- ✅ `dashboards/layout.py` (botones actualizados a Excel)
- ✅ `dashboards/callbacks.py` (URLs a `/api/reports/excel`)
- ✅ `requirements.txt` (+ openpyxl, xlsxwriter)

### Archivos Mantenidos (PDF)
- ℹ️ `reports.py` (aún disponible para PDF)
- ℹ️ Endpoint `/api/reports/pdf` (aún funcional)

---

## 🔮 Próximas Mejoras Sugeridas

1. **Gráficos en Excel**
   - Integrar gráficos de tendencias usando `openpyxl.chart`
   - Gráficos de líneas para PM2.5 y PM10
   - Gráficos de barras para comparación entre dispositivos

2. **Formato Condicional**
   - Colores según nivel de calidad del aire
   - Alertas visuales para valores fuera de rango

3. **Tablas Dinámicas**
   - Pre-configurar tablas dinámicas
   - Facilitar análisis interactivo

4. **Compresión**
   - Usar formato comprimido para archivos grandes
   - Opción de ZIP para múltiples reportes

5. **Envío Automático**
   - Programar generación y envío por email
   - Reportes diarios/semanales automáticos

---

## 🐛 Solución de Problemas

### Error: "MergedCell object has no attribute..."
**Estado:** ✅ CORREGIDO en versión actual  
**Solución:** Reiniciar servidor para cargar código actualizado

### El archivo no se descarga
**Verificar:**
1. ✅ Servidor Flask corriendo
2. ✅ Dependencias instaladas (`openpyxl`, `xlsxwriter`)
3. ✅ Hay datos en el período seleccionado

### El archivo es muy grande
**Solución:**
- Usar `aggregate=true` (por defecto)
- Filtrar por dispositivos específicos
- Reducir el período

### No hay datos en el reporte
**Causas posibles:**
- Ingesta de datos no está activa
- No hay datos para el período/dispositivos seleccionados
- Filtros muy restrictivos

---

## ✅ Estado: OPERATIVO

Los reportes Excel están completamente implementados y funcionando correctamente.

### Verificación Final
- [✅] Servidor Flask corriendo
- [✅] Dependencias instaladas
- [✅] Error de MergedCell corregido
- [✅] Dashboard actualizado con botones Excel
- [✅] API `/api/reports/excel` funcional
- [✅] Documentación completa

---

**Fecha de Actualización:** 13 de octubre de 2025  
**Versión:** 2.0.0  
**Estado:** Producción  
**Cambio Principal:** PDF → Excel con datos completos minuto a minuto
