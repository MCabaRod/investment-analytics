"""
Orquesta la actualización incremental de histórico (punto 21) y la
validación de calidad (punto 23): nunca se guarda un dato silenciosamente
problemático sin dejar constancia en data_quality_logs.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.data_sources.base import PricePoint
from app.data_sources.provider_chain import ProviderChain, build_default_provider_chain
from app.models.asset import Asset
from app.models.data_quality import DataQualityIssueType
from app.repositories.data_quality_repository import DataQualityLogRepository
from app.repositories.price_repository import PriceHistoryRepository

# Umbral para marcar una variación diaria como "absurda" y enviarla a revisión
# en lugar de descartarla silenciosamente. Configurable si hace falta afinar.
MAX_PLAUSIBLE_DAILY_CHANGE = 0.5  # 50%

# Fecha mínima por defecto para la primera carga de un activo sin histórico.
DEFAULT_HISTORY_START = dt.date(2000, 1, 1)


@dataclass
class IngestionResult:
    asset_id: int
    status: str  # "up_to_date" | "updated" | "no_data"
    source: str | None
    points_written: int


class PriceIngestionService:
    def __init__(self, db: Session, provider_chain: ProviderChain | None = None):
        self.db = db
        self.prices = PriceHistoryRepository(db)
        self.quality = DataQualityLogRepository(db)
        self.provider_chain = provider_chain or build_default_provider_chain()

    def update_asset(self, asset: Asset) -> IngestionResult:
        symbols = self._resolve_symbols(asset)
        if not symbols:
            self.quality.log(
                asset.id,
                source="ingestion",
                issue_type=DataQualityIssueType.provider_unavailable,
                detail="El activo no tiene ticker ni símbolo de proveedor configurado.",
            )
            return IngestionResult(asset.id, "no_data", None, 0)

        last_date = self.prices.get_latest_date(asset.id)
        start = last_date + dt.timedelta(days=1) if last_date else DEFAULT_HISTORY_START
        end = dt.date.today()

        if start > end:
            return IngestionResult(asset.id, "up_to_date", None, 0)

        result = self.provider_chain.get_price_history(symbols, start, end)
        if not result.points:
            self.quality.log(
                asset.id,
                source="provider_chain",
                issue_type=DataQualityIssueType.provider_unavailable,
                detail=f"Ningún proveedor devolvió datos para el rango {start}–{end}.",
            )
            return IngestionResult(asset.id, "no_data", None, 0)

        clean_points = self._validate(asset, result.source, result.points, previous_close=self._last_close(asset.id))
        if not clean_points:
            return IngestionResult(asset.id, "no_data", result.source, 0)

        written = self.prices.upsert_many(
            asset.id, clean_points, source=result.source, retrieved_at=dt.datetime.now(dt.timezone.utc)
        )
        return IngestionResult(asset.id, "updated", result.source, written)

    def _resolve_symbols(self, asset: Asset) -> dict[str, str]:
        """
        Mapea proveedor -> símbolo. Usa AssetIdentifier si existe una entrada
        específica; si no, cae al ticker (heurística razonable para el MVP,
        solo cubre bien activos de mercados US con ticker "plano").
        """
        symbols: dict[str, str] = {}
        by_provider = {i.provider: i.provider_symbol for i in asset.identifiers}
        if "yahoo_finance" in by_provider:
            symbols["yahoo_finance"] = by_provider["yahoo_finance"]
        elif asset.ticker:
            symbols["yahoo_finance"] = asset.ticker

        if "stooq" in by_provider:
            symbols["stooq"] = by_provider["stooq"]
        elif asset.ticker:
            symbols["stooq"] = f"{asset.ticker.lower()}.us"

        return symbols

    def _last_close(self, asset_id: int) -> Decimal | None:
        last_date = self.prices.get_latest_date(asset_id)
        if last_date is None:
            return None
        rows = self.prices.get_range(asset_id, last_date, last_date)
        return rows[0].close if rows else None

    def _validate(
        self,
        asset: Asset,
        source: str,
        points: list[PricePoint],
        previous_close: Decimal | None,
    ) -> list[PricePoint]:
        """
        Filtra/marca puntos problemáticos. Los duplicados de fecha se
        deduplican (se queda el último); los precios nulos o negativos se
        descartan y se registran; los saltos anómalos NO se descartan (podría
        ser real, p.ej. un split), pero se registran para revisión manual.
        """
        seen_dates: set[dt.date] = set()
        clean: list[PricePoint] = []
        last_close = previous_close

        for point in sorted(points, key=lambda p: p.date):
            if point.date in seen_dates:
                self.quality.log(
                    asset.id, source, DataQualityIssueType.duplicate_date,
                    f"Fecha duplicada en la respuesta del proveedor: {point.date}",
                )
                continue
            seen_dates.add(point.date)

            if point.close is None:
                self.quality.log(
                    asset.id, source, DataQualityIssueType.null_value,
                    f"Cierre nulo para {point.date}, descartado.",
                )
                continue

            if point.close < 0:
                self.quality.log(
                    asset.id, source, DataQualityIssueType.negative_price,
                    f"Precio negativo ({point.close}) para {point.date}, descartado.",
                )
                continue

            if last_close and last_close > 0:
                change = abs(float(point.close - last_close) / float(last_close))
                if change > MAX_PLAUSIBLE_DAILY_CHANGE:
                    self.quality.log(
                        asset.id, source, DataQualityIssueType.absurd_change,
                        f"Variación de {change:.0%} entre {last_close} y {point.close} en {point.date}. "
                        "Dato conservado pero marcado para revisión (puede ser un split real).",
                    )

            last_close = point.close
            clean.append(point)

        return clean
