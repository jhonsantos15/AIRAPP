# 🌬️ AireApp - Sistema de Monitoreo de Calidad del Aire

Sistema de monitoreo en tiempo real de calidad del aire con ingesta IoT, API REST y dashboard interactivo.

## 🚀 Inicio Rápido

### Prerequisitos

- Python 3.11+
- Azure IoT Hub (credenciales en `.env`)

### Instalación

```powershell
# Clonar repositorio
git clone https://github.com/jhonsantos15/AIRAPP.git
cd aireapp

# Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Azure IoT Hub
```

### Ejecución

El sistema requiere **3 procesos** corriendo simultáneamente:

#### Terminal 1: Consumidor IoT (Ingesta de datos)
```powershell
python scripts/start_iot_consumer.py --from latest
```
Consume eventos desde Azure IoT Hub y los almacena en la base de datos.

#### Terminal 2: Dashboard (Visualización)
```powershell
python scripts/start_dashboard.py --debug
```
Dashboard interactivo en: http://localhost:8050

#### Terminal 3: API REST (Opcional)
```powershell
python scripts/start_api.py
```
API REST en: http://localhost:8000/docs

## 📁 Arquitectura

```
Frontend (Dash)  ←→  Backend (FastAPI)  ←→  Database (SQLite)
                          ↓
                   IoT Hub Service
                          ↓
              Azure Event Hub (IoT Hub)
```

### Estructura del Proyecto

```
aireapp/
├── src/
│   ├── api/          # API REST con FastAPI
│   ├── dashboard/    # Dashboard con Dash/Plotly
│   ├── iot/          # Consumidor de Azure IoT Hub
│   ├── services/     # Lógica de negocio
│   ├── core/         # Configuración, DB, Modelos
│   ├── schemas/      # Schemas Pydantic
│   └── utils/        # Utilidades y constantes
├── scripts/          # Scripts de inicio
├── migrations/       # Migraciones Alembic
├── tests/            # Tests unitarios
└── requirements.txt
```

## 🔑 Características Principales

- **Ingesta en Tiempo Real**: Consumo de eventos desde Azure IoT Hub con múltiples consumer groups
- **Dashboard Interactivo**: Visualización de PM2.5, PM10, temperatura y humedad con actualización automática cada 60 segundos
- **API REST**: Endpoints para consultar dispositivos, mediciones y generar reportes
- **Filtros Avanzados**: Selección por dispositivos, sensores, fechas y tipo de material particulado
- **Resample Inteligente**: Resolución de 1 minuto para día actual, 5min para rangos cortos
- **Visualización de Gaps**: Las gráficas muestran espacios donde no hay datos (sin interpolación falsa)

## 🛠️ Tecnologías

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: Dash, Plotly
- **IoT**: Azure IoT Hub, Event Hubs SDK
- **Base de Datos**: SQLite (desarrollo), PostgreSQL (producción)
- **Migraciones**: Alembic

## 📊 Dashboard

El dashboard permite:
- Visualizar datos en tiempo real (con 1 minuto de retraso)
- Filtrar por período de análisis (solo fechas con datos disponibles)
- Seleccionar dispositivos específicos
- Elegir sensores (Sensor 1, Sensor 2)
- Filtrar por tipo de partícula (PM2.5, PM10)
- Descargar reportes en Excel

## 🔧 Scripts Útiles

```powershell
# Verificar dispositivos
python scripts/check_devices.py

# Verificar datos de hoy
python scripts/check_data_today.py

# Poblar base de datos (desarrollo)
python scripts/seed_db.py
```

## 🐛 Troubleshooting

### El dashboard no muestra datos
- Verificar que el consumidor IoT esté corriendo
- Revisar logs en `logs/`
- Confirmar que hay datos en la base de datos: `python scripts/check_data_today.py`

### Error de conexión a IoT Hub
- Verificar credenciales en `.env`
- Confirmar que el Event Hub esté accesible
- Revisar consumer group configurado

## 📝 Licencia

Proyecto privado - TIP Colombia

## 👥 Autor

Jhon Santos - [@jhonsantos15](https://github.com/jhonsantos15)
