import datetime as dt

from pydantic import BaseModel, Field


class AssetMetricsResponse(BaseModel):
    asset_id: int
    as_of: dt.date = Field(description="Fecha del último dato de precio usado en los cálculos.")
    data_points: int = Field(description="Número de cotizaciones diarias usadas.")

    ytd_return: float | None = Field(
        default=None,
        description="Rentabilidad desde el último cierre del año natural anterior hasta hoy. "
        "NO es lo mismo que la rentabilidad a 1 año.",
    )
    return_1y: float | None = Field(default=None, description="Rentabilidad en los últimos 365 días.")
    return_3y: float | None = Field(default=None, description="Rentabilidad en los últimos 3 años.")
    return_5y: float | None = Field(default=None, description="Rentabilidad en los últimos 5 años.")
    return_since_inception: float | None = Field(
        default=None, description="Rentabilidad desde el primer dato almacenado del activo."
    )

    volatility_annualized: float | None = Field(
        default=None, description="Desviación típica de los retornos diarios, anualizada."
    )
    max_drawdown: float | None = Field(
        default=None, description="Máxima caída desde un pico histórico (valor negativo o cero)."
    )
    sharpe_ratio: float | None = Field(
        default=None,
        description="(Rentabilidad 1 año - tasa libre de riesgo) / volatilidad anualizada.",
    )
    sortino_ratio: float | None = Field(
        default=None, description="Como Sharpe, pero solo penaliza la volatilidad de retornos negativos."
    )
    risk_free_rate_used: float = Field(description="Tasa libre de riesgo aplicada (configurable).")

    note: str | None = None
