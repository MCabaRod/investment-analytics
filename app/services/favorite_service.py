from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.repositories.asset_repository import AssetRepository
from app.repositories.favorite_repository import FavoriteRepository


class FavoriteService:
    def __init__(self, db: Session):
        self.favorites = FavoriteRepository(db)
        self.assets = AssetRepository(db)

    def list_for_user(self, user_id: int) -> list[Favorite]:
        return self.favorites.list_for_user(user_id)

    def add(self, user_id: int, asset_id: int) -> Favorite:
        if self.assets.get(asset_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activo no encontrado")
        existing = self.favorites.get(user_id, asset_id)
        if existing is not None:
            return existing
        return self.favorites.add(user_id, asset_id)

    def remove(self, user_id: int, asset_id: int) -> None:
        favorite = self.favorites.get(user_id, asset_id)
        if favorite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorito no encontrado")
        self.favorites.remove(favorite)
