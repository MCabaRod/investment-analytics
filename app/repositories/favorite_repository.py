from sqlalchemy.orm import Session, joinedload

from app.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: int) -> list[Favorite]:
        return (
            self.db.query(Favorite)
            .options(joinedload(Favorite.asset))
            .filter(Favorite.user_id == user_id)
            .all()
        )

    def get(self, user_id: int, asset_id: int) -> Favorite | None:
        return (
            self.db.query(Favorite)
            .filter(Favorite.user_id == user_id, Favorite.asset_id == asset_id)
            .first()
        )

    def add(self, user_id: int, asset_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, asset_id=asset_id)
        self.db.add(favorite)
        self.db.commit()
        self.db.refresh(favorite)
        return favorite

    def remove(self, favorite: Favorite) -> None:
        self.db.delete(favorite)
        self.db.commit()
