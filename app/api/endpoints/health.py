"""Endpoint de estado de la aplicación (uso interno y para Docker healthcheck)."""
import datetime as dt

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Comprueba que la API responde y que la base de datos es alcanzable.
    No expone lógica de negocio: solo diagnóstico de infraestructura.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - queremos capturar cualquier fallo de conexión
        db_status = f"error: {exc.__class__.__name__}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
