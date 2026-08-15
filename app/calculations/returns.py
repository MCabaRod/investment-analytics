"""
Cálculos de rentabilidad sobre series de precios.

Fórmula base (punto 35 del encargo):

    Return = (P_final / P_inicial) - 1

Todas las funciones devuelven `None` cuando no hay histórico suficiente para
calcular el dato de forma fiable — nunca se aproxima ni se inventa un valor.
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

PricePoint = tuple[dt.date, Decimal]


def simple_return(start_price: Decimal, end_price: Decimal) -> Decimal | None:
    if start_price is None or end_price is None or start_price == 0:
        return None
    return (end_price / start_price) - 1


def _price_on_or_before(series: list[PricePoint], target_date: dt.date) -> PricePoint | None:
    """Última cotización disponible en target_date o antes. `series` debe estar ordenada ascendente."""
    candidate = None
    for point_date, price in series:
        if point_date <= target_date:
            candidate = (point_date, price)
        else:
            break
    return candidate


def period_return(series: list[PricePoint], years: float) -> Decimal | None:
    """
    Rentabilidad entre el último dato disponible y el dato de hace `years`
    años. Si no hay histórico suficiente para llegar a esa fecha, devuelve
    None (nunca aproxima con el dato más antiguo disponible como si fuera
    el de la fecha objetivo).
    """
    if len(series) < 2:
        return None

    latest_date, latest_price = series[-1]
    target_date = latest_date - dt.timedelta(days=round(years * 365.25))

    oldest_date = series[0][0]
    if target_date < oldest_date:
        return None  # no llegamos tan atrás: honesto devolver None, no aproximar

    baseline = _price_on_or_before(series, target_date)
    if baseline is None:
        return None
    return simple_return(baseline[1], latest_price)


def since_inception_return(series: list[PricePoint]) -> Decimal | None:
    if len(series) < 2:
        return None
    return simple_return(series[0][1], series[-1][1])


def normalize_to_100(series: list[PricePoint]) -> list[PricePoint]:
    """
    Rentabilidad normalizada = 100 en la fecha inicial (punto 18): permite
    comparar activos con precios nominales muy distintos en el mismo gráfico.
    """
    if not series:
        return []
    base_price = series[0][1]
    if base_price == 0:
        return []
    return [(d, (p / base_price) * 100) for d, p in series]
