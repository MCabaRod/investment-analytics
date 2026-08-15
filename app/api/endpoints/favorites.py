from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.demo_user import get_current_user
from app.models.user import User
from app.schemas.favorite import FavoriteCreate, FavoriteRead
from app.services.favorite_service import FavoriteService

router = APIRouter()


@router.get("", response_model=list[FavoriteRead])
def list_favorites(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return FavoriteService(db).list_for_user(user.id)


@router.post("", response_model=FavoriteRead, status_code=201)
def add_favorite(
    payload: FavoriteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return FavoriteService(db).add(user.id, payload.asset_id)


@router.delete("/{asset_id}", status_code=204)
def remove_favorite(
    asset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    FavoriteService(db).remove(user.id, asset_id)
