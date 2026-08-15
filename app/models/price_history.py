"""
Histórico de precios diarios. Un único registro "canónico" por (asset, date):
el proveedor que lo entregó se guarda en `source` para trazabilidad, pero no
se duplican filas por proveedor — la cadena de fallback en data_sources/
resuelve ya cuál es el dato válido para esa fecha antes de llegar aquí.
"""
import datetime as dt
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriceHistory(Base):
    __tablename__ = "asset_prices"
    __table_args__ = (UniqueConstraint("asset_id", "date", name="uq_asset_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    adjusted_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source: Mapped[str] = mapped_column(String(50))
    retrieved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
