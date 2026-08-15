"""
Router raíz de la API.

Cada nuevo grupo de endpoints (assets, favorites, compare, ...) se registrará
aquí en fases posteriores. Mantiene `main.py` limpio y desacoplado de los
detalles de cada recurso.
"""
from fastapi import APIRouter

from app.api.endpoints import assets, favorites, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])

# Fase 3 en adelante:
# from app.api.endpoints import compare
# api_router.include_router(compare.router, prefix="/compare", tags=["compare"])
