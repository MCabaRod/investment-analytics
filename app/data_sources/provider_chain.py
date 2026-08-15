"""
Orquesta la cadena de fallback entre proveedores (punto 4 del encargo):

    principal (Yahoo Finance) -> secundario (Stooq) -> ...

`services/` solo conoce `ProviderChain`, nunca un proveedor concreto. Añadir
un proveedor nuevo o reordenar prioridades no requiere tocar `services/`.
"""
from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from app.data_sources.base import DataProvider, PricePoint
from app.data_sources.stooq import StooqProvider
from app.data_sources.yahoo_finance import YahooFinanceProvider

logger = logging.getLogger(__name__)


@dataclass
class ChainResult:
    source: str
    points: list[PricePoint]


class ProviderChain:
    def __init__(self, providers: list[DataProvider]):
        if not providers:
            raise ValueError("La cadena de proveedores no puede estar vacía")
        self.providers = providers

    def get_price_history(self, symbol_by_provider: dict[str, str], start: dt.date, end: dt.date) -> ChainResult:
        """
        `symbol_by_provider` mapea nombre de proveedor -> símbolo a usar en ese
        proveedor (puede diferir de un proveedor a otro para el mismo activo).
        Se prueba cada proveedor en orden hasta obtener datos no vacíos.
        """
        for provider in self.providers:
            symbol = symbol_by_provider.get(provider.name)
            if not symbol:
                continue
            try:
                points = provider.get_price_history(symbol, start, end)
            except Exception as exc:  # noqa: BLE001 - un proveedor no debe tumbar la cadena
                logger.warning("Proveedor %s falló para %s: %s", provider.name, symbol, exc)
                continue
            if points:
                return ChainResult(source=provider.name, points=points)
        return ChainResult(source="none", points=[])

    def get_fundamentals(self, symbol_by_provider: dict[str, str]) -> tuple[str, dict]:
        for provider in self.providers:
            symbol = symbol_by_provider.get(provider.name)
            if not symbol:
                continue
            try:
                data = provider.get_fundamentals(symbol)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fundamentales: proveedor %s falló para %s: %s", provider.name, symbol, exc)
                continue
            if data:
                return provider.name, data
        return "none", {}


def build_default_provider_chain() -> ProviderChain:
    return ProviderChain([YahooFinanceProvider(), StooqProvider()])
