import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from database import SessionLocal
import models
import logging
from datetime import datetime
import math

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG por ahora para diagnóstico; cámbialo a INFO cuando esté resuelto
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# CONFIGURACIÓN MQTT
BROKER = "192.168.0.71"
PORT = 1883
TOPIC = "garden/sensors/data"

def validar_datos(temp: float, hum: float) -> bool:
    """Valida que los datos estén en rangos razonables"""
    if not (isinstance(temp, (int, float)) and math.isfinite(temp)):
        logger.error("Temperatura no es un número finito: %r", temp)
        return False

    if not (isinstance(hum, (int, float)) and math.isfinite(hum)):
        logger.error("Humedad no es un número finito: %r", hum)
        return False

    if not (-50 <= temp <= 100):
        logger.error("Temperatura fuera de rango: %s", temp)
        return False

    if not (0 <= hum <= 100):
        logger.error("Humedad fuera de rango: %s", hum)
        return False

    return True

def get_or_create_sensor(db: Session, nombre: str):
    """Busca un sensor por nombre; si no existe lo crea y devuelve la instancia"""
    try:
        sensor = db.query(models.Sensor).filter(models.Sensor.nombre == nombre).first()
        if sensor:
            logger.debug("Sensor encontrado en DB: %s (id=%s)", nombre, getattr(sensor, "id", getattr(sensor, "id_sensor", None)))
            return sensor

        sensor = models.Sensor(nombre=nombre)
        db.add(sensor)
        db.commit()
        db.refresh(sensor)
        logger.info("Sensor creado: %s (id=%s)", nombre, getattr(sensor, "id", getattr(sensor, "id_sensor", None)))
        return sensor
    except Exception:
        logger.exception("Error al obtener/crear sensor '%s'", nombre)
        try:
            db.rollback()
        except Exception:
            logger.exception("Error al hacer rollback")
        return None

def guardar_medicion(db: Session, id_sensor: int, temp: float, hum: float):
    """Guarda una medición en PostgreSQL usando la sesión pasada"""
    try:
        medicion = models.Medicion(
            id_sensor=id_sensor,
            temperatura=temp,
            humedad=hum,
            hora=datetime.now()
        )
        db.add(medicion)
        db.commit()
        logger.info("Medición guardada en DB: sensor_id=%s temp=%s hum=%s", id_sensor, temp, hum)

        # Obtener datos relacionados para logs/alertas
        try:
            sensor = db.query(models.Sensor).filter(
                (getattr(models.Sensor, "id_sensor", None) == id_sensor) if hasattr(models.Sensor, "id_sensor") else False
            ).first()
        except Exception:
            # Fallback: buscar por la columna primaria 'id'
            sensor = db.query(models.Sensor).filter(models.Sensor.id == id_sensor).first()

        planta = db.query(models.Planta).filter(models.Planta.id_sensor == id_sensor).first()

        sensor_nombre = sensor.nombre if sensor else f"sensor_{id_sensor}"
        planta_nombre = planta.nombre if planta else None

        # Verificar alertas si existe planta
        if planta:
            try:
                if planta.temp_min is not None and (temp < float(planta.temp_min) or temp > float(planta.temp_max)):
                    logger.warning("Temperatura fuera de rango para %s: %s (min=%s max=%s)", planta.nombre, temp, planta.temp_min, planta.temp_max)
                if planta.humedad_min is not None and (hum < float(planta.humedad_min) or hum > float(planta.humedad_max)):
                    logger.warning("Humedad fuera de rango para %s: %s (min=%s max=%s)", planta.nombre, hum, planta.humedad_min, planta.humedad_max)
            except Exception:
                logger.exception("Error al verificar rangos de planta (posibles valores inválidos en DB)")
    except Exception:
        logger.exception("Error al guardar medición (rollback)")
        try:
            db.rollback()
        except Exception:
            logger.exception("Error al hacer rollback después del fallo al guardar medición")

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        logger.info("Conectado al broker MQTT %s:%s, suscribiendo al topic %s", BROKER, PORT, TOPIC)
        client.subscribe(TOPIC)
    else:
        logger.error("Fallo conexión MQTT, rc=%s", rc)

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje MQTT"""
    try:
        logger.debug("Mensaje recibido (bytes): %r", msg.payload)
        mensaje = msg.payload.decode('utf-8', errors='replace').strip()
        logger.info("Mensaje recibido en topic %s: %s", msg.topic, mensaje)

        # Formato esperado: Nombre-Matricula-Temperatura-Humedad
        datos = mensaje.split('-')
        if len(datos) != 4:
            # intentar separadores alternativos comunes
            for sep in [';', ',', ' ']:
                if len(mensaje.split(sep)) == 4:
                    datos = mensaje.split(sep)
                    logger.debug("Usando separador alternativo '%s'", sep)
                    break

        if len(datos) != 4:
            logger.error("Formato inválido, se esperaba 4 campos, llegaron %d: %s", len(datos), mensaje)
            return

        nombre = datos[0].strip()
        matricula = datos[1].strip()
        if matricula == "":
            logger.error("Matricula vacía en mensaje: %s", mensaje)
            return

        # Aceptar coma decimal transformándola a punto
        temp_str = datos[2].strip().replace(',', '.')
        hum_str = datos[3].strip().replace(',', '.')

        try:
            temperatura = float(temp_str)
            humedad = float(hum_str)
        except ValueError:
            logger.exception("No se pudieron convertir temperatura/humedad a float: '%s' / '%s'", temp_str, hum_str)
            return

        if not validar_datos(temperatura, humedad):
            logger.debug("Datos rechazados por validación: temp=%s hum=%s", temperatura, humedad)
            return

        db = SessionLocal()
        try:
            sensor = get_or_create_sensor(db, nombre)
            if not sensor:
                logger.error("No se pudo obtener o crear el sensor '%s'", nombre)
                return

            id_sensor = getattr(sensor, "id_sensor", None) or getattr(sensor, "id", None)
            if not id_sensor:
                logger.error("El objeto sensor no tiene atributo 'id' ni 'id_sensor': %r", sensor)
                return

            guardar_medicion(db, id_sensor, temperatura, humedad)
        finally:
            db.close()

    except Exception:
        logger.exception("Error inesperado procesando mensaje MQTT")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()
        logger.info("Desconectado por KeyboardInterrupt")
    except Exception:
        logger.exception("Error en el loop principal MQTT")

if __name__ == "__main__":
    main()
