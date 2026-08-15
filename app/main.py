"""
Punto de entrada de la aplicación.

Responsabilidades de este archivo, y solo estas:
- Crear la instancia de FastAPI.
- Configurar middlewares (CORS).
- Montar routers y archivos estáticos.
- Arrancar/parar el scheduler de tareas en el ciclo de vida de la app.

Ninguna lógica de negocio ni de acceso a datos debe vivir aquí.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.tasks.scheduler import start_scheduler, stop_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.enable_scheduler:
        start_scheduler()
    yield
    if settings.enable_scheduler:
        stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Herramienta de análisis y apoyo a la decisión de inversión en fondos, ETFs y "
        "acciones. Uso exclusivamente informativo y educativo: no ejecuta operaciones "
        "ni constituye asesoramiento financiero."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "disclaimer": (
            "Esta aplicación proporciona información y herramientas de análisis con fines "
            "exclusivamente informativos y educativos. No constituye asesoramiento financiero "
            "ni recomendación personalizada de inversión."
        ),
    }
