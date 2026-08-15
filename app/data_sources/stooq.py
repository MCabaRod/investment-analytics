"""
Proveedor secundario: Stooq.

Expone un endpoint CSV estable y sin autenticación
(https://stooq.com/q/d/l/?s=SYMBOL&d1=YYYYMMDD&d2=YYYYMMDD&i=d) que llevamos
años viendo funcionar de forma consistente para EOD de acciones/ETFs. No
ofrece fundamentales: `get_fundamentals` devuelve siempre {} (nunca se
inventa un dato que la fuente no da).

Símbolos: Stooq añade sufijo de mercado (p.ej. "aapl.us" para NASDAQ/NYSE).
La resolución de símbolo por proveedor se hace en AssetIdentifier; si no hay
un símbolo específico registrado para "stooq", se usa `ticker.lower()+".us"`
como heurística razonable para el MVP (solo mercado US).
"""
import datetime as dt
import io
import logging
from decimal import Decimal

import httpx

from app.data_sources.base import DataProvider, PricePoint

logger = logging.getLogger(__name__)

STOOQ_URL = "https://stooq.com/q/d/l/"


class StooqProvider(DataProvider):
    name = "stooq"

    def get_price_history(self, symbol: str, start: dt.date, end: dt.date) -> list[PricePoint]:
        params = {
            "s": symbol,
            "d1": start.strftime("%Y%m%d"),
            "d2": end.strftime("%Y%m%d"),
            "i": "d",
        }
        try:
            response = httpx.get(STOOQ_URL, params=params, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Stooq request failed for %s: %s", symbol, exc)
            return []

        text = response.text.strip()
        if not text or text.startswith("No data") or "Date" not in text.splitlines()[0]:
            return []

        return list(self._parse_csv(text))

    @staticmethod
    def _parse_csv(text: str):
        import csv

        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            try:
                close = row.get("Close")
                if not close:
                    continue  # nunca inventamos un cierre ausente
                yield PricePoint(
                    date=dt.date.fromisoformat(row["Date"]),
                    open=_to_decimal(row.get("Open")),
                    high=_to_decimal(row.get("High")),
                    low=_to_decimal(row.get("Low")),
                    close=Decimal(close),
                    adjusted_close=None,  # Stooq no distingue ajustado en el CSV diario básico
                    volume=int(row["Volume"]) if row.get("Volume") else None,
                )
            except (KeyError, ValueError) as exc:
                logger.warning("Fila Stooq ignorada por error de parseo: %s (%s)", row, exc)
                continue

    def get_fundamentals(self, symbol: str) -> dict:
        return {}  # Stooq no ofrece fundamentales en el endpoint CSV público

    def is_available(self) -> bool:
        try:
            response = httpx.get(STOOQ_URL, params={"s": "aapl.us", "i": "d"}, timeout=5.0)
            return response.status_code == 200
        except httpx.HTTPError as exc:
            logger.warning("StooqProvider no disponible: %s", exc)
            return False


def _to_decimal(value: str | None) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except Exception:  # noqa: BLE001
        return None
