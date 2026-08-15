"""Esquemas de entrada/salida para el recurso Asset."""
from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import AssetType


class AssetBase(BaseModel):
    name: str = Field(..., max_length=255)
    asset_type: AssetType
    isin: str | None = Field(default=None, max_length=12)
    ticker: str | None = Field(default=None, max_length=20)
    exchange: str | None = Field(default=None, max_length=50)
    currency: str | None = Field(default=None, max_length=3)


class AssetCreate(AssetBase):
    is_featured: bool = False
    featured_order: int | None = None


class AssetUpdate(BaseModel):
    """Todos los campos opcionales: solo se actualiza lo que se envía."""

    name: str | None = None
    isin: str | None = None
    ticker: str | None = None
    exchange: str | None = None
    currency: str | None = None
    is_featured: bool | None = None
    featured_order: int | None = None
    is_active: bool | None = None


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_featured: bool
    featured_order: int | None
    is_active: bool


class AssetSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    asset_type: AssetType
    isin: str | None
    ticker: str | None
    exchange: str | None
