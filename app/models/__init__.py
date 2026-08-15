"""
Importa todos los modelos para que SQLAlchemy registre las relaciones y
Alembic los detecte en el autogenerate. Cualquier modelo nuevo debe añadirse
aquí.
"""
from app.models.asset import Asset, AssetIdentifier  # noqa: F401
from app.models.data_quality import DataQualityLog, DataSource  # noqa: F401
from app.models.favorite import Favorite  # noqa: F401
from app.models.price_history import PriceHistory  # noqa: F401
from app.models.user import User  # noqa: F401
