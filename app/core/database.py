"""
Configuración de la conexión a base de datos y gestión de sesiones SQLAlchemy.

Este módulo NO contiene lógica de negocio. Únicamente expone:
- `engine`: el motor de conexión.
- `SessionLocal`: factory de sesiones.
- `get_db`: dependencia de FastAPI para inyectar una sesión por request.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=True,  # evita conexiones muertas tras inactividad
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db() -> Generator:
    """Dependencia FastAPI: entrega una sesión por request y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
