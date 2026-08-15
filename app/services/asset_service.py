"""
Reglas de negocio de Asset. No conoce FastAPI ni construye queries SQL
directamente: delega en AssetRepository.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    def __init__(self, db: Session):
        self.repo = AssetRepository(db)

    def get_or_404(self, asset_id: int) -> Asset:
        asset = self.repo.get(asset_id)
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activo no encontrado")
        return asset

    def list_assets(
        self,
        asset_type: AssetType | None,
        only_featured: bool,
        limit: int,
        offset: int,
    ) -> list[Asset]:
        return self.repo.list(
            asset_type=asset_type, only_featured=only_featured, limit=limit, offset=offset
        )

    def search(self, q: str) -> list[Asset]:
        if not q or len(q.strip()) < 1:
            return []
        return self.repo.search(q)

    def create(self, data: AssetCreate) -> Asset:
        if data.isin and self.repo.get_by_isin(data.isin):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un activo con ISIN {data.isin}",
            )
        asset = Asset(**data.model_dump())
        return self.repo.create(asset)

    def update(self, asset_id: int, data: AssetUpdate) -> Asset:
        asset = self.get_or_404(asset_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        return self.repo.update(asset)

    def delete(self, asset_id: int) -> None:
        asset = self.get_or_404(asset_id)
        self.repo.delete(asset)
