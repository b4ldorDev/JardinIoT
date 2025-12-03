#!/bin/bash

# ================================================================
# JARDÍN IoT - Script de Configuración de IP
# ================================================================
# Este script cambia la IP de la Raspberry Pi en todos los archivos
# necesarios para que el sistema funcione correctamente.
# ================================================================

echo ""
echo "█████████████████████████████████████████████████████████████"
echo "█                                                           █"
echo "█           🌱 JARDÍN IoT - CONFIGURACIÓN 🌱                █"
echo "█                                                           █"
echo "█████████████████████████████████████████████████████████████"
echo ""

# Obtener el directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verificar que estamos en el directorio correcto
if [ ! -d "$SCRIPT_DIR/backend" ] || [ ! -d "$SCRIPT_DIR/frontend" ]; then
    echo "❌ Error: No se encontró la estructura de carpetas correcta."
    echo "   Asegúrate de ejecutar este script desde el directorio raíz del proyecto."
    exit 1
fi

# Solicitar la IP de la Raspberry Pi
echo "📍 Ingresa la IP de tu Raspberry Pi:"
echo "   (Ejemplo: 192.168.1.100)"
echo ""
read -p "   IP: " RASPBERRY_IP

# Validar que se ingresó una IP
if [ -z "$RASPBERRY_IP" ]; then
    echo ""
    echo "❌ Error: Debes ingresar una IP válida."
    exit 1
fi

# Validar formato básico de IP (4 grupos de números separados por puntos)
if ! [[ $RASPBERRY_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo ""
    echo "❌ Error: Formato de IP inválido."
    echo "   Usa el formato: XXX.XXX.XXX.XXX"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo " Configurando IP: $RASPBERRY_IP"
echo "════════════════════════════════════════════════════════════"
echo ""

# ================================================================
# 1. Configurar frontend/app.js
# ================================================================
FRONTEND_FILE="$SCRIPT_DIR/frontend/app.js"
if [ -f "$FRONTEND_FILE" ]; then
    # Reemplazar cualquier IP o placeholder con la nueva IP
    sed -i "s|http://[0-9A-Za-z_.]\+:8000/api|http://$RASPBERRY_IP:8000/api|g" "$FRONTEND_FILE"
    echo "✅ frontend/app.js configurado"
else
    echo "⚠️  frontend/app.js no encontrado"
fi

# ================================================================
# 2. Configurar backend/mqtt_listener.py
# ================================================================
MQTT_FILE="$SCRIPT_DIR/backend/mqtt_listener.py"
if [ -f "$MQTT_FILE" ]; then
    # Reemplazar cualquier IP o placeholder en la variable MQTT_BROKER
    sed -i "s|MQTT_BROKER = os.getenv(\"MQTT_BROKER\", \"[0-9A-Za-z_.]\+\")|MQTT_BROKER = os.getenv(\"MQTT_BROKER\", \"$RASPBERRY_IP\")|g" "$MQTT_FILE"
    echo "✅ backend/mqtt_listener.py configurado"
else
    echo "⚠️  backend/mqtt_listener.py no encontrado"
fi

# ================================================================
# 3. Configurar esp8266/esp8266_sensor.ino
# ================================================================
ESP_FILE="$SCRIPT_DIR/esp8266/esp8266_sensor.ino"
if [ -f "$ESP_FILE" ]; then
    # Reemplazar cualquier IP o placeholder en MQTT_SERVER
    sed -i "s|MQTT_SERVER = \"[0-9A-Za-z_.]\+\"|MQTT_SERVER = \"$RASPBERRY_IP\"|g" "$ESP_FILE"
    echo "✅ esp8266/esp8266_sensor.ino configurado"
else
    echo "⚠️  esp8266/esp8266_sensor.ino no encontrado"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo " ✅ CONFIGURACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════"
echo ""
echo " Archivos configurados con IP: $RASPBERRY_IP"
echo ""
echo " 📋 PRÓXIMOS PASOS:"
echo ""
echo " 1. Instalar dependencias del backend:"
echo "    cd backend"
echo "    python3 -m venv venv"
echo "    source venv/bin/activate"
echo "    pip install -r requirements.txt"
echo ""
echo " 2. Crear base de datos PostgreSQL:"
echo "    sudo -u postgres psql -f database/init_database.sql"
echo ""
echo " 3. Configurar password de PostgreSQL:"
echo "    Edita backend/database.py y cambia 'tu_password'"
echo ""
echo " 4. Configurar nombre del sensor en:"
echo "    - backend/mqtt_listener.py (SENSOR_MAP)"
echo "    - esp8266/esp8266_sensor.ino (NOMBRE y MATRICULA)"
echo ""
echo " 5. Configurar WiFi en esp8266/esp8266_sensor.ino:"
echo "    - WIFI_SSID"
echo "    - WIFI_PASSWORD"
echo ""
echo " 6. Subir código al ESP8266 usando Arduino IDE"
echo ""
echo " 7. Iniciar servicios:"
echo "    # Terminal 1 - MQTT Listener:"
echo "    cd backend && source venv/bin/activate"
echo "    python mqtt_listener.py"
echo ""
echo "    # Terminal 2 - API:"
echo "    cd backend && source venv/bin/activate"
echo "    uvicorn app:app --host 0.0.0.0 --port 8000"
echo ""
echo "    # Terminal 3 - Frontend:"
echo "    cd frontend"
echo "    python3 -m http.server 3000"
echo ""
echo " 8. Acceder al dashboard:"
echo "    http://$RASPBERRY_IP:3000"
echo ""
echo "════════════════════════════════════════════════════════════"
echo " 🌱 ¡Disfruta monitoreando tus plantas! 🌱"
echo "════════════════════════════════════════════════════════════"
echo ""
