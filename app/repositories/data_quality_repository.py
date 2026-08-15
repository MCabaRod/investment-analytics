from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.models.data_quality import DataQualityIssueType, DataQualityLog


class DataQualityLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self, asset_id: int | None, source: str, issue_type: DataQualityIssueType, detail: str
    ) -> DataQualityLog:
        entry = DataQualityLog(
            asset_id=asset_id,
            source=source,
            issue_type=issue_type,
            detail=detail,
            detected_at=dt.datetime.now(dt.timezone.utc),
            resolved=False,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_unresolved(self, asset_id: int | None = None) -> list[DataQualityLog]:
        query = self.db.query(DataQualityLog).filter(DataQualityLog.resolved.is_(False))
        if asset_id is not None:
            query = query.filter(DataQualityLog.asset_id == asset_id)
        return query.order_by(DataQualityLog.detected_at.desc()).all()
