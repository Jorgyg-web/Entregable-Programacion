# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Base de datos local SQLite
DATABASE_URL = "sqlite:///./liga.db"

# Crear el engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite en entorno multihilo (FastAPI)
)

# Sesión de conexión a la base de datos
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
