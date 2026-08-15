"""
Métricas de riesgo (punto 13 del encargo).

Fórmulas documentadas explícitamente:

    volatilidad_anualizada = std(retornos_diarios) * sqrt(periodos_por_año)
    Sharpe = (Return_anualizado - RiskFreeRate) / Volatilidad
    Sortino = igual que Sharpe pero solo con la desviación de retornos negativos
    Max Drawdown = caída máxima desde cualquier máximo acumulado histórico

La tasa libre de riesgo NUNCA se asume arbitrariamente: se recibe siempre
como parámetro, tomado de `settings.risk_free_rate` (documentado y
configurable, ver app/core/config.py).
"""
from __future__ import annotations

import datetime as dt
import math
import statistics
from decimal import Decimal

TRADING_DAYS_PER_YEAR = 252
PricePoint = tuple[dt.date, Decimal]


def daily_returns(series: list[PricePoint]) -> list[float]:
    """Retornos porcentuales día a día. Requiere al menos 2 puntos."""
    returns: list[float] = []
    for i in range(1, len(series)):
        prev = float(series[i - 1][1])
        curr = float(series[i][1])
        if prev != 0:
            returns.append(curr / prev - 1)
    return returns


def annualized_volatility(
    returns: list[float], periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float | None:
    if len(returns) < 2:
        return None
    return statistics.stdev(returns) * math.sqrt(periods_per_year)


def max_drawdown(series: list[PricePoint]) -> float | None:
    """
    Máxima caída porcentual desde cualquier pico histórico hasta el valle
    posterior. Devuelve un número negativo o cero (p.ej. -0.35 = -35%).
    """
    if not series:
        return None
    peak = float(series[0][1])
    worst = 0.0
    for _, price in series:
        price_f = float(price)
        if price_f > peak:
            peak = price_f
        if peak > 0:
            drawdown = (price_f - peak) / peak
            worst = min(worst, drawdown)
    return worst


def sharpe_ratio(
    annualized_return: float | None, volatility: float | None, risk_free_rate: float
) -> float | None:
    if annualized_return is None or not volatility:
        return None
    return (annualized_return - risk_free_rate) / volatility


def sortino_ratio(
    returns: list[float],
    risk_free_rate: float,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float | None:
    """
    Igual que Sharpe pero solo penaliza la volatilidad "mala" (retornos
    negativos). Requiere al menos 2 retornos negativos para que la
    desviación típica de la downside tenga sentido estadístico.
    """
    downside = [r for r in returns if r < 0]
    if len(downside) < 2 or not returns:
        return None
    downside_std = statistics.stdev(downside) * math.sqrt(periods_per_year)
    if downside_std == 0:
        return None
    annualized_mean_return = statistics.mean(returns) * periods_per_year
    return (annualized_mean_return - risk_free_rate) / downside_std


def beta(asset_returns: list[float], benchmark_returns: list[float]) -> float | None:
    """
    Beta respecto a un benchmark. Ambas listas deben estar alineadas por
    fecha (mismo número de observaciones, mismo orden) antes de llamar aquí
    — esa alineación es responsabilidad de quien construya las series
    (services/), no de esta función.
    """
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 2:
        return None
    a = asset_returns[:n]
    b = benchmark_returns[:n]
    mean_a = statistics.mean(a)
    mean_b = statistics.mean(b)
    covariance = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / n
    variance_b = sum((x - mean_b) ** 2 for x in b) / n
    if variance_b == 0:
        return None
    return covariance / variance_b
