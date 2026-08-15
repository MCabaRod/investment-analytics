import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PricePointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: dt.date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    adjusted_close: Decimal | None
    volume: int | None
    source: str


class AssetHistoryResponse(BaseModel):
    asset_id: int
    points: list[PricePointRead]
    last_updated: dt.datetime | None
    note: str | None = None
