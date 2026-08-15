"""
Job programado: actualiza el histórico de precios de todos los activos
activos (destacados o no). Diseñado para ejecutarse una vez al día tras el
cierre del mercado estadounidense (ver scheduler.py).

Limitación conocida y documentada (punto 36 del encargo): con una única
ejecución diaria no se respeta el horario de cierre específico de cada bolsa
(NASDAQ, LSE, Xetra, ...). Para el MVP es una simplificación aceptable
porque yfinance/Stooq devuelven el último cierre disponible en cada mercado,
no un valor intradía; una mejora futura sería programar una ejecución por
zona horaria de mercado.
"""
import logging

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.repositories.data_quality_repository import DataQualityLogRepository
from app.services.price_ingestion_service import PriceIngestionService

logger = logging.getLogger(__name__)


def run_daily_price_update() -> dict:
    """Punto de entrada del job. Nunca lanza excepción: cada fallo se registra."""
    db = SessionLocal()
    summary = {"updated": 0, "up_to_date": 0, "no_data": 0, "errors": 0}
    try:
        service = PriceIngestionService(db)
        assets = db.query(Asset).filter(Asset.is_active.is_(True)).all()
        for asset in assets:
            try:
                result = service.update_asset(asset)
                summary[result.status] = summary.get(result.status, 0) + 1
            except Exception as exc:  # noqa: BLE001 - un fallo no debe frenar el resto
                logger.exception("Fallo actualizando asset_id=%s: %s", asset.id, exc)
                DataQualityLogRepository(db).log(
                    asset.id, source="scheduler", issue_type=_import_error_type(), detail=str(exc)
                )
                summary["errors"] += 1
        logger.info("Actualización diaria de precios completada: %s", summary)
        return summary
    finally:
        db.close()


def _import_error_type():
    from app.models.data_quality import DataQualityIssueType

    return DataQualityIssueType.provider_unavailable


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = run_daily_price_update()
    print(summary)
