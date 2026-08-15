"""
Modelo central de activos.

Un `Asset` es cualquier instrumento analizable (acción, ETF o fondo). El
nombre nunca se usa como identificador: cada activo tiene un id interno y,
cuando existen, ISIN/ticker/exchange. `AssetIdentifier` resuelve el problema
de que un mismo instrumento tenga símbolos distintos según el proveedor
(punto 6 del encargo).

Fondos: el modelo ya soporta asset_type="fund", pero en esta fase no hay
proveedor de datos conectado para fondos (ver README / decisión de producto).
"""
import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AssetType(str, enum.Enum):
    stock = "stock"
    etf = "etf"
    fund = "fund"


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), index=True)

    isin: Mapped[str | None] = mapped_column(String(12), unique=True, index=True, nullable=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    featured_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    identifiers: Mapped[list["AssetIdentifier"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Asset id={self.id} name={self.name!r} type={self.asset_type}>"


class AssetIdentifier(Base):
    """Símbolo con el que un proveedor concreto identifica a este activo."""

    __tablename__ = "asset_identifiers"
    __table_args__ = (UniqueConstraint("asset_id", "provider", name="uq_asset_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(50))  # p.ej. "yahoo_finance", "stooq"
    provider_symbol: Mapped[str] = mapped_column(String(50))

    asset: Mapped["Asset"] = relationship(back_populates="identifiers")
