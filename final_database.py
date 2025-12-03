from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ================================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# Cambia estos valores según tu instalación de PostgreSQL
# ================================================================
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_password")  # CAMBIAR ESTO
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "jardin_iot")

# Construir URL de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    echo=False  # Cambia a True para debug SQL
)

# Crear SessionLocal para las consultas
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para los modelos
Base = declarative_base()

# Dependency para FastAPI
def get_db():
    """
    Generador que proporciona una sesión de base de datos.
    Se cierra automáticamente después de cada request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()