from fastapi import FastAPI, Depends, HTTPException # Crear  la aplicación , Depends importa dependencias para libreria  en esta nos importa s la conexión con la db   
from fastapi.middleware.cors import CORSMiddleware   # Permite peticiones de otros dominios 
from sqlalchemy.orm import Session   # nos permite crear una sesion para manejar la db 
from sqlalchemy import desc, func  # nos permite usar funciones sql  ORDER BY DESC, COUNT
from typing import List, Optional # 
from datetime import datetime
import models  # Para los modelos de la base de datos 
from database import get_db  #obtener la conexion a la db 

# ================================================================
# CONFIGURACIÓN DE FASTAPI
# ================================================================
app = FastAPI(
    title="Jardín IoT API",
    description="Sistema de monitoreo de plantas con ESP8266 y DHT11",
    version="1.0.0"
)

# CORS - Permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# ROOT
# ================================================================
@app.get("/")
def root():
    """Endpoint raíz - Información del sistema"""
    return {
        "sistema": "Jardín IoT",
        "version": "2.0.0",
        "status": "online",
        "descripcion": "Sistema de monitoreo de plantas con ESP8266 y DHT11"
    }

# ================================================================
# SENSORES
# ================================================================
@app.get("/api/sensores")
def listar_sensores(db: Session = Depends(get_db)):
    """Obtiene la lista de todos los sensores"""
    sensores = db.query(models.Sensor).all()
    return [
        {
            "id": s.id_sensor,
            "nombre": s.nombre,
            "ubicacion": s.ubicacion,
            "activo": s.activo
        }
        for s in sensores
    ]

# ================================================================
# PLANTAS
# ================================================================
@app.get("/api/plantas")
def listar_plantas(db: Session = Depends(get_db)):
    """Obtiene la lista de todas las plantas con sus configuraciones"""
    plantas = db.query(models.Planta).all()
    return [
        {
            "id": p.id_planta,
            "nombre": p.nombre,
            "sensor": {
                "id": p.sensor.id_sensor,
                "nombre": p.sensor.nombre,
                "ubicacion": p.sensor.ubicacion
            } if p.sensor else None,
            "rangos": {
                "temp_min": float(p.temp_min) if p.temp_min else None,
                "temp_max": float(p.temp_max) if p.temp_max else None,
                "humedad_min": float(p.humedad_min) if p.humedad_min else None,
                "humedad_max": float(p.humedad_max) if p.humedad_max else None
            }
        }
        for p in plantas
    ]

# ================================================================
# MEDICIONES - ÚLTIMAS POR SENSOR
# ================================================================
@app.get("/api/mediciones/ultimas")
def obtener_ultimas_mediciones(db: Session = Depends(get_db)):
    """
    Obtiene la última medición de cada sensor con:
    - Datos del sensor
    - Datos de la planta asociada
    - Indicadores de alerta si está fuera de rango
    """
    # Subconsulta: última hora de cada sensor
    subq = db.query(
        models.Medicion.id_sensor,
        func.max(models.Medicion.hora).label('ultima_hora')
    ).group_by(models.Medicion.id_sensor).subquery()
    
    # Consulta principal con joins
    resultados = db.query(
        models.Sensor,
        models.Planta,
        models.Medicion
    ).join(
        models.Medicion,
        models.Sensor.id_sensor == models.Medicion.id_sensor
    ).outerjoin(
        models.Planta,
        models.Sensor.id_sensor == models.Planta.id_sensor
    ).join(
        subq,
        (models.Medicion.id_sensor == subq.c.id_sensor) &
        (models.Medicion.hora == subq.c.ultima_hora)
    ).all()
    
    # Formatear respuesta
    respuesta = []
    for sensor, planta, medicion in resultados:
        temp = float(medicion.temperatura)
        hum = float(medicion.humedad)
        
        # Calcular alertas
        alerta_temp = False
        alerta_hum = False
        
        if planta:
            if planta.temp_min and planta.temp_max:
                alerta_temp = temp < float(planta.temp_min) or temp > float(planta.temp_max)
            if planta.humedad_min and planta.humedad_max:
                alerta_hum = hum < float(planta.humedad_min) or hum > float(planta.humedad_max)
        
        respuesta.append({
            "sensor": {
                "id": sensor.id_sensor,
                "nombre": sensor.nombre,
                "ubicacion": sensor.ubicacion
            },
            "planta": {
                "nombre": planta.nombre,
                "temp_min": float(planta.temp_min) if planta.temp_min else None,
                "temp_max": float(planta.temp_max) if planta.temp_max else None,
                "humedad_min": float(planta.humedad_min) if planta.humedad_min else None,
                "humedad_max": float(planta.humedad_max) if planta.humedad_max else None
            } if planta else None,
            "medicion": {
                "temperatura": temp,
                "humedad": hum,
                "hora": medicion.hora.isoformat(),
                "alerta_temp": alerta_temp,
                "alerta_humedad": alerta_hum
            }
        })
    
    return respuesta

