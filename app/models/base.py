"""
Base declarativa común para todos los modelos ORM.

Los modelos concretos (Asset, User, PriceHistory, ...) se añadirán en la
Fase 2 y siguientes, heredando de `Base` y, opcionalmente, de `TimestampMixin`.
"""
import datetime as dt

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin que añade `created_at` / `updated_at` a cualquier modelo."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
    )
