"""
Siembra la selección inicial de activos destacados (punto 7 y 30 del
encargo): configurable vía este script, nunca hardcodeada en el frontend.

Uso:
    python -m app.core.seed_featured_assets

Idempotente: si el ISIN/ticker ya existe, actualiza is_featured/featured_order
en lugar de duplicar.
"""
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.asset import Asset, AssetType

DEFAULT_FEATURED: list[dict] = [
    {"name": "Microsoft Corporation", "asset_type": AssetType.stock, "isin": "US5949181045", "ticker": "MSFT", "exchange": "NASDAQ", "currency": "USD", "featured_order": 1},
    {"name": "Apple Inc.", "asset_type": AssetType.stock, "isin": "US0378331005", "ticker": "AAPL", "exchange": "NASDAQ", "currency": "USD", "featured_order": 2},
    {"name": "NVIDIA Corporation", "asset_type": AssetType.stock, "isin": "US67066G1040", "ticker": "NVDA", "exchange": "NASDAQ", "currency": "USD", "featured_order": 3},
    {"name": "Amazon.com Inc.", "asset_type": AssetType.stock, "isin": "US0231351067", "ticker": "AMZN", "exchange": "NASDAQ", "currency": "USD", "featured_order": 4},
    {"name": "Vanguard S&P 500 ETF", "asset_type": AssetType.etf, "isin": "US9229083632", "ticker": "VOO", "exchange": "NYSEARCA", "currency": "USD", "featured_order": 5},
    {"name": "iShares Core MSCI World UCITS ETF", "asset_type": AssetType.etf, "isin": "IE00B4L5Y983", "ticker": "IWDA", "exchange": "LSE", "currency": "USD", "featured_order": 6},
    {"name": "Invesco EQQQ Nasdaq-100 UCITS ETF", "asset_type": AssetType.etf, "isin": "IE0032077012", "ticker": "EQQQ", "exchange": "LSE", "currency": "USD", "featured_order": 7},
]


def seed(db: Session) -> None:
    for entry in DEFAULT_FEATURED:
        existing = db.query(Asset).filter(Asset.isin == entry["isin"]).first()
        if existing:
            existing.is_featured = True
            existing.featured_order = entry["featured_order"]
        else:
            db.add(Asset(**entry, is_featured=True))
    db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
        print(f"Sembrados/actualizados {len(DEFAULT_FEATURED)} activos destacados.")
    finally:
        session.close()
