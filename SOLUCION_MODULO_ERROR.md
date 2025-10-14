# 🔧 Solución: Error de ModuleNotFoundError en Entorno Virtual

## Problema
```
ModuleNotFoundError: No module named 'reportlab'
```

Esto ocurre porque el entorno virtual `.venv` no tiene instaladas las dependencias necesarias.

## Solución Rápida

### Opción 1: Instalar dependencias en el entorno virtual (RECOMENDADO)

```powershell
# 1. Asegúrate de estar en la carpeta del proyecto
cd C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp

# 2. Activa el entorno virtual (si no está activado)
.\.venv\Scripts\Activate.ps1

# 3. Instala todas las dependencias
pip install -r requirements.txt

# 4. Verifica que se instalaron correctamente
pip list | Select-String "reportlab|openpyxl|xlsxwriter"

# 5. Ahora puedes ejecutar la ingesta
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

### Opción 2: Instalar solo las dependencias faltantes

```powershell
# Con el entorno virtual activado:
pip install reportlab==4.2.0 openpyxl==3.1.5 xlsxwriter==3.2.9 matplotlib==3.9.0
```

## Verificación

### Verifica que el entorno virtual esté activado
Tu prompt debe mostrar `(.venv)` al inicio:
```powershell
(.venv) PS C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp>
```

### Si no está activado:
```powershell
.\.venv\Scripts\Activate.ps1
```

### Si hay problemas de permisos:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1
```

## Comandos Completos para Ejecutar

```powershell
# Terminal 1: Servidor Flask
cd C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py

# Terminal 2: Ingesta de datos (en otra ventana)
cd C:\Users\Usuario\OneDrive - TIP Colombia\Escritorio\aireapp
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

## ¿Por qué ocurre esto?

El entorno virtual `.venv` es un ambiente Python aislado. Cuando instalas paquetes con `pip install` fuera del entorno virtual, se instalan en el Python global del sistema, pero NO en el entorno virtual.

Para que funcione todo correctamente, DEBES:
1. ✅ Activar el entorno virtual
2. ✅ Instalar las dependencias DENTRO del entorno virtual
3. ✅ Ejecutar los comandos con el entorno virtual activado

## Dependencias Necesarias

Desde `requirements.txt`:
```txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
python-dotenv==1.0.1
SQLAlchemy==2.0.35
pandas==2.2.2
plotly==5.24.1
dash==2.18.2
azure-eventhub==5.12.2
click==8.1.7
pytest==8.3.2
reportlab==4.2.0        ← Necesaria para reportes PDF
matplotlib==3.9.0       ← Necesaria para gráficos
openpyxl==3.1.2         ← Necesaria para reportes Excel
xlsxwriter==3.2.0       ← Necesaria para reportes Excel
```

## Después de Instalar

Una vez instaladas las dependencias, deberías poder ejecutar sin errores:

```powershell
(.venv) PS> python manage.py ingest --cg asa-s1,asa-s2,asa-s3,asa-s4,asa-s5,asa-s6 --from latest
```

## Resumen

**El problema:** Entorno virtual sin dependencias instaladas  
**La solución:** Activar `.venv` e instalar con `pip install -r requirements.txt`  
**El resultado:** Ingesta y servidor funcionando correctamente
