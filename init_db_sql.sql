-- ================================================================
-- JARDÍN IoT - INICIALIZACIÓN DE BASE DE DATOS
-- ================================================================

-- Crear base de datos
CREATE DATABASE jardin_iot;

-- Conectarse a la base de datos
\c jardin_iot

-- ================================================================
-- TABLA: SENSORES
-- ================================================================
CREATE TABLE sensores (
    id_sensor SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    ubicacion VARCHAR(100),
    activo BOOLEAN DEFAULT true
);

-- ================================================================
-- TABLA: PLANTAS
-- ================================================================
CREATE TABLE plantas (
    id_planta SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    id_sensor INTEGER REFERENCES sensores(id_sensor),
    temp_min DECIMAL(5,2),
    temp_max DECIMAL(5,2),
    humedad_min DECIMAL(5,2),
    humedad_max DECIMAL(5,2)
);

-- ================================================================
-- TABLA: MEDICIONES
-- ================================================================
CREATE TABLE mediciones (
    id_medicion SERIAL PRIMARY KEY,
    id_sensor INTEGER REFERENCES sensores(id_sensor) NOT NULL,
    hora TIMESTAMP DEFAULT NOW(),
    temperatura DECIMAL(5,2) NOT NULL,
    humedad DECIMAL(5,2) NOT NULL
);

-- Índice para búsquedas rápidas por fecha
CREATE INDEX idx_mediciones_hora ON mediciones(hora);
CREATE INDEX idx_mediciones_sensor ON mediciones(id_sensor);

-- ================================================================
-- DATOS INICIALES - SENSORES
-- ================================================================
INSERT INTO sensores (nombre, ubicacion) VALUES
('Sensor 1', 'Zona Centro'),
('Sensor 2', 'Zona Este'),
('Sensor 3', 'Zona Oeste');

-- ================================================================
-- DATOS INICIALES - PLANTAS
-- ================================================================
INSERT INTO plantas (nombre, id_sensor, temp_min, temp_max, humedad_min, humedad_max) VALUES
('Tomate', 1, 15.0, 30.0, 60.0, 80.0),
('Albahaca', 2, 18.0, 28.0, 50.0, 70.0),
('Lechuga', 3, 10.0, 24.0, 65.0, 85.0);

-- ================================================================
-- VERIFICACIÓN
-- ================================================================
SELECT 'Sensores creados:' as info;
SELECT * FROM sensores;

SELECT 'Plantas creadas:' as info;
SELECT * FROM plantas;

SELECT 'Tablas creadas exitosamente!' as resultado;