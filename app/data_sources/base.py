"""
Interfaz común que debe implementar cualquier proveedor de datos.

El resto de la aplicación (services, tasks) depende únicamente de esta
interfaz, nunca de una librería o API concreta. Esto permite cambiar de
proveedor, añadir uno nuevo, o definir una cadena de fallback

    principal -> secundario -> alternativo

sin tocar el resto del código. Se implementará en la Fase 3.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class PricePoint:
    date: date
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    adjusted_close: Decimal | None
    volume: int | None


@dataclass(frozen=True)
class ProviderResult:
    """Envoltorio de cualquier respuesta de un proveedor, con su trazabilidad."""

    source: str
    retrieved_at: str  # ISO 8601
    data: object


class DataProvider(ABC):
    """Contrato que deben cumplir YahooFinanceProvider, StooqProvider, etc."""

    name: str

    @abstractmethod
    def get_price_history(self, symbol: str, start: date, end: date) -> list[PricePoint]:
        """Devuelve el histórico de precios diarios para un símbolo en un rango."""
        raise NotImplementedError

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> dict:
        """Devuelve datos fundamentales disponibles. Debe omitir (no inventar) los que falten."""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Comprobación ligera de disponibilidad (para el mecanismo de fallback)."""
        raise NotImplementedError
