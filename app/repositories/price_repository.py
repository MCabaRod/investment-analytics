from __future__ import annotations

import datetime as dt

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data_sources.base import PricePoint
from app.models.price_history import PriceHistory


class PriceHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_date(self, asset_id: int) -> dt.date | None:
        return self.db.query(func.max(PriceHistory.date)).filter(
            PriceHistory.asset_id == asset_id
        ).scalar()

    def get_range(self, asset_id: int, start: dt.date, end: dt.date) -> list[PriceHistory]:
        return (
            self.db.query(PriceHistory)
            .filter(
                PriceHistory.asset_id == asset_id,
                PriceHistory.date >= start,
                PriceHistory.date <= end,
            )
            .order_by(PriceHistory.date.asc())
            .all()
        )

    def get_last_retrieved_at(self, asset_id: int) -> dt.datetime | None:
        return self.db.query(func.max(PriceHistory.retrieved_at)).filter(
            PriceHistory.asset_id == asset_id
        ).scalar()

    def upsert_many(
        self, asset_id: int, points: list[PricePoint], source: str, retrieved_at: dt.datetime
    ) -> int:
        """Inserta o actualiza (asset_id, date). Devuelve el número de filas escritas."""
        written = 0
        for point in points:
            existing = (
                self.db.query(PriceHistory)
                .filter(PriceHistory.asset_id == asset_id, PriceHistory.date == point.date)
                .first()
            )
            if existing:
                existing.open = point.open
                existing.high = point.high
                existing.low = point.low
                existing.close = point.close
                existing.adjusted_close = point.adjusted_close
                existing.volume = point.volume
                existing.source = source
                existing.retrieved_at = retrieved_at
            else:
                self.db.add(
                    PriceHistory(
                        asset_id=asset_id,
                        date=point.date,
                        open=point.open,
                        high=point.high,
                        low=point.low,
                        close=point.close,
                        adjusted_close=point.adjusted_close,
                        volume=point.volume,
                        source=source,
                        retrieved_at=retrieved_at,
                    )
                )
            written += 1
        self.db.commit()
        return written
