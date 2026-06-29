# Flows

Prefect flow wrappers will live here once the local package and metadata tables are stable.

Initial planned flows:

- `ingest_sources.py`
- `build_warehouse.py`
- `train_models.py`
- `publish_artifacts.py`

Flows should call reusable package code rather than contain important business logic themselves.

