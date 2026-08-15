"""
Modelo de usuario.

En esta fase la aplicación no tiene login: se opera con un único usuario
`demo` sembrado en base de datos (ver app/core/demo_user.py). El modelo ya
incluye `hashed_password` para que activar autenticación real en el futuro
sea un cambio de servicio (JWT + hashing), no de esquema.
"""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
