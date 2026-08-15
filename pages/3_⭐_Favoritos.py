import streamlit as st

from ui_helpers import ensure_schema, get_favorite_asset_ids, get_session, render_asset_card

st.set_page_config(page_title="Favoritos · Investment Analytics", page_icon="⭐", layout="wide")
ensure_schema()

st.title("⭐ Mis favoritos")

db = get_session()
try:
    from app.core.demo_user import get_current_user
    from app.services.favorite_service import FavoriteService

    user = get_current_user(db)
    favorites = FavoriteService(db).list_for_user(user.id)

    if not favorites:
        st.info("Aún no tienes favoritos. Márcalos desde el Dashboard, el Buscador o la ficha de activo.")
    else:
        favorite_ids = get_favorite_asset_ids(db)
        cols = st.columns(3)
        for i, fav in enumerate(favorites):
            with cols[i % 3]:
                render_asset_card(db, fav.asset, favorite_ids)
finally:
    db.close()
