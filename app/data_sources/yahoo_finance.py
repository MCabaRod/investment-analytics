"""
Proveedor principal: yfinance (biblioteca no oficial sobre los endpoints
públicos de Yahoo Finance).

Fiabilidad conocida y documentada: no hay API oficial de Yahoo desde 2017;
yfinance funciona bien en la práctica pero puede romperse sin aviso si Yahoo
cambia su backend, y puede devolver HTTP 429 bajo uso intensivo. Por eso está
detrás de la interfaz `DataProvider` y existe `StooqProvider` como fallback
(ver app/data_sources/provider_chain.py).
"""
import datetime as dt
import logging
from decimal import Decimal

from app.data_sources.base import DataProvider, PricePoint

logger = logging.getLogger(__name__)

# Campos de `Ticker.info` que sí vamos a exponer como fundamentales.
# Si un campo no está presente en la respuesta, se omite (nunca se inventa).
_FUNDAMENTAL_FIELDS = {
    "trailingPE": "pe_ratio",
    "forwardPE": "forward_pe",
    "pegRatio": "peg_ratio",
    "priceToBook": "price_to_book",
    "enterpriseToEbitda": "ev_ebitda",
    "dividendYield": "dividend_yield",
    "marketCap": "market_cap",
    "trailingEps": "eps",
    "revenueGrowth": "revenue_growth",
    "earningsGrowth": "earnings_growth",
    "returnOnEquity": "roe",
    "debtToEquity": "debt_to_equity",
}


class YahooFinanceProvider(DataProvider):
    name = "yahoo_finance"

    def get_price_history(self, symbol: str, start: dt.date, end: dt.date) -> list[PricePoint]:
        import yfinance as yf  # import perezoso: evita coste de import si no se usa

        ticker = yf.Ticker(symbol)
        # end es exclusivo en yfinance -> sumamos un día para incluirlo
        df = ticker.history(
            start=start.isoformat(),
            end=(end + dt.timedelta(days=1)).isoformat(),
            auto_adjust=False,
            actions=False,
        )
        if df is None or df.empty:
            return []

        points: list[PricePoint] = []
        for idx, row in df.iterrows():
            close = row.get("Close")
            if close is None or (isinstance(close, float) and close != close):  # NaN check
                continue  # nunca inventamos un cierre; si falta, se omite el punto
            points.append(
                PricePoint(
                    date=idx.date() if hasattr(idx, "date") else idx,
                    open=_to_decimal(row.get("Open")),
                    high=_to_decimal(row.get("High")),
                    low=_to_decimal(row.get("Low")),
                    close=Decimal(str(close)),
                    adjusted_close=_to_decimal(row.get("Adj Close")),
                    volume=int(row["Volume"]) if row.get("Volume") == row.get("Volume") else None,
                )
            )
        return points

    def get_fundamentals(self, symbol: str) -> dict:
        import yfinance as yf

        info = yf.Ticker(symbol).info or {}
        result = {}
        for source_key, target_key in _FUNDAMENTAL_FIELDS.items():
            value = info.get(source_key)
            if value is not None:
                result[target_key] = value
        return result

    def is_available(self) -> bool:
        try:
            import yfinance  # noqa: F401

            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("YahooFinanceProvider no disponible: %s", exc)
            return False


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        if value != value:  # NaN
            return None
        return Decimal(str(value))
    except (TypeError, ValueError):
        return None
