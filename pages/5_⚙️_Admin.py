import streamlit as st

from ui_helpers import ensure_schema, get_session

st.set_page_config(page_title="Admin · Investment Analytics", page_icon="⚙️", layout="wide")
ensure_schema()

st.title("⚙️ Administración")
st.caption(
    "Panel mínimo del MVP (punto 31 del encargo): alta de activos, forzar actualización "
    "y ver incidencias de calidad de datos."
)

db = get_session()
try:
    tab_add, tab_refresh, tab_quality = st.tabs(["➕ Añadir activo", "🔄 Actualizar datos", "🩺 Calidad de datos"])

    with tab_add:
        from app.models.asset import AssetType
        from app.schemas.asset import AssetCreate
        from app.services.asset_service import AssetService
        from fastapi import HTTPException

        with st.form("add_asset_form"):
            name = st.text_input("Nombre *")
            asset_type = st.selectbox(
                "Tipo *", options=["stock", "etf", "fund"],
                format_func=lambda v: {"stock": "Acción", "etf": "ETF", "fund": "Fondo"}[v],
            )
            col1, col2 = st.columns(2)
            with col1:
                ticker = st.text_input("Ticker")
                exchange = st.text_input("Mercado (exchange)")
            with col2:
                isin = st.text_input("ISIN")
                currency = st.text_input("Divisa (3 letras, p.ej. USD)")
            is_featured = st.checkbox("Marcar como destacado")

            submitted = st.form_submit_button("Crear activo")
            if submitted:
                if not name:
                    st.error("El nombre es obligatorio.")
                else:
                    try:
                        created = AssetService(db).create(
                            AssetCreate(
                                name=name,
                                asset_type=AssetType(asset_type),
                                ticker=ticker or None,
                                isin=isin or None,
                                exchange=exchange or None,
                                currency=currency.upper() or None,
                                is_featured=is_featured,
                            )
                        )
                        st.success(f"Activo creado: {created.name} (id {created.id})")
                    except HTTPException as exc:
                        st.error(exc.detail)

        st.divider()
        if st.button("Sembrar/actualizar destacados por defecto"):
            from app.core.seed_featured_assets import seed

            seed(db)
            st.success("Destacados sembrados/actualizados.")

    with tab_refresh:
        from app.models.asset import Asset
        from app.services.price_ingestion_service import PriceIngestionService

        st.write(
            "Fuerza la actualización de histórico para todos los activos activos. "
            "Requiere que **este servidor** (Streamlit Cloud) tenga salida a internet "
            "hacia Yahoo Finance / Stooq — no depende de tu ordenador."
        )
        if st.button("Actualizar todos los activos activos", type="primary"):
            service = PriceIngestionService(db)
            assets = db.query(Asset).filter(Asset.is_active.is_(True)).all()
            progress = st.progress(0.0)
            results = []
            for i, asset in enumerate(assets):
                try:
                    result = service.update_asset(asset)
                    results.append((asset.name, asset.ticker, result.status, result.source, result.points_written))
                except Exception as exc:  # noqa: BLE001
                    results.append((asset.name, asset.ticker, "error", None, str(exc)))
                progress.progress((i + 1) / max(len(assets), 1))
            st.dataframe(
                [
                    {"Activo": r[0], "Ticker": r[1], "Estado": r[2], "Fuente": r[3], "Puntos escritos": r[4]}
                    for r in results
                ],
                width="stretch",
                hide_index=True,
            )

        st.divider()
        st.write("Actualizar un único activo:")
        assets_all = db.query(Asset).filter(Asset.is_active.is_(True)).all()
        options = {f"{a.name} ({a.ticker or a.id})": a for a in assets_all}
        if options:
            chosen = st.selectbox("Activo", options=list(options.keys()), key="single_refresh")
            if st.button("Actualizar este activo"):
                result = PriceIngestionService(db).update_asset(options[chosen])
                st.success(f"Estado: {result.status} · Fuente: {result.source} · Puntos: {result.points_written}")

    with tab_quality:
        from app.repositories.data_quality_repository import DataQualityLogRepository

        logs = DataQualityLogRepository(db).list_unresolved()
        st.write(f"{len(logs)} incidencias sin resolver.")
        if logs:
            st.dataframe(
                [
                    {
                        "Fecha": log.detected_at.strftime("%d/%m/%Y %H:%M"),
                        "Activo ID": log.asset_id,
                        "Fuente": log.source,
                        "Tipo": log.issue_type.value,
                        "Detalle": log.detail,
                    }
                    for log in logs
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.success("Sin incidencias de calidad pendientes.")
finally:
    db.close()
