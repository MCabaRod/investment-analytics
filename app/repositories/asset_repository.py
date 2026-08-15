"""
Repositorio de Asset: única capa que construye queries SQLAlchemy.

Los services dependen de esta interfaz concreta (en el MVP no hace falta
abstraerla con ABC porque solo hay una implementación — Postgres/SQLAlchemy),
pero mantenerla separada de `services/` permite testear la lógica de negocio
con un repositorio falso si algún día hiciera falta.
"""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, asset_id: int) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def list(
        self,
        asset_type: AssetType | None = None,
        only_active: bool = True,
        only_featured: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Asset]:
        query = self.db.query(Asset)
        if only_active:
            query = query.filter(Asset.is_active.is_(True))
        if asset_type is not None:
            query = query.filter(Asset.asset_type == asset_type)
        if only_featured:
            query = query.filter(Asset.is_featured.is_(True)).order_by(
                Asset.featured_order.asc().nulls_last()
            )
        else:
            query = query.order_by(Asset.name.asc())
        return query.offset(offset).limit(limit).all()

    def search(self, q: str, limit: int = 20) -> list[Asset]:
        """Búsqueda parcial (case-insensitive) por nombre, ticker o ISIN."""
        pattern = f"%{q.strip()}%"
        return (
            self.db.query(Asset)
            .filter(
                Asset.is_active.is_(True),
                or_(
                    Asset.name.ilike(pattern),
                    Asset.ticker.ilike(pattern),
                    Asset.isin.ilike(pattern),
                ),
            )
            .order_by(Asset.name.asc())
            .limit(limit)
            .all()
        )

    def get_by_isin(self, isin: str) -> Asset | None:
        return self.db.query(Asset).filter(Asset.isin == isin).first()

    def create(self, asset: Asset) -> Asset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def update(self, asset: Asset) -> Asset:
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        self.db.delete(asset)
        self.db.commit()
