import streamlit as st

from ui_helpers import (
    PERIOD_DAYS,
    build_price_chart,
    ensure_schema,
    fmt_money,
    fmt_pct,
    get_favorite_asset_ids,
    get_session,
    period_start_date,
    toggle_favorite,
)

st.set_page_config(page_title="Ficha de activo · Investment Analytics", page_icon="📈", layout="wide")
ensure_schema()

db = get_session()
try:
    from app.services.asset_service import AssetService

    asset_id = st.session_state.get("selected_asset_id")
    qp_asset_id = st.query_params.get("asset_id")
    if asset_id is None and qp_asset_id:
        asset_id = int(qp_asset_id)

    if asset_id is None:
        st.title("📈 Ficha de activo")
        assets = AssetService(db).list_assets(asset_type=None, only_featured=False, limit=500, offset=0)
        if not assets:
            st.info("No hay activos todavía. Añade alguno desde Admin.")
            st.stop()
        options = {f"{a.name} ({a.ticker or a.isin or a.id})": a.id for a in assets}
        chosen = st.selectbox("Selecciona un activo", options=list(options.keys()))
        asset_id = options[chosen]
        st.session_state["selected_asset_id"] = asset_id

    from fastapi import HTTPException

    try:
        asset = AssetService(db).get_or_404(asset_id)
    except HTTPException:
        st.error("Ese activo no existe.")
        st.stop()

    st.query_params["asset_id"] = str(asset_id)

    # --- Cabecera ---
    favorite_ids = get_favorite_asset_ids(db)
    is_fav = asset.id in favorite_ids

    col_title, col_fav = st.columns([5, 1])
    with col_title:
        st.title(asset.name)
        st.caption(
            f"{asset.ticker or 'N/D'} · {asset.exchange or 'N/D'} · {asset.currency or 'N/D'} · "
            f"{asset.asset_type.value.upper()}"
        )
    with col_fav:
        st.write("")
        if st.button("★ Quitar de favoritos" if is_fav else "☆ Añadir a favoritos"):
            toggle_favorite(db, asset.id, is_fav)
            st.rerun()

    # --- Métricas de cabecera ---
    from app.services.metrics_service import MetricsService

    metrics = MetricsService(db).compute(asset.id)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("YTD", fmt_pct(metrics.ytd_return))
    m2.metric("1 año", fmt_pct(metrics.return_1y))
    m3.metric("3 años", fmt_pct(metrics.return_3y))
    m4.metric("5 años", fmt_pct(metrics.return_5y))
    m5.metric("Desde inicio", fmt_pct(metrics.return_since_inception))

    if metrics.data_points == 0:
        st.warning(
            "Sin histórico almacenado todavía. Ve a Admin y pulsa 'Actualizar todos los "
            "activos' para cargarlo (requiere que este servidor tenga salida a internet)."
        )

    st.divider()

    # --- Gráfico histórico ---
    from app.repositories.price_repository import PriceHistoryRepository

    repo = PriceHistoryRepository(db)
    period = st.radio(
        "Periodo", options=list(PERIOD_DAYS.keys()), index=3, horizontal=True, key="period_selector"
    )
    view_mode = st.radio(
        "Vista", options=["Precio", "Rentabilidad normalizada (base 100)"], horizontal=True
    )

    import datetime as dt

    latest_date = metrics.as_of if metrics.data_points else dt.date.today()
    start = period_start_date(period, latest_date) or dt.date(1990, 1, 1)
    rows = repo.get_range(asset.id, start, latest_date)

    if rows:
        mode = "normalized" if view_mode.startswith("Rentabilidad") else "price"
        st.plotly_chart(build_price_chart(rows, mode=mode), width="stretch")
        last_updated = repo.get_last_retrieved_at(asset.id)
        st.caption(f"Datos actualizados: {last_updated.strftime('%d/%m/%Y %H:%M UTC') if last_updated else 'N/D'}")
    else:
        st.info("Sin datos para este periodo.")

    st.divider()

    # --- Riesgo ---
    st.subheader("Riesgo")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Volatilidad anualizada", fmt_pct(metrics.volatility_annualized))
    r2.metric("Máximo drawdown", fmt_pct(metrics.max_drawdown))
    r3.metric("Sharpe", f"{metrics.sharpe_ratio:.2f}" if metrics.sharpe_ratio is not None else "N/D")
    r4.metric("Sortino", f"{metrics.sortino_ratio:.2f}" if metrics.sortino_ratio is not None else "N/D")
    with st.expander("¿Qué significa cada métrica?"):
        st.markdown(
            "- **Volatilidad anualizada**: dispersión de los retornos diarios, anualizada. "
            "Mayor volatilidad = mayor variación de precio en el tiempo.\n"
            "- **Máximo drawdown**: la mayor caída porcentual desde un máximo histórico hasta "
            "el valle posterior.\n"
            "- **Sharpe**: rentabilidad ajustada al riesgo total, comparada con la tasa libre "
            f"de riesgo configurada ({metrics.risk_free_rate_used:.2%}).\n"
            "- **Sortino**: como Sharpe, pero solo penaliza la volatilidad de los retornos "
            "negativos (no castiga la volatilidad al alza)."
        )
    if metrics.note:
        st.caption(f"ℹ️ {metrics.note}")

    st.divider()

    # --- Fundamentales (solo para acciones, en vivo desde el proveedor) ---
    if asset.asset_type.value == "stock":
        st.subheader("Fundamentales")
        st.caption(
            "Estos datos se piden en vivo al proveedor (no están cacheados en base de datos "
            "en esta fase). Si faltan, se muestra N/D — nunca se inventan."
        )
        if st.button("Consultar fundamentales"):
            from app.data_sources.provider_chain import build_default_provider_chain

            symbol = asset.ticker or ""
            with st.spinner("Consultando proveedor..."):
                try:
                    source, data = build_default_provider_chain().get_fundamentals(
                        {"yahoo_finance": symbol}
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"No se pudo obtener fundamentales: {exc}")
                    data, source = {}, "none"

            labels = {
                "pe_ratio": "P/E", "forward_pe": "Forward P/E", "peg_ratio": "PEG",
                "price_to_book": "P/B", "ev_ebitda": "EV/EBITDA",
                "dividend_yield": "Dividend Yield", "market_cap": "Market Cap",
                "eps": "EPS", "revenue_growth": "Revenue Growth",
                "earnings_growth": "Earnings Growth", "roe": "ROE",
                "debt_to_equity": "Debt/Equity",
            }
            cols = st.columns(4)
            for i, (key, label) in enumerate(labels.items()):
                with cols[i % 4]:
                    value = data.get(key)
                    st.metric(label, "N/D" if value is None else f"{value:,.2f}")
            st.caption(f"Fuente: {source}")
finally:
    db.close()
