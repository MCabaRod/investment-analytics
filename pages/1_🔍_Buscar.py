import streamlit as st

from ui_helpers import ensure_schema, get_favorite_asset_ids, get_session, render_asset_card

st.set_page_config(page_title="Buscar · Investment Analytics", page_icon="🔍", layout="wide")
ensure_schema()

st.title("🔍 Buscar activo")
query = st.text_input("Nombre, ticker o ISIN", key="search_page_query")

db = get_session()
try:
    if query:
        from app.services.asset_service import AssetService

        results = AssetService(db).search(query)
        if not results:
            st.info("Sin resultados. Puedes darlo de alta desde la página Admin.")
        favorite_ids = get_favorite_asset_ids(db)
        cols = st.columns(3)
        for i, asset in enumerate(results):
            with cols[i % 3]:
                render_asset_card(db, asset, favorite_ids)
    else:
        st.caption("Escribe para buscar por coincidencia parcial de nombre, ticker o ISIN.")
finally:
    db.close()
