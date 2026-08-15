"""
Orquesta los cálculos de app/calculations/ sobre el histórico almacenado de
un activo. No accede nunca a proveedores externos: solo lee de base de
datos (punto 24 del encargo).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.calculations.returns import period_return, since_inception_return
from app.calculations.risk import (
    annualized_volatility,
    daily_returns,
    max_drawdown,
    sharpe_ratio,
    sortino_ratio,
)
from app.calculations.ytd import ytd_return
from app.core.config import get_settings
from app.repositories.price_repository import PriceHistoryRepository
from app.schemas.metrics import AssetMetricsResponse


class MetricsService:
    def __init__(self, db: Session):
        self.db = db
        self.prices = PriceHistoryRepository(db)
        self.settings = get_settings()

    def compute(self, asset_id: int) -> AssetMetricsResponse:
        rows = self.prices.get_range(asset_id, dt.date(1900, 1, 1), dt.date.today())
        risk_free = self.settings.risk_free_rate

        if not rows:
            return AssetMetricsResponse(
                asset_id=asset_id,
                as_of=dt.date.today(),
                data_points=0,
                risk_free_rate_used=risk_free,
                note="Sin histórico almacenado. Ejecuta POST /refresh o espera a la actualización diaria.",
            )

        series = [(r.date, r.close) for r in rows]
        latest_date = series[-1][0]

        r1y = period_return(series, 1)
        r3y = period_return(series, 3)
        r5y = period_return(series, 5)
        ytd = ytd_return(series)
        inception = since_inception_return(series)

        returns = daily_returns(series)
        volatility = annualized_volatility(returns)
        drawdown = max_drawdown(series)
        # Sharpe/Sortino usan la rentabilidad a 1 año como proxy de rentabilidad
        # anualizada; si no hay un año completo de histórico, ambos son N/D.
        sharpe = sharpe_ratio(float(r1y) if r1y is not None else None, volatility, risk_free)
        sortino = sortino_ratio(returns, risk_free) if returns else None

        note = None
        if len(series) < 30:
            note = "Histórico muy corto: las métricas de riesgo pueden no ser representativas."

        return AssetMetricsResponse(
            asset_id=asset_id,
            as_of=latest_date,
            data_points=len(series),
            ytd_return=float(ytd) if ytd is not None else None,
            return_1y=float(r1y) if r1y is not None else None,
            return_3y=float(r3y) if r3y is not None else None,
            return_5y=float(r5y) if r5y is not None else None,
            return_since_inception=float(inception) if inception is not None else None,
            volatility_annualized=volatility,
            max_drawdown=drawdown,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            risk_free_rate_used=risk_free,
            note=note,
        )
