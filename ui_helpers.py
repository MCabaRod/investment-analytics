"""
Funciones compartidas por todas las páginas de Streamlit.

IMPORTANTE: importa `bootstrap` antes que nada, y este módulo antes de tocar
`app.*`, para que la configuración (DATABASE_URL, etc.) ya esté cargada
desde `st.secrets` cuando se creen el engine y las sesiones.
"""
from __future__ import annotations

import datetime as dt

import bootstrap  # noqa: F401 - efecto secundario: carga secrets en el entorno
import plotly.graph_objects as go
import streamlit as st

ASSET_TYPE_LABELS = {"stock": "Acción", "etf": "ETF", "fund": "Fondo"}
PERIOD_DAYS = {
    "1M": 30, "3M": 90, "6M": 182, "1A": 365, "3A": 365 * 3,
    "5A": 365 * 5, "10A": 365 * 10, "MAX": None,
}


@st.cache_resource(show_spinner="Preparando la base de datos...")
def ensure_schema() -> bool:
    """
    Crea las tablas si no existen y siembra los destacados por defecto.
    Sustituye a `alembic upgrade head` en este modo de despliegue (sin
    acceso a shell en Streamlit Cloud). Es idempotente: no borra datos
    existentes si ya se ejecutó antes.
    """
    from app.core.database import SessionLocal, engine
    from app.core.seed_featured_assets import seed
    from app.models.base import Base

    import app.models  # noqa: F401 - registra todos los modelos

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    return True


def get_session():
    from app.core.database import SessionLocal

    return SessionLocal()


def fmt_pct(value: float | None) -> str:
    return "N/D" if value is None else f"{value:+.2%}"


def fmt_money(value, currency: str | None = None) -> str:
    if value is None:
        return "N/D"
    suffix = f" {currency}" if currency else ""
    return f"{float(value):,.2f}{suffix}"


def asset_type_label(asset_type) -> str:
    key = asset_type.value if hasattr(asset_type, "value") else str(asset_type)
    return ASSET_TYPE_LABELS.get(key, key)


def go_to_asset(asset_id: int) -> None:
    st.session_state["selected_asset_id"] = asset_id
    st.switch_page("pages/2_📈_Detalle.py")


def get_favorite_asset_ids(db) -> set[int]:
    from app.core.demo_user import get_current_user
    from app.services.favorite_service import FavoriteService

    user = get_current_user(db)
    return {f.asset_id for f in FavoriteService(db).list_for_user(user.id)}


def toggle_favorite(db, asset_id: int, is_favorite: bool) -> None:
    from app.core.demo_user import get_current_user
    from app.services.favorite_service import FavoriteService

    user = get_current_user(db)
    service = FavoriteService(db)
    if is_favorite:
        service.remove(user.id, asset_id)
    else:
        service.add(user.id, asset_id)


def render_asset_card(db, asset, favorite_ids: set[int]) -> None:
    from app.services.metrics_service import MetricsService

    with st.container(border=True):
        st.markdown(f"**{asset.name}**")
        st.caption(f"{asset.ticker or 'N/D'} · {asset_type_label(asset.asset_type)} · {asset.currency or ''}")

        metrics = MetricsService(db).compute(asset.id)
        st.metric("YTD", fmt_pct(metrics.ytd_return))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Ver ficha", key=f"view_{asset.id}", width="stretch"):
                go_to_asset(asset.id)
        with col2:
            is_fav = asset.id in favorite_ids
            label = "★ Quitar" if is_fav else "☆ Favorito"
            if st.button(label, key=f"fav_{asset.id}", width="stretch"):
                toggle_favorite(db, asset.id, is_fav)
                st.rerun()


def build_price_chart(rows, mode: str = "price") -> go.Figure:
    """
    `rows` son objetos PriceHistory ordenados por fecha. `mode` es "price" o
    "normalized" (rentabilidad normalizada a 100, punto 18 del encargo).
    """
    from app.calculations.returns import normalize_to_100

    dates = [r.date for r in rows]
    if mode == "normalized":
        series = normalize_to_100([(r.date, r.close) for r in rows])
        values = [float(v) for _, v in series]
        y_title = "Rentabilidad normalizada (base 100)"
    else:
        values = [float(r.close) for r in rows]
        y_title = "Precio de cierre"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines", line=dict(width=2)))
    fig.update_layout(
        yaxis_title=y_title,
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(count=3, label="3A", step="year", stepmode="backward"),
                    dict(count=5, label="5A", step="year", stepmode="backward"),
                    dict(step="all", label="MAX"),
                ]
            ),
            rangeslider=dict(visible=False),
        ),
        hovermode="x unified",
    )
    return fig


def period_start_date(period_label: str, latest_date: dt.date) -> dt.date | None:
    days = PERIOD_DAYS.get(period_label)
    if days is None:
        return None
    return latest_date - dt.timedelta(days=days)
