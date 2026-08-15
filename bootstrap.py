"""
Puente entre `st.secrets` (Streamlit Cloud) y la configuración de la
aplicación (`app.core.config.Settings`, que lee variables de entorno).

Debe importarse ANTES que cualquier módulo de `app.*` en cada página de
Streamlit, para que DATABASE_URL, SECRET_KEY, etc. estén disponibles cuando
`get_settings()` se ejecute por primera vez (está cacheado con @lru_cache,
así que solo hace falta que esté bien la primera vez).
"""
import os

import streamlit as st


def load_secrets_into_env() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return  # no hay secrets.toml (p.ej. ejecución local sin configurarlo aún)

    for key in secrets.keys():
        os.environ.setdefault(key.upper(), str(secrets[key]))


load_secrets_into_env()
