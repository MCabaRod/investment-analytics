"""
Scheduler de tareas en segundo plano. APScheduler es suficiente para el MVP
(un único proceso, sin necesidad de cola distribuida); si en el futuro se
necesita escalar a múltiples workers, este módulo es el único punto a
sustituir por Celery + Redis, sin tocar el resto de la aplicación.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.tasks.jobs.update_prices_job import run_daily_price_update

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone="UTC")
    # 21:30 UTC: después del cierre de NYSE/NASDAQ (21:00 UTC en horario
    # estándar; con horario de verano estadounidense el cierre real es
    # 20:00 UTC, así que este margen cubre ambos casos salvo festivos con
    # cierre anticipado, que no se contemplan en el MVP).
    _scheduler.add_job(
        run_daily_price_update,
        trigger=CronTrigger(hour=21, minute=30),
        id="daily_price_update",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    logger.info("Scheduler iniciado: actualización diaria de precios a las 21:30 UTC.")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
