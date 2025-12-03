# 🌱 Jardín IoT - Sistema de Monitoreo de Plantas

Sistema completo de monitoreo de plantas usando **ESP8266**, **DHT11**, **MQTT**, **PostgreSQL** y **FastAPI**.

![Dashboard](https://img.shields.io/badge/Status-Online-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)

##  Descripción

Este proyecto te permite monitorear en tiempo real la temperatura y humedad de tus plantas con:
- Sensores **ESP8266 + DHT11**
- Comunicación **MQTT**
- Base de datos **PostgreSQL**
- API REST con **FastAPI**
- Dashboard web **estilo terminal retro**
-  **Alertas automáticas** cuando las condiciones salen del rango óptimo

##  Arquitectura

```
ESP8266 (DHT11) ──MQTT──> Raspberry Pi
                            │
                            ├─ Mosquitto (Broker MQTT)
                            ├─ PostgreSQL (Base de datos)
                            ├─ Python MQTT Listener
                            ├─ FastAPI (REST API)
                            └─ Frontend (HTML/CSS/JS)
```

##  Estructura del Proyecto

```
jardin-iot/
├── backend/
│   ├── app.py              # API FastAPI
│   ├── database.py         # Configuración de PostgreSQL
│   ├── models.py           # Modelos SQLAlchemy
│   ├── mqtt_listener.py    # Listener MQTT → PostgreSQL
│   └── requirements.txt    # Dependencias Python
├── frontend/
│   ├── index.html          # Dashboard
│   ├── styles.css          # Estilos retro terminal
│   └── app.js              # Lógica del frontend
├── database/
│   └── init_database.sql   # Script de inicialización
├── esp8266/
│   └── esp8266_sensor.ino  # Código para ESP8266
└── README.md
```

## Instalación 

### Requisitos Previos

- **Raspberry Pi** con Raspbian/Raspberry Pi OS
- **Python 3.8+**
- **PostgreSQL 12+**
- **Mosquitto MQTT Broker**
- **ESP8266** con sensor **DHT11**

### Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/jardin-iot.git
cd jardin-iot
```

### Instalar PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Crear Base de Datos

```bash
sudo -u postgres psql -f database/init_database.sql
```

### Instalar Mosquitto

```bash
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

###  Configurar Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**IMPORTANTE:** Edita `database.py` y cambia el password de PostgreSQL:

```python
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_password_aqui")
```

** IMPORTANTE:** Edita `mqtt_listener.py` y configura los nombres de tus sensores:

```python
SENSOR_MAP = {
    "TuNombre": 1,  # Debe coincidir con el nombre en el ESP8266
}
```

### Configurar Frontend

Edita `frontend/app.js` línea 5:

```javascript
const API_URL = 'http://TU_IP_RASPBERRY:8000/api';
```

### Programar ESP8266

1. Abre `esp8266/esp8266_sensor.ino` en Arduino IDE
2. Modifica:
   ```cpp
   const char* WIFI_SSID = "tu_red_wifi";
   const char* WIFI_PASSWORD = "tu_password";
   const char* MQTT_SERVER = "IP_DE_TU_RASPBERRY";
   const char* NOMBRE = "TuNombre";
   const char* MATRICULA = "TuMatricula";
   ```
3. Sube el código al ESP8266

##  Ejecutar el Sistema

### Opción 1: Manual (para pruebas)

**Terminal 1 - MQTT Listener:**
```bash
cd backend
source venv/bin/activate
python mqtt_listener.py
```

**Terminal 2 - API:**
```bash
cd backend
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
python3 -m http.server 3000
```

### Opción 2: Servicios Systemd (auto-inicio)

**Crear servicios:**

```bash
# MQTT Listener
sudo nano /etc/systemd/system/jardin-mqtt.service
```

```ini
[Unit]
Description=Jardin IoT MQTT Listener
After=network.target postgresql.service mosquitto.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/jardin-iot/backend
Environment="PATH=/home/pi/jardin-iot/backend/venv/bin"
ExecStart=/home/pi/jardin-iot/backend/venv/bin/python mqtt_listener.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# API
sudo nano /etc/systemd/system/jardin-api.service
```

```ini
[Unit]
Description=Jardin IoT API
After=network.target postgresql.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/jardin-iot/backend
Environment="PATH=/home/pi/jardin-iot/backend/venv/bin"
ExecStart=/home/pi/jardin-iot/backend/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Frontend
sudo nano /etc/systemd/system/jardin-frontend.service
```

```ini
[Unit]
Description=Jardin IoT Frontend
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/jardin-iot/frontend
ExecStart=/usr/bin/python3 -m http.server 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Activar servicios:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable jardin-mqtt jardin-api jardin-frontend
sudo systemctl start jardin-mqtt jardin-api jardin-frontend
```

## Acceso al Sistema

- **Dashboard:** `http://TU_IP_RASPBERRY:3000`
- **API Docs:** `http://TU_IP_RASPBERRY:8000/docs`
- **API Root:** `http://TU_IP_RASPBERRY:8000`

## 🔌 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información del sistema |
| GET | `/api/sensores` | Lista de sensores |
| GET | `/api/plantas` | Lista de plantas |
| GET | `/api/mediciones/ultimas` | Última medición de cada sensor |
| GET | `/api/mediciones` | Historial de mediciones |
| GET | `/api/mediciones/sensor/{id}` | Mediciones de un sensor |
| GET | `/api/estadisticas` | Estadísticas generales |
| GET | `/api/estadisticas/sensor/{id}` | Estadísticas por sensor |

## Base de Datos

### Tablas

**sensores**
```sql
id_sensor | nombre    | ubicacion   | activo
----------|-----------|-------------|-------
1         | Sensor 1  | Zona Centro | true
```

**plantas**
```sql
id_planta | nombre  | id_sensor | temp_min | temp_max | humedad_min | humedad_max
----------|---------|-----------|----------|----------|-------------|------------
1         | Tomate  | 1         | 15.0     | 30.0     | 60.0        | 80.0
```

**mediciones**
```sql
id_medicion | id_sensor | hora                | temperatura | humedad
------------|-----------|---------------------|-------------|--------
1           | 1         | 2024-03-20 10:30:00 | 25.5        | 68.0
```

## Comandos Útiles

### Ver logs en tiempo real
```bash
sudo journalctl -u jardin-mqtt -f
sudo journalctl -u jardin-api -f
```

### Verificar estado de servicios
```bash
sudo systemctl status jardin-mqtt
sudo systemctl status jardin-api
sudo systemctl status jardin-frontend
```

### Consultar base de datos
```bash
psql -U postgres -d jardin_iot
```

```sql
-- Ver últimas 10 mediciones
SELECT 
    s.nombre AS sensor,
    p.nombre AS planta,
    m.hora,
    m.temperatura,
    m.humedad
FROM mediciones m
JOIN sensores s ON m.id_sensor = s.id_sensor
LEFT JOIN plantas p ON s.id_sensor = p.id_sensor
ORDER BY m.hora DESC
LIMIT 10;
```

### Probar MQTT manualmente
```bash
# Suscribirse
mosquitto_sub -h localhost -t "garden/sensors/data"

# Publicar mensaje de prueba
mosquitto_pub -h localhost -t "garden/sensors/data" -m "Test-A12345-25.5-68.0"
```

##  Solución de Problemas

### No llegan datos

1. Verificar que Mosquitto esté corriendo:
   ```bash
   sudo systemctl status mosquitto
   ```

2. Verificar logs del listener:
   ```bash
   sudo journalctl -u jardin-mqtt -n 50
   ```

3. Probar MQTT manualmente:
   ```bash
   mosquitto_sub -h localhost -t "garden/sensors/data"
   ```

### Error de conexión a PostgreSQL

Verifica el password en `database.py` y que PostgreSQL esté corriendo:
```bash
sudo systemctl status postgresql
```

### Frontend no actualiza

1. Verifica que la API esté respondiendo:
   ```bash
   curl http://localhost:8000/api/estadisticas
   ```

2. Abre la consola del navegador (F12) y busca errores

3. Verifica que la IP en `app.js` sea correcta

## Screenshots

### Dashboard Principal
![Dashboard](docs/dashboard.png)

### Tarjetas de Plantas con Alertas
![Alertas](docs/alertas.png)

### API Documentation
![API Docs](docs/api-docs.png)

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: Amazing Feature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más información.

## 👤 Autor


- GitHub: [@b4ldorDev](https://github.com/b4ldirDev)

---

** Hecho con Python, FastAPI y mucho ☕**
