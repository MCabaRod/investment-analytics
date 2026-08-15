import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.asset import AssetType
from app.repositories.price_repository import PriceHistoryRepository
from app.schemas.asset import AssetCreate, AssetRead, AssetSearchResult, AssetUpdate
from app.schemas.metrics import AssetMetricsResponse
from app.schemas.price import AssetHistoryResponse
from app.services.asset_service import AssetService
from app.services.metrics_service import MetricsService
from app.services.price_ingestion_service import PriceIngestionService

router = APIRouter()


@router.get("", response_model=list[AssetRead])
def list_assets(
    asset_type: AssetType | None = Query(default=None),
    featured: bool = Query(default=False, description="Devolver solo los activos destacados"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Lista activos, opcionalmente filtrados por tipo o restringidos a destacados."""
    return AssetService(db).list_assets(asset_type, featured, limit, offset)


@router.get("/search", response_model=list[AssetSearchResult])
def search_assets(
    q: str = Query(..., min_length=1, description="Nombre, ticker o ISIN (coincidencia parcial)"),
    db: Session = Depends(get_db),
):
    return AssetService(db).search(q)


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    return AssetService(db).get_or_404(asset_id)


@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    """
    Alta de activo. En el MVP no hay panel de administración, pero este
    endpoint es el punto de entrada que usará (punto 31 del encargo).
    """
    return AssetService(db).create(payload)


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: int, payload: AssetUpdate, db: Session = Depends(get_db)):
    """Actualización parcial: p.ej. marcar/desmarcar destacado y su orden."""
    return AssetService(db).update(asset_id, payload)


@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    AssetService(db).delete(asset_id)


@router.get("/{asset_id}/history", response_model=AssetHistoryResponse)
def get_asset_history(
    asset_id: int,
    start: dt.date | None = Query(default=None),
    end: dt.date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Histórico almacenado (nunca se llama a un proveedor externo en este
    endpoint — punto 24: el usuario siempre lee de base de datos, la
    ingesta la hace el scheduler o el endpoint de refresco manual).
    """
    AssetService(db).get_or_404(asset_id)  # 404 si no existe
    end = end or dt.date.today()
    start = start or (end - dt.timedelta(days=365))

    repo = PriceHistoryRepository(db)
    rows = repo.get_range(asset_id, start, end)
    last_updated = repo.get_last_retrieved_at(asset_id)

    note = None
    if not rows:
        note = "Sin datos almacenados para este rango. Fuerza una actualización con POST /refresh."

    return AssetHistoryResponse(
        asset_id=asset_id,
        points=rows,
        last_updated=last_updated,
        note=note,
    )


@router.post("/{asset_id}/refresh", response_model=AssetHistoryResponse)
def refresh_asset_history(asset_id: int, db: Session = Depends(get_db)):
    """
    Fuerza una actualización de histórico para este activo (capacidad de
    administración del punto 31). Ejecuta la ingesta de forma síncrona: para
    el volumen del MVP es aceptable, pero en producción convendría lanzarlo
    como tarea en background si se abre a muchos usuarios.
    """
    asset = AssetService(db).get_or_404(asset_id)
    PriceIngestionService(db).update_asset(asset)

    repo = PriceHistoryRepository(db)
    end = dt.date.today()
    start = end - dt.timedelta(days=365)
    rows = repo.get_range(asset_id, start, end)
    return AssetHistoryResponse(
        asset_id=asset_id,
        points=rows,
        last_updated=repo.get_last_retrieved_at(asset_id),
    )


@router.get("/{asset_id}/metrics", response_model=AssetMetricsResponse)
def get_asset_metrics(asset_id: int, db: Session = Depends(get_db)):
    """
    Rentabilidad (YTD, 1/3/5 años, desde inicio) y riesgo (volatilidad,
    drawdown, Sharpe, Sortino) calculados sobre el histórico almacenado.
    Cualquier métrica sin datos suficientes se devuelve como `null` — el
    frontend debe mostrarlo como "N/D" (punto 40 del encargo: nunca inventar
    un dato financiero).
    """
    AssetService(db).get_or_404(asset_id)
    return MetricsService(db).compute(asset_id)
