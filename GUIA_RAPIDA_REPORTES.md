# 📊 Guía Rápida: Reportes PDF

## ✨ Inicio Rápido

### Desde el Dashboard Web

1. **Abrir el dashboard:**
   ```
   http://localhost:5000/dash/
   ```

2. **(Opcional) Aplicar filtros:**
   - Selecciona dispositivos específicos
   - Elige el canal del sensor (Sensor 1, Sensor 2 o Ambos)

3. **Descargar reporte:**
   - Busca la sección "Descargar Reportes en PDF"
   - Haz clic en el botón del período deseado:
     - **Última Hora** 🕐
     - **Últimas 24 Horas** 📅
     - **Últimos 7 Días** 📆
     - **Año Actual** 🗓️

4. **¡Listo!** El PDF se descargará automáticamente

---

## 🔗 URLs Directas (API)

### Reporte de Última Hora
```
http://localhost:5000/api/reports/pdf?period=hour
```

### Reporte de 24 Horas
```
http://localhost:5000/api/reports/pdf?period=24hours
```

### Reporte de 7 Días
```
http://localhost:5000/api/reports/pdf?period=7days
```

### Reporte Año Actual
```
http://localhost:5000/api/reports/pdf?period=year
```

---

## 🎯 Ejemplos con Filtros

### Solo Sensor S1
```
http://localhost:5000/api/reports/pdf?period=24hours&device_id=S1_PMTHVD
```

### Sensores S1 y S2, últimos 7 días
```
http://localhost:5000/api/reports/pdf?period=7days&device_id=S1_PMTHVD,S2_PMTHVD
```

### Solo Canal 1 (Um1), última hora
```
http://localhost:5000/api/reports/pdf?period=hour&sensor_channel=um1
```

### Reporte Personalizado (rango específico)
```
http://localhost:5000/api/reports/pdf?period=custom&start_date=2025-10-01&end_date=2025-10-10
```

---

## 📦 Contenido del Reporte

Cada PDF incluye:

✅ **Período analizado** con fechas y horas  
✅ **Total de registros** procesados  
✅ **Estadísticas por variable:**
   - PM2.5 (µg/m³): Min, Max, Promedio
   - PM10 (µg/m³): Min, Max, Promedio  
   - Temperatura (°C): Min, Max, Promedio
   - Humedad (%): Min, Max, Promedio

✅ **Distribución por dispositivos** (cantidad de registros)  
✅ **Muestra de datos** (últimos 20 registros)  
✅ **Información del sistema** y disclaimer

---

## 💻 Uso Programático

### Python
```python
import requests

# Descargar reporte
response = requests.get(
    "http://localhost:5000/api/reports/pdf",
    params={"period": "24hours"}
)

# Guardar archivo
with open("reporte.pdf", "wb") as f:
    f.write(response.content)
```

### PowerShell
```powershell
Invoke-WebRequest `
  -Uri "http://localhost:5000/api/reports/pdf?period=hour" `
  -OutFile "reporte.pdf"
```

### cURL
```bash
curl "http://localhost:5000/api/reports/pdf?period=hour" -o reporte.pdf
```

---

## 🛠️ Solución Rápida de Problemas

### ❌ El reporte está vacío
**Solución:** Verifica que haya datos para el período seleccionado
```bash
# Verificar datos en la base de datos
python manage.py check_db
```

### ❌ Error 400 (Bad Request)
**Solución:** Revisa el formato de los parámetros
- Fechas deben ser: `YYYY-MM-DD`
- period debe ser: `hour`, `24hours`, `7days`, `year`, o `custom`

### ❌ El botón no descarga
**Solución:** Verifica que el servidor esté corriendo
```bash
# Iniciar servidor
python app.py
```

---

## 📝 Parámetros Disponibles

| Parámetro | Requerido | Valores | Ejemplo |
|-----------|-----------|---------|---------|
| `period` | ✅ Sí | `hour`, `24hours`, `7days`, `year`, `custom` | `period=hour` |
| `device_id` | ⚪ No | CSV de IDs | `device_id=S1_PMTHVD,S2_PMTHVD` |
| `sensor_channel` | ⚪ No | `um1`, `um2`, `ambos` | `sensor_channel=um1` |
| `start_date` | ⚪ Solo con custom | `YYYY-MM-DD` | `start_date=2025-10-01` |
| `end_date` | ⚪ Solo con custom | `YYYY-MM-DD` | `end_date=2025-10-13` |

---

## 🎨 Personalización

Para personalizar la apariencia de los reportes, edita el archivo:
```
reports_config.py
```

Puedes modificar:
- 🎨 Colores (primary, secondary, tablas)
- 📝 Textos (títulos, etiquetas)
- 📄 Formato de página (márgenes, tamaño)
- 📊 Variables a incluir
- 🖼️ Logo institucional (opcional)

---

## 📚 Documentación Completa

Para más detalles, consulta:
- `GUIA_REPORTES_PDF.md` - Guía completa
- `RESUMEN_IMPLEMENTACION_PDF.md` - Detalles técnicos
- `reports.py` - Código fuente con comentarios

---

## 🚀 Tips de Uso

1. **Filtros aplicados**: Los botones del dashboard aplican automáticamente los filtros seleccionados

2. **Nombre del archivo**: Los PDFs incluyen timestamp para evitar sobrescritura
   ```
   reporte_calidad_aire_24hours_20251013_204530.pdf
   ```

3. **Zona horaria**: Todos los reportes usan hora de Bogotá (UTC-5)

4. **Rendimiento**: Para períodos largos (año completo), el reporte puede tardar unos segundos

5. **Datos históricos**: Los reportes solo incluyen datos que están en la base de datos

---

## ✅ Verificación Rápida

Prueba que todo funcione correctamente:

```bash
# Ejecutar script de pruebas
python test_reports.py
```

Este script generará automáticamente todos los tipos de reportes y mostrará un resumen de resultados.

---

**¿Necesitas ayuda?** Consulta `TROUBLESHOOTING.md` o revisa los logs en `logs/aireapp.log`
