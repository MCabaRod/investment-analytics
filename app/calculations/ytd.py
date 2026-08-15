"""
YTD (Year To Date) — módulo separado a propósito.

El encargo es explícito en no confundir YTD con la rentabilidad a 1 año:
YTD se calcula desde el último cierre disponible del año natural ANTERIOR
hasta el dato más reciente, no "hace 365 días".
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from app.calculations.returns import simple_return

PricePoint = tuple[dt.date, Decimal]


def ytd_return(series: list[PricePoint]) -> Decimal | None:
    """
    `series` debe estar ordenada ascendente por fecha.
    Devuelve None si no hay ningún dato del año natural anterior (o previo)
    disponible como referencia — nunca se aproxima con el primer dato del
    año en curso.
    """
    if not series:
        return None

    latest_date, latest_price = series[-1]
    year_start = dt.date(latest_date.year, 1, 1)

    baseline = None
    for point_date, price in series:
        if point_date < year_start:
            baseline = (point_date, price)
        else:
            break

    if baseline is None:
        return None
    return simple_return(baseline[1], latest_price)