# ================================================================
# MEDICIONES - HISTORIAL
# ================================================================
@app.get("/api/mediciones")
def obtener_mediciones(
    limit: int = 100,
    id_sensor: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de mediciones.
    - limit: número máximo de registros (default: 100)
    - id_sensor: filtrar por sensor específico (opcional)
    """
    query = db.query(models.Medicion)
    
    if id_sensor:
        query = query.filter(models.Medicion.id_sensor == id_sensor)
    
    mediciones = query.order_by(desc(models.Medicion.hora)).limit(limit).all()
    mediciones.reverse()  # Mostrar cronológicamente
    
    return [
        {
            "id_sensor": m.id_sensor,
            "hora": m.hora.strftime("%H:%M:%S"),
            "temperatura": float(m.temperatura),
            "humedad": float(m.humedad)
        }
        for m in mediciones
    ]

@app.get("/api/mediciones/sensor/{id_sensor}")
def obtener_mediciones_sensor(
    id_sensor: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Obtiene las últimas N mediciones de un sensor específico"""
    mediciones = db.query(models.Medicion)\
        .filter(models.Medicion.id_sensor == id_sensor)\
        .order_by(desc(models.Medicion.hora))\
        .limit(limit)\
        .all()
    
    if not mediciones:
        raise HTTPException(status_code=404, detail="Sensor no encontrado o sin mediciones")
    
    mediciones.reverse()
    
    return [
        {
            "hora": m.hora.strftime("%H:%M:%S"),
            "temperatura": float(m.temperatura),
            "humedad": float(m.humedad)
        }
        for m in mediciones
    ]

# ================================================================
# ESTADÍSTICAS
# ================================================================
@app.get("/api/estadisticas")
def obtener_estadisticas_generales(db: Session = Depends(get_db)):
    """Obtiene estadísticas generales del sistema"""
    
    # Estadísticas de mediciones
    stats = db.query(
        func.count(models.Medicion.id_medicion).label('total'),
        func.avg(models.Medicion.temperatura).label('temp_avg'),
        func.min(models.Medicion.temperatura).label('temp_min'),
        func.max(models.Medicion.temperatura).label('temp_max'),
        func.avg(models.Medicion.humedad).label('hum_avg'),
        func.min(models.Medicion.humedad).label('hum_min'),
        func.max(models.Medicion.humedad).label('hum_max')
    ).first()
    
    # Contadores
    sensores_activos = db.query(models.Sensor).filter(models.Sensor.activo == True).count()
    total_plantas = db.query(models.Planta).count()
    
    return {
        "sensores_activos": sensores_activos,
        "plantas": total_plantas,
        "total_mediciones": stats.total if stats.total else 0,
        "temperatura": {
            "promedio": round(float(stats.temp_avg), 2) if stats.temp_avg else 0,
            "minima": round(float(stats.temp_min), 2) if stats.temp_min else 0,
            "maxima": round(float(stats.temp_max), 2) if stats.temp_max else 0
        },
        "humedad": {
            "promedio": round(float(stats.hum_avg), 2) if stats.hum_avg else 0,
            "minima": round(float(stats.hum_min), 2) if stats.hum_min else 0,
            "maxima": round(float(stats.hum_max), 2) if stats.hum_max else 0
        }
    }

@app.get("/api/estadisticas/sensor/{id_sensor}")
def obtener_estadisticas_sensor(id_sensor: int, db: Session = Depends(get_db)):
    """Obtiene estadísticas de un sensor específico"""
    
    # Verificar que el sensor existe
    sensor = db.query(models.Sensor).filter(models.Sensor.id_sensor == id_sensor).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    
    # Estadísticas
    stats = db.query(
        func.count(models.Medicion.id_medicion).label('total'),
        func.avg(models.Medicion.temperatura).label('temp_avg'),
        func.min(models.Medicion.temperatura).label('temp_min'),
        func.max(models.Medicion.temperatura).label('temp_max'),
        func.avg(models.Medicion.humedad).label('hum_avg'),
        func.min(models.Medicion.humedad).label('hum_min'),
        func.max(models.Medicion.humedad).label('hum_max')
    ).filter(models.Medicion.id_sensor == id_sensor).first()
    
    planta = db.query(models.Planta).filter(models.Planta.id_sensor == id_sensor).first()
    
    return {
        "sensor": {
            "id": sensor.id_sensor,
            "nombre": sensor.nombre,
            "ubicacion": sensor.ubicacion
        },
        "planta": planta.nombre if planta else "Sin planta",
        "total_mediciones": stats.total if stats.total else 0,
        "temperatura": {
            "promedio": round(float(stats.temp_avg), 2) if stats.temp_avg else 0,
            "minima": round(float(stats.temp_min), 2) if stats.temp_min else 0,
            "maxima": round(float(stats.temp_max), 2) if stats.temp_max else 0
        },
        "humedad": {
            "promedio": round(float(stats.hum_avg), 2) if stats.hum_avg else 0,
            "minima": round(float(stats.hum_min), 2) if stats.hum_min else 0,
            "maxima": round(float(stats.hum_max), 2) if stats.hum_max else 0
        }
    }
