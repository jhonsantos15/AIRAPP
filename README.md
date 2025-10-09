##===================================================================
# INICIALIZAR TERMINAL UNO (SERVIDOR)
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1 
python manage.py runserver --port 5000
##===================================================================
##===================================================================
# INICIALIZAR TERMINAL DOS (INGESTA)
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1 
python manage.py ingest --cg asa-s6 --from latest
##===================================================================


# En ESTA terminal si la ingesta falla (solo sesión actual)

Remove-Item Env:\HTTPS_PROXY -ErrorAction SilentlyContinue
Remove-Item Env:\HTTP_PROXY  -ErrorAction SilentlyContinue
$env:NO_PROXY = "127.0.0.1,localhost"

$env:HTTPS_PROXY = "http://USUARIO:CLAVE@proxy.real.miempresa.com:80"
$env:HTTP_PROXY  = $env:HTTPS_PROXY
$env:NO_PROXY    = "127.0.0.1,localhost"

python manage.py ingest --cg asa-s6 --from latest













# AireApp – Sensores de Bajo Costo (IoT Hub / Event Hub)

Aplicación web en *Python + Flask* con *Dash* para adquirir, almacenar y visualizar *datos crudos* de sensores (S1_PMTHVD … S6_PMTHVD) conectados a *Azure IoT Hub* (compatible con *Event Hub*).  
Zona horaria fija: *America/Bogota (UTC-5)*.

> *Disclaimer:* Datos indicativos sin corrección; no equivalen a estaciones de referencia (IDEAM Res. 2254 de 2017, guías OMS).

## 1) Requisitos
- Python *3.11+*
- (Windows) PowerShell / (Linux) bash
- Acceso a Azure IoT Hub compatible con Event Hub

## 2) Instalación rápida

bash
git clone <este_repo> aireapp
cd aireapp
##============================================================================================================
#Para inicializar el proyecto se debe:
# 1. En una terminal correr el siguiente codigo para poder instalar dependencias en entorno virtual de python:

python -m venv .venv
. .venv/Scripts/activate        
pip install -r requirements.txt

# 2. Para levantar el servidor ejecutar:

python manage.py runserver --port 5000

# 3. Para consultar la data en tiempo real se requiere realizar la Ingesta (en otra terminal):
python -m venv .venv
. .venv/Scripts/activate  
python manage.py ingest --cg asa-s6 --from latest
#==============================================================================================================
# AireApp — Monitoreo de Calidad del Aire (Flask + Dash + Azure IoT Hub/Event Hubs)

Aplicación web en **Python (Flask + Dash)** para adquirir y visualizar datos de sensores de bajo costo
conectados a **Azure IoT Hub** (vía punto **Compatible con Event Hubs**). La zona horaria se fija en
**America/Bogota (UTC−05:00)** para toda la aplicación.

> **Aviso técnico**: Los datos son **indicativos**. No sustituyen estaciones de referencia ni redes oficiales.
> Para comparabilidad normativa considerar la **Resolución IDEAM 2254 de 2017** y guías OMS vigentes.

---

## 1) Arquitectura (resumen)
- **Sensores (S1…S6)** → **Azure IoT Hub** → **Event Hubs compatible**.
- **Servicio de Ingesta** (`ingest.py`, comando `manage.py ingest`) consume eventos y persiste en la **BD**.
- **BD** (por defecto **SQLite**; reemplazable por **PostgreSQL** u otro motor).
- **API REST** (endpoints en Flask, p. ej. `/api/series`) expone series de tiempo.
- **UI** con **Dash/Plotly**: gráficos de PM2.5, PM10, temperatura, humedad, etc.

text
Dispositivos → IoT Hub → Event Hub → Ingesta → Base de Datos → API → Dash