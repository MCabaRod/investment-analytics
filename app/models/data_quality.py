"""
Registro de fuentes (para el futuro panel de administración, punto 31) y log
de incidencias de calidad (punto 23): nunca se oculta un problema en
silencio, se deja constancia consultable.
"""
import datetime as dt
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)  # "yahoo_finance", "stooq", ...
    priority: Mapped[int] = mapped_column(Integer)  # 1 = principal, 2 = secundaria, ...
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataQualityIssueType(str, enum.Enum):
    null_value = "null_value"
    negative_price = "negative_price"
    absurd_change = "absurd_change"
    duplicate_date = "duplicate_date"
    stale_data = "stale_data"
    source_mismatch = "source_mismatch"
    provider_unavailable = "provider_unavailable"


class DataQualityLog(Base):
    __tablename__ = "data_quality_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(String(50))
    issue_type: Mapped[DataQualityIssueType] = mapped_column(Enum(DataQualityIssueType))
    detail: Mapped[str] = mapped_column(Text)
    detected_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
