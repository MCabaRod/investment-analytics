"""
Placeholder de autenticación.

MVP sin login: toda petición opera como un único usuario `demo`, creado de
forma perezosa si no existe. Cuando se implemente autenticación real, solo
hay que sustituir `get_current_user` por la validación de JWT — nada más del
código (services, repos, endpoints) depende de cómo se resuelve el usuario.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

DEMO_USER_EMAIL = "demo@local"


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
    if user is None:
        user = User(email=DEMO_USER_EMAIL, hashed_password=None, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
