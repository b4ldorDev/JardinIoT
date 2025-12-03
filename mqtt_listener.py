import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración MQTT
MQTT_BROKER = "192.168.1.71"  
MQTT_PORT = 1883
MQTT_TOPIC = "garden/sensors/data"

# MAPEO DE NOMBRES A IDs DE SENSORES
# Ajusta estos valores a lo que tengas en tu tabla "sensor"
SENSOR_MAP = {
    "IleanaTapiaCastillo": 1,
    "OtroNombre1": 2,
    "OtroNombre2": 3
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
        
        sensor = db.query(models.Sensor).filter(models.Sensor.id_sensor == id_sensor).first()
        planta = db.query(models.Planta).filter(models.Planta.id_sensor == id_sensor).first()
        
        sensor_nombre = sensor.nombre if sensor else f"Sensor {id_sensor}"
        planta_nombre = planta.nombre if planta else "Sin planta"
        
        logger.info(f"Guardado: {sensor_nombre} ({planta_nombre}) - {temp}°C, {hum}%")
        
        if planta:
            if temp < float(planta.temp_min) or temp > float(planta.temp_max):
                logger.warning(f"Alerta temperatura: {planta_nombre} fuera de rango")
            if hum < float(planta.humedad_min) or hum > float(planta.humedad_max):
                logger.warning(f"Alerta humedad: {planta_nombre} fuera de rango")
                
    except Exception as e:
        logger.error(f"Error guardando: {e}")
        db.rollback()
    finally:
        db.close()


# ============================================
# LISTENER MQTT SEGURO: IGNORA DATOS MALOS
# ============================================

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        logger.info("Conectado a MQTT Broker")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Suscrito a: {MQTT_TOPIC}")
    else:
        logger.error(f"Error de conexión: {rc}")


def on_message(client, userdata, msg):
    """Callback seguro: ignora mensajes corruptos o inválidos"""
    try:
        payload = msg.payload.decode('utf-8').strip()
        logger.info(f"Mensaje recibido: {payload}")

        parts = payload.split('-')

        # Validar mínimo nombre-temp-hum
        if len(parts) < 3:
            logger.warning("Datos incompletos, ignorando mensaje")
            return

        nombre = parts[0]

        # Validar conversión de temperatura y humedad
        try:
            temp = float(parts[-2])
            hum = float(parts[-1])
        except ValueError:
            logger.warning("Temperatura o humedad inválidas, ignorando mensaje")
            return

        # Verificar que el sensor exista
        id_sensor = SENSOR_MAP.get(nombre)
        if id_sensor is None:
            logger.warning(f"Sensor no reconocido: {nombre}, ignorando")
            return

        # Guardar medición válida
        save_medicion(id_sensor, temp, hum)

    except Exception as e:
        logger.error(f"Error procesando mensaje, ignorado: {e}")


def main():
    """Inicia el listener MQTT"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    logger.info("Iniciando MQTT Listener para Jardín IoT...")
    logger.info(f"Conectando a {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Sensores configurados: {list(SENSOR_MAP.keys())}")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Deteniendo listener...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    main()
