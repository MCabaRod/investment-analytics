import streamlit as st

from ui_helpers import ensure_schema, get_favorite_asset_ids, get_session, render_asset_card

st.set_page_config(page_title="Investment Analytics", page_icon="📊", layout="wide")
ensure_schema()

st.title("📊 Investment Analytics")
st.caption(
    "Información y herramientas de análisis con fines exclusivamente informativos y "
    "educativos. No constituye asesoramiento financiero ni recomendación personalizada "
    "de inversión."
)

query = st.text_input("🔍 Buscar activo (nombre, ticker o ISIN)...", key="dashboard_search")

db = get_session()
try:
    if query:
        from app.services.asset_service import AssetService

        results = AssetService(db).search(query)
        st.subheader(f"Resultados para «{query}»")
        if not results:
            st.info("Sin resultados.")
        favorite_ids = get_favorite_asset_ids(db)
        cols = st.columns(3)
        for i, asset in enumerate(results):
            with cols[i % 3]:
                render_asset_card(db, asset, favorite_ids)
        st.stop()

    tipo = st.radio(
        "Tipo de activo",
        options=["Todos", "Acciones", "ETFs", "Fondos"],
        horizontal=True,
    )
    type_map = {"Acciones": "stock", "ETFs": "etf", "Fondos": "fund"}
    asset_type = type_map.get(tipo)

    if tipo == "Fondos":
        st.info(
            "⚠️ Los fondos de inversión están soportados en el modelo de datos, pero "
            "aún no hay una fuente de datos automática conectada para ellos (no existe "
            "una API abierta fiable para fondos UCITS). Puedes darlos de alta desde "
            "Admin, pero sin histórico automático por ahora."
        )

    st.subheader("⭐ Destacados")
    from app.models.asset import AssetType
    from app.services.asset_service import AssetService

    featured = AssetService(db).list_assets(
        asset_type=AssetType(asset_type) if asset_type else None,
        only_featured=True,
        limit=50,
        offset=0,
    )
    favorite_ids = get_favorite_asset_ids(db)

    if not featured:
        st.info("No hay activos destacados de este tipo todavía.")
    else:
        cols = st.columns(4)
        for i, asset in enumerate(featured):
            with cols[i % 4]:
                render_asset_card(db, asset, favorite_ids)

    st.divider()
    st.subheader("Todos los activos")
    all_assets = AssetService(db).list_assets(
        asset_type=AssetType(asset_type) if asset_type else None,
        only_featured=False,
        limit=200,
        offset=0,
    )
    if all_assets:
        st.dataframe(
            [
                {
                    "Nombre": a.name,
                    "Ticker": a.ticker or "N/D",
                    "Tipo": a.asset_type.value,
                    "ISIN": a.isin or "N/D",
                    "Divisa": a.currency or "N/D",
                }
                for a in all_assets
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No hay activos de este tipo. Añade alguno desde la página Admin.")
finally:
    db.close()
