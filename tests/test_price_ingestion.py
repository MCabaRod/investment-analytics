import datetime as dt
from decimal import Decimal

from app.data_sources.base import PricePoint
from app.data_sources.provider_chain import ChainResult
from app.models.asset import Asset, AssetType
from app.repositories.data_quality_repository import DataQualityLogRepository
from app.services.price_ingestion_service import PriceIngestionService


class _StubChain:
    def __init__(self, points: list[PricePoint], source: str = "yahoo_finance"):
        self._points = points
        self._source = source

    def get_price_history(self, symbols, start, end):
        return ChainResult(source=self._source, points=self._points)


def _make_asset(db_session) -> Asset:
    asset = Asset(name="Microsoft Corporation", asset_type=AssetType.stock, ticker="MSFT", currency="USD")
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_ingestion_writes_new_points_and_is_incremental(db_session):
    asset = _make_asset(db_session)
    points = [
        PricePoint(dt.date(2026, 8, 10), Decimal("100"), Decimal("102"), Decimal("99"), Decimal("101"), Decimal("101"), 1000),
        PricePoint(dt.date(2026, 8, 11), Decimal("101"), Decimal("103"), Decimal("100"), Decimal("102"), Decimal("102"), 1100),
    ]
    service = PriceIngestionService(db_session, provider_chain=_StubChain(points))

    result = service.update_asset(asset)
    assert result.status == "updated"
    assert result.points_written == 2

    # Segunda pasada sin nuevos puntos remotos -> no debería pedir nada porque
    # ya tiene datos hasta "hoy" solo si hoy <= última fecha; simulamos que el
    # proveedor ahora solo tiene el mismo rango ya almacenado.
    service_2 = PriceIngestionService(db_session, provider_chain=_StubChain([]))
    result_2 = service_2.update_asset(asset)
    # Como "hoy" es posterior a 2026-08-11 en un entorno real, y no hay datos
    # nuevos del proveedor, debe reportarse no_data (nunca inventa un punto).
    assert result_2.status in {"no_data", "up_to_date"}


def test_ingestion_discards_negative_price_and_logs_quality_issue(db_session):
    asset = _make_asset(db_session)
    points = [
        PricePoint(dt.date(2026, 8, 10), Decimal("100"), Decimal("102"), Decimal("99"), Decimal("-5"), Decimal("-5"), 1000),
        PricePoint(dt.date(2026, 8, 11), Decimal("101"), Decimal("103"), Decimal("100"), Decimal("102"), Decimal("102"), 1100),
    ]
    service = PriceIngestionService(db_session, provider_chain=_StubChain(points))

    result = service.update_asset(asset)
    assert result.points_written == 1  # el precio negativo se descarta

    logs = DataQualityLogRepository(db_session).list_unresolved(asset.id)
    assert any(log.issue_type.value == "negative_price" for log in logs)


def test_ingestion_deduplicates_repeated_dates(db_session):
    asset = _make_asset(db_session)
    points = [
        PricePoint(dt.date(2026, 8, 10), Decimal("100"), Decimal("102"), Decimal("99"), Decimal("101"), Decimal("101"), 1000),
        PricePoint(dt.date(2026, 8, 10), Decimal("100"), Decimal("102"), Decimal("99"), Decimal("999"), Decimal("999"), 1000),
    ]
    service = PriceIngestionService(db_session, provider_chain=_StubChain(points))

    result = service.update_asset(asset)
    assert result.points_written == 1

    logs = DataQualityLogRepository(db_session).list_unresolved(asset.id)
    assert any(log.issue_type.value == "duplicate_date" for log in logs)


def test_ingestion_flags_absurd_change_but_keeps_the_point(db_session):
    asset = _make_asset(db_session)
    points = [
        PricePoint(dt.date(2026, 8, 10), Decimal("100"), Decimal("102"), Decimal("99"), Decimal("100"), Decimal("100"), 1000),
        PricePoint(dt.date(2026, 8, 11), Decimal("100"), Decimal("500"), Decimal("100"), Decimal("400"), Decimal("400"), 1000),
    ]
    service = PriceIngestionService(db_session, provider_chain=_StubChain(points))

    result = service.update_asset(asset)
    assert result.points_written == 2  # se conserva, no se inventa ni se descarta

    logs = DataQualityLogRepository(db_session).list_unresolved(asset.id)
    assert any(log.issue_type.value == "absurd_change" for log in logs)
