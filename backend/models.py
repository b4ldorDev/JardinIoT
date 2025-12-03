from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Sensor(Base):
    """
    Tabla: sensores
    Representa un sensor ESP8266 con DHT11
    """
    __tablename__ = "sensores"
    
    id_sensor = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    ubicacion = Column(String(100))
    activo = Column(Boolean, default=True)
    
    # Relaciones
    plantas = relationship("Planta", back_populates="sensor")
    mediciones = relationship("Medicion", back_populates="sensor")
    
    def __repr__(self):
        return f"<Sensor {self.nombre} - {self.ubicacion}>"


class Planta(Base):
    """
    Tabla: plantas
    Representa una planta monitoreada con sus rangos óptimos
    """
    __tablename__ = "plantas"
    
    id_planta = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    id_sensor = Column(Integer, ForeignKey('sensores.id_sensor'))
    temp_min = Column(DECIMAL(5, 2))
    temp_max = Column(DECIMAL(5, 2))
    humedad_min = Column(DECIMAL(5, 2))
    humedad_max = Column(DECIMAL(5, 2))
    
    # Relación
    sensor = relationship("Sensor", back_populates="plantas")
    
    def __repr__(self):
        return f"<Planta {self.nombre}>"


class Medicion(Base):
    """
    Tabla: mediciones
    Almacena las lecturas de temperatura y humedad de cada sensor
    """
    __tablename__ = "mediciones"
    
    id_medicion = Column(Integer, primary_key=True, index=True)
    id_sensor = Column(Integer, ForeignKey('sensores.id_sensor'), nullable=False)
    hora = Column(DateTime, default=datetime.utcnow, index=True)
    temperatura = Column(DECIMAL(5, 2), nullable=False)
    humedad = Column(DECIMAL(5, 2), nullable=False)
    
    # Relación
    sensor = relationship("Sensor", back_populates="mediciones")
    
    def __repr__(self):
        return f"<Medicion {self.hora}: {self.temperatura}°C, {self.humedad}%>"
