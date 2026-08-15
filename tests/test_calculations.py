import datetime as dt
from decimal import Decimal

import pytest

from app.calculations.returns import (
    normalize_to_100,
    period_return,
    simple_return,
    since_inception_return,
)
from app.calculations.risk import (
    annualized_volatility,
    beta,
    daily_returns,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
)
from app.calculations.ytd import ytd_return


def test_simple_return_basic():
    assert simple_return(Decimal("100"), Decimal("110")) == Decimal("0.10")


def test_simple_return_zero_start_is_none():
    assert simple_return(Decimal("0"), Decimal("110")) is None


def test_since_inception_return():
    series = [(dt.date(2020, 1, 1), Decimal("50")), (dt.date(2026, 1, 1), Decimal("100"))]
    assert since_inception_return(series) == Decimal("1.0")


def test_period_return_insufficient_history_returns_none():
    series = [(dt.date(2026, 1, 1), Decimal("100")), (dt.date(2026, 6, 1), Decimal("110"))]
    assert period_return(series, years=5) is None  # no hay 5 años de histórico


def test_period_return_finds_closest_prior_date():
    series = [
        (dt.date(2025, 8, 10), Decimal("100")),  # ~1 año antes
        (dt.date(2025, 8, 15), Decimal("105")),
        (dt.date(2026, 8, 14), Decimal("120")),
    ]
    result = period_return(series, years=1)
    assert float(result) == pytest.approx(0.20, rel=0.01)


def test_ytd_uses_last_close_of_previous_year_not_one_year_ago():
    series = [
        (dt.date(2025, 12, 30), Decimal("100")),  # último cierre del año anterior
        (dt.date(2025, 6, 1), Decimal("50")),  # más antiguo, no debe usarse como baseline YTD
        (dt.date(2026, 8, 14), Decimal("130")),
    ]
    series.sort(key=lambda p: p[0])
    result = ytd_return(series)
    assert result == Decimal("0.30")  # (130/100) - 1, NO (130/50)-1


def test_ytd_without_prior_year_data_is_none():
    series = [(dt.date(2026, 1, 5), Decimal("100")), (dt.date(2026, 8, 14), Decimal("110"))]
    assert ytd_return(series) is None


def test_normalize_to_100():
    series = [(dt.date(2026, 1, 1), Decimal("50")), (dt.date(2026, 6, 1), Decimal("75"))]
    normalized = normalize_to_100(series)
    assert normalized[0][1] == Decimal("100")
    assert normalized[1][1] == Decimal("150")


def test_max_drawdown_detects_worst_peak_to_valley():
    series = [
        (dt.date(2026, 1, 1), Decimal("100")),
        (dt.date(2026, 1, 2), Decimal("120")),  # pico
        (dt.date(2026, 1, 3), Decimal("60")),  # valle: caída de -50% desde el pico
        (dt.date(2026, 1, 4), Decimal("90")),
    ]
    dd = max_drawdown(series)
    assert dd == pytest.approx(-0.5)


def test_annualized_volatility_needs_at_least_two_returns():
    assert annualized_volatility([]) is None
    assert annualized_volatility([0.01]) is None
    vol = annualized_volatility([0.01, -0.01, 0.02, -0.02])
    assert vol is not None and vol > 0


def test_sharpe_ratio_uses_configured_risk_free_rate():
    result = sharpe_ratio(annualized_return=0.15, volatility=0.10, risk_free_rate=0.02)
    assert result == pytest.approx((0.15 - 0.02) / 0.10)


def test_sharpe_ratio_none_without_volatility():
    assert sharpe_ratio(0.10, None, 0.02) is None
    assert sharpe_ratio(None, 0.10, 0.02) is None


def test_sortino_ratio_requires_negative_returns():
    only_positive = [0.01, 0.02, 0.015]
    assert sortino_ratio(only_positive, risk_free_rate=0.02) is None

    mixed = [0.02, -0.01, 0.015, -0.02, 0.01, -0.015]
    result = sortino_ratio(mixed, risk_free_rate=0.02)
    assert result is not None


def test_beta_perfect_correlation_equals_one():
    asset_returns = [0.01, 0.02, -0.01, 0.03]
    benchmark_returns = [0.01, 0.02, -0.01, 0.03]
    assert beta(asset_returns, benchmark_returns) == pytest.approx(1.0)


def test_beta_needs_at_least_two_observations():
    assert beta([0.01], [0.01]) is None
