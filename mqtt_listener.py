import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración MQTT
MQTT_BROKER = "localhost"  # Tu Raspberry Pi
MQTT_PORT = 1883
MQTT_TOPIC = "garden/sensors/data"

# MAPEO DE NOMBRES A IDs DE SENSORES
# Cambia esto según tus datos en la tabla sensores
SENSOR_MAP = {
    "IleanaTapiaCastillo": 1,  # Sensor 1
    "OtroNombre1": 2,            # Sensor 2
    "OtroNombre2": 3             # Sensor 3
}

def save_medicion(id_sensor: int, temp: float, hum: float):
    """Guarda una medición en PostgreSQL"""
    db = SessionLocal()
    try:
        medicion = models.Medicion(
            id_sensor=id_sensor,
            temperatura=temp,
            humedad=hum
        )
        db.add(medicion)
        db.commit()
        
        # Obtener info del sensor y planta
        sensor = db.query(models.Sensor).filter(models.Sensor.id_sensor == id_sensor).first()
        planta = db.query(models.Planta).filter(models.Planta.id_sensor == id_sensor).first()
        
        sensor_nombre = sensor.nombre if sensor else f"Sensor {id_sensor}"
        planta_nombre = planta.nombre if planta else "Sin planta"
        
        logger.info(f"✓ Guardado: {sensor_nombre} ({planta_nombre}) - {temp}°C, {hum}%")
        
        # Verificar alertas
        if planta:
            if temp < float(planta.temp_min) or temp > float(planta.temp_max):
                logger.warning(f"⚠️  ALERTA TEMPERATURA: {planta_nombre} fuera de rango!")
            if hum < float(planta.humedad_min) or hum > float(planta.humedad_max):
                logger.warning(f"⚠️  ALERTA HUMEDAD: {planta_nombre} fuera de rango!")
                
    except Exception as e:
        logger.error(f"Error guardando: {e}")
        db.rollback()
    finally:
        db.close()

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        logger.info("✓ Conectado a MQTT Broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"✓ Suscrito a: {MQTT_TOPIC}")
    else:
        logger.error(f"✗ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje MQTT"""
    try:
        # Formato: "IleanaTapiaCastillo-A01773374-25.50-60.30"
        payload = msg.payload.decode('utf-8')
        logger.info(f"📨 Mensaje recibido: {payload}")
        
        parts = payload.split('-')
        if len(parts) == 4:
            nombre = parts[0]
            matricula = parts[1]
            temp = float(parts[2])
            hum = float(parts[3])
            
            # Mapear nombre a ID de sensor
            id_sensor = SENSOR_MAP.get(nombre)
            
            if id_sensor:
                save_medicion(id_sensor, temp, hum)
            else:
                logger.warning(f"⚠️  Sensor no reconocido: {nombre}")
                logger.info(f"💡 Sensores válidos: {list(SENSOR_MAP.keys())}")
        else:
            logger.warning(f"Formato inválido: {payload}")
            
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

def main():
    """Inicia el listener MQTT"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    logger.info("🚀 Iniciando MQTT Listener para Jardín IoT...")
    logger.info(f"📡 Conectando a {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"🌱 Sensores configurados: {list(SENSOR_MAP.keys())}")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("\n👋 Deteniendo listener...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
