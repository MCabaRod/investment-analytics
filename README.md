# Investment Analytics

Aplicación de análisis y apoyo a la decisión de inversión en fondos, ETFs y acciones.

> ⚠️ Esta aplicación proporciona información y herramientas de análisis con fines
> exclusivamente informativos y educativos. No constituye asesoramiento financiero
> ni recomendación personalizada de inversión. No ejecuta operaciones ni se conecta
> a brokers. Los datos pueden contener errores o retrasos y las rentabilidades
> pasadas no garantizan resultados futuros.

## Estado del proyecto: Fase 3 — Datos

**Fase 1** entregó el proyecto base (FastAPI + PostgreSQL + Docker + Alembic
+ estructura modular). **Fase 2** añadió el modelo de activos, CRUD,
buscador, destacados configurables y favoritos con usuario `demo`.

**Fase 3** añade:
- `DataProvider` implementado por `YahooFinanceProvider` (principal, vía
  `yfinance`) y `StooqProvider` (secundario, CSV EOD sin autenticación).
- `ProviderChain`: fallback automático principal → secundario, orquestado
  desde `app/data_sources/provider_chain.py`, sin que `services/` conozca el
  proveedor concreto.
- `PriceHistory`: histórico diario con actualización **incremental** (solo
  se piden a la fuente los días posteriores al último dato almacenado).
- Validación de calidad (`app/services/price_ingestion_service.py`): precios
  nulos o negativos se descartan y se registran, fechas duplicadas se
  deduplican y se registran, variaciones diarias anómalas (>50%) se
  **conservan pero se marcan** para revisión — nunca se oculta un problema
  en silencio (`data_quality_logs`).
- Job diario (`APScheduler`, 21:30 UTC) que actualiza todos los activos
  activos. Documentado en el propio código que una única ejecución diaria es
  una simplificación del MVP frente a la diversidad de horarios de cierre
  por bolsa.
- `GET /api/assets/{id}/history` (lee solo de base de datos, nunca llama a
  una fuente externa en el request del usuario) y `POST
  /api/assets/{id}/refresh` (fuerza actualización síncrona — capacidad de
  administración del punto 31).

> **Importante:** este entorno de desarrollo sandbox no tiene salida de red
> hacia Yahoo Finance ni Stooq, así que `YahooFinanceProvider` y
> `StooqProvider` están probados con **mocks** (`tests/test_data_sources.py`),
> no contra las APIs reales. Verifica la ingesta real ejecutando
> `docker compose exec api python -c "..."` o esperando al job diario en tu
> propia máquina, que sí tiene acceso a internet.

## Estado del proyecto: Fase 4 — Cálculos financieros

Añade `app/calculations/` (returns, ytd, risk) con fórmulas documentadas y
probadas con valores deterministas: rentabilidad simple, YTD (explícitamente
distinto de "1 año" — usa el último cierre del año natural anterior),
rentabilidad a 1/3/5 años y desde inicio, normalización a base 100 (para el
comparador de la Fase 6), volatilidad anualizada, máximo drawdown, Sharpe y
Sortino. La tasa libre de riesgo es configurable (`RISK_FREE_RATE` en
`.env`), nunca hardcodeada.

Nuevo endpoint: `GET /api/assets/{id}/metrics` — cualquier métrica sin datos
suficientes se devuelve `null` (el frontend de la Fase 5 lo mostrará como
"N/D"), nunca se aproxima ni se inventa un valor.

Endpoints disponibles hasta ahora:
- `GET /`, `GET /api/health`
- `GET /api/assets`, `GET /api/assets/search?q=`, `GET /api/assets/{id}`
- `POST /api/assets`, `PATCH /api/assets/{id}`, `DELETE /api/assets/{id}`
- `GET /api/assets/{id}/history?start=&end=`, `POST /api/assets/{id}/refresh`
- `GET /api/assets/{id}/metrics`
- `GET /api/favorites`, `POST /api/favorites`, `DELETE /api/favorites/{asset_id}`
- Documentación automática en `/docs`

## Arranque local con Docker

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Documentación (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

## Arranque sin Docker (opcional)

Requiere Python 3.12+ y una instancia de PostgreSQL accesible.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # ajustar DATABASE_URL a tu Postgres local
uvicorn app.main:app --reload
```

## Tests

```bash
pytest --cov=app
```

## Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

## Datos iniciales

```bash
# Destacados por defecto (configurables, no hardcodeados en frontend)
docker compose exec api python -m app.core.seed_featured_assets

# Primera carga de histórico para todos los activos activos (acciones/ETFs)
docker compose exec api python3 -c "
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.services.price_ingestion_service import PriceIngestionService
db = SessionLocal()
service = PriceIngestionService(db)
for asset in db.query(Asset).filter(Asset.is_active.is_(True)).all():
    print(asset.ticker, service.update_asset(asset))
db.close()
"
```

## Estructura del proyecto

```
app/
├── main.py            # instancia FastAPI, middlewares, montaje de routers
├── api/                # rutas HTTP (sin lógica de negocio)
├── core/               # configuración, base de datos, seguridad
├── models/             # modelos SQLAlchemy (Fase 2+)
├── schemas/            # esquemas Pydantic de entrada/salida (Fase 2+)
├── services/           # lógica de negocio (Fase 2+)
├── repositories/        # acceso a datos vía SQLAlchemy (Fase 2+)
├── data_sources/        # proveedores de datos (yfinance, Stooq, ...) (Fase 3)
├── scraping/            # scraping específico cuando no exista API oficial
├── calculations/        # rentabilidad, volatilidad, Sharpe, drawdown, YTD (Fase 4)
├── tasks/               # tareas programadas (APScheduler) (Fase 3)
├── templates/            # Jinja2 (Fase 5)
└── static/               # CSS/JS (Fase 5)
```

## Próximas fases

Ver el plan completo de fases en la documentación de arquitectura entregada
junto con este proyecto (Fase 2: modelo de activos y buscador · Fase 3:
proveedores de datos e histórico · Fase 4: cálculos financieros · Fase 5:
frontend · Fase 6: comparador · Fase 7: calidad y tests · Fase 8: refinamiento).

## 🚀 Despliegue con Streamlit Cloud (sin Docker, sin instalar nada local)

Ver la guía paso a paso completa en la conversación de diseño / mensaje de
entrega. Resumen:

1. Base de datos Postgres gratuita en [Neon.tech](https://neon.tech) (crear proyecto desde el navegador).
2. Subir este proyecto a un repositorio de GitHub (se puede hacer con "Add file → Upload files" desde la web, sin instalar git).
3. Desplegar en [share.streamlit.io](https://share.streamlit.io), archivo principal `streamlit_app.py`.
4. Configurar en Settings → Secrets el contenido de `.streamlit/secrets.toml.example` con tus credenciales reales de Neon.
5. (Opcional) Activar `.github/workflows/update_prices.yml` para actualización diaria automática vía GitHub Actions, sin servidor propio.

La app crea las tablas y siembra los destacados automáticamente en el primer arranque (`ui_helpers.ensure_schema`), sin necesidad de ejecutar Alembic a mano.
