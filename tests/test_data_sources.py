import datetime as dt

import pandas as pd
import pytest

from app.data_sources.provider_chain import ProviderChain
from app.data_sources.stooq import StooqProvider
from app.data_sources.yahoo_finance import YahooFinanceProvider


class _FakeTicker:
    """Doble de yfinance.Ticker para no depender de red real."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.info = {"trailingPE": 32.5, "marketCap": 3_000_000_000_000}

    def history(self, start, end, auto_adjust=False, actions=False):
        index = pd.to_datetime(["2026-08-10", "2026-08-11"])
        return pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [102.0, 103.0],
                "Low": [99.0, 100.0],
                "Close": [101.0, 102.5],
                "Adj Close": [101.0, 102.5],
                "Volume": [1_000_000, 1_100_000],
            },
            index=index,
        )


def test_yahoo_finance_provider_parses_history(monkeypatch):
    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)

    provider = YahooFinanceProvider()
    points = provider.get_price_history("MSFT", dt.date(2026, 8, 10), dt.date(2026, 8, 11))

    assert len(points) == 2
    assert points[0].close == pytest.approx(101.0)
    assert points[0].date == dt.date(2026, 8, 10)


def test_yahoo_finance_provider_fundamentals_omits_missing_fields(monkeypatch):
    import yfinance

    monkeypatch.setattr(yfinance, "Ticker", _FakeTicker)

    provider = YahooFinanceProvider()
    fundamentals = provider.get_fundamentals("MSFT")

    assert fundamentals["pe_ratio"] == 32.5
    assert "peg_ratio" not in fundamentals  # no estaba en el fake info -> nunca se inventa


class _FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        pass


def test_stooq_provider_parses_csv(monkeypatch):
    csv_body = (
        "Date,Open,High,Low,Close,Volume\n"
        "2026-08-10,100.0,102.0,99.0,101.0,1000000\n"
        "2026-08-11,101.0,103.0,100.0,102.5,1100000\n"
    )

    def fake_get(url, params=None, timeout=None):
        return _FakeResponse(csv_body)

    monkeypatch.setattr("app.data_sources.stooq.httpx.get", fake_get)

    provider = StooqProvider()
    points = provider.get_price_history("msft.us", dt.date(2026, 8, 10), dt.date(2026, 8, 11))

    assert len(points) == 2
    assert points[1].close == pytest.approx(102.5)
    assert provider.get_fundamentals("msft.us") == {}  # nunca inventa fundamentales


def test_provider_chain_falls_back_to_secondary(monkeypatch):
    class EmptyProvider:
        name = "yahoo_finance"

        def get_price_history(self, symbol, start, end):
            return []

    class WorkingProvider:
        name = "stooq"

        def get_price_history(self, symbol, start, end):
            from app.data_sources.base import PricePoint
            from decimal import Decimal

            return [
                PricePoint(
                    date=dt.date(2026, 8, 10),
                    open=Decimal("1"),
                    high=Decimal("1"),
                    low=Decimal("1"),
                    close=Decimal("1"),
                    adjusted_close=None,
                    volume=None,
                )
            ]

    chain = ProviderChain([EmptyProvider(), WorkingProvider()])
    result = chain.get_price_history(
        {"yahoo_finance": "MSFT", "stooq": "msft.us"}, dt.date(2026, 8, 10), dt.date(2026, 8, 10)
    )

    assert result.source == "stooq"
    assert len(result.points) == 1
