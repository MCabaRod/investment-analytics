import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from ui_helpers import PERIOD_DAYS, ensure_schema, fmt_pct, get_session, period_start_date

st.set_page_config(page_title="Comparador · Investment Analytics", page_icon="⚖️", layout="wide")
ensure_schema()

st.title("⚖️ Comparador de activos")

db = get_session()
try:
    from app.services.asset_service import AssetService

    all_assets = AssetService(db).list_assets(asset_type=None, only_featured=False, limit=500, offset=0)
    options = {f"{a.name} ({a.ticker or a.isin or a.id})": a for a in all_assets}

    if not options:
        st.info("No hay activos todavía. Añade alguno desde Admin.")
        st.stop()

    chosen_labels = st.multiselect(
        "Selecciona 2 o más activos a comparar", options=list(options.keys()), max_selections=6
    )

    if len(chosen_labels) < 2:
        st.info("Elige al menos 2 activos para comparar.")
        st.stop()

    assets = [options[label] for label in chosen_labels]

    period = st.radio("Periodo", options=list(PERIOD_DAYS.keys()), index=3, horizontal=True)

    from app.repositories.price_repository import PriceHistoryRepository
    from app.services.metrics_service import MetricsService
    from app.calculations.returns import normalize_to_100

    repo = PriceHistoryRepository(db)
    metrics_service = MetricsService(db)

    table_rows = []
    fig = go.Figure()

    for asset in assets:
        metrics = metrics_service.compute(asset.id)
        latest_date = metrics.as_of if metrics.data_points else dt.date.today()
        start = period_start_date(period, latest_date) or dt.date(1990, 1, 1)
        rows = repo.get_range(asset.id, start, latest_date)

        table_rows.append(
            {
                "Activo": asset.name,
                "Ticker": asset.ticker or "N/D",
                "YTD": fmt_pct(metrics.ytd_return),
                "1 año": fmt_pct(metrics.return_1y),
                "3 años": fmt_pct(metrics.return_3y),
                "5 años": fmt_pct(metrics.return_5y),
                "Volatilidad": fmt_pct(metrics.volatility_annualized),
                "Drawdown": fmt_pct(metrics.max_drawdown),
                "Sharpe": f"{metrics.sharpe_ratio:.2f}" if metrics.sharpe_ratio is not None else "N/D",
            }
        )

        if rows:
            normalized = normalize_to_100([(r.date, r.close) for r in rows])
            fig.add_trace(
                go.Scatter(
                    x=[d for d, _ in normalized],
                    y=[float(v) for _, v in normalized],
                    mode="lines",
                    name=asset.name,
                )
            )

    st.subheader("Tabla comparativa")
    st.dataframe(table_rows, width="stretch", hide_index=True)

    st.subheader("Rentabilidad normalizada (base 100)")
    st.caption(
        "Todos los activos empiezan en 100 en la fecha inicial del periodo seleccionado, "
        "para poder comparar activos con precios nominales muy distintos (punto 18 del "
        "encargo original)."
    )
    if fig.data:
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=450, hovermode="x unified")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Ninguno de los activos seleccionados tiene histórico almacenado todavía.")
finally:
    db.close()
