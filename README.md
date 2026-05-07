# F1 Telemetry API

[![CI](https://github.com/facufernandez05/f1-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/facufernandez05/f1-analysis/actions/workflows/ci.yml)

Portfolio-ready backend project built with FastAPI, SQLAlchemy, PostgreSQL,
Alembic, and FastF1.

It ingests real Formula 1 session data and exposes analysis endpoints such as
fastest lap, average lap time, per-driver rankings, and lap-by-lap pace trends.

It also includes a Python SDK so other developers can consume your API as a
library in their own projects.

## What this project does

- Ingests real session data from FastF1 (`POST /api/v1/ingest/`)
- Stores normalized data in PostgreSQL (`sessions`, `drivers`, `laps`)
- Exposes clean REST endpoints under `/api/v1`
- Returns computed analytics (`GET /api/v1/sessions/{id}/stats`)
- Returns pace time-series ready for charts (`GET /api/v1/sessions/{id}/pace`)
- Ships a reusable Python client library (`sdk/f1telemetry_sdk`)
- Includes automated quality checks in CI (ruff, black, isort, pytest)

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL 16
- FastF1
- Docker + Docker Compose
- pytest + ruff + black + isort

## Quick Start (Docker-only)

### 1) Clone and configure env vars

```bash
git clone https://github.com/facufernandez05/f1-analysis.git
cd f1-analysis
cp .env.example .env
```

### 2) Start everything

```bash
make up
```

If Docker ever reports `permission denied` for `entrypoint.sh`:

```bash
chmod +x entrypoint.sh
```

What happens here:

- PostgreSQL starts on `localhost:5433`
- API starts on `localhost:8000`
- Migrations run automatically (`alembic upgrade head`) before the API boots

### 3) Verify API is alive

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","app":"F1 Telemetry API"}
```

### 4) Ingest a real F1 session

```bash
make ingest YEAR=2024 GP=Bahrain SESSION=R
```

### 5) Inspect the data

```bash
make sessions
make drivers
make stats SESSION_ID=1
```

### 6) Open interactive docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 7) Stop services

```bash
make down
```

## Useful commands

```bash
make up                     # Build + run API and DB in background
make down                   # Stop containers
make logs                   # Follow API logs
make ps                     # Show container status
make shell                  # Shell inside api container

make test                   # Run pytest inside api container
make lint                   # Run ruff + black --check + isort --check-only
make format                 # Auto-format (black + isort)

make ingest YEAR=2024 GP=Monaco SESSION=Q
make stats SESSION_ID=1
make pace SESSION_ID=1
make laps SESSION_ID=1
make sdk-install            # install local SDK in editable mode
make sdk-build              # build wheel/sdist for distribution
```

## API endpoints

### Health

- `GET /health`

### Sessions

- `GET /api/v1/sessions/`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/sessions/{session_id}/stats`
- `GET /api/v1/sessions/{session_id}/pace?window_size=3&normalize_to_best=true`

### Drivers

- `GET /api/v1/drivers/`
- `GET /api/v1/drivers/{driver_code}`

### Laps

- `GET /api/v1/sessions/{session_id}/laps`
- `GET /api/v1/sessions/{session_id}/laps?driver_code=VER`

### Ingestion

- `POST /api/v1/ingest/`

Request body example:

```json
{
  "year": 2024,
  "grand_prix": "Bahrain",
  "session_type": "R"
}
```

## Project structure

```text
f1-analysis/
├── app/
│   ├── api/v1/          # FastAPI routers (sessions, drivers, laps, ingest)
│   ├── db/              # SQLAlchemy base, models, session dependency
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic (ingestion, analysis)
│   ├── config.py
│   └── main.py
├── alembic/             # Database migrations
├── tests/               # Unit and API tests
├── sdk/
│   └── f1telemetry_sdk/ # Installable Python SDK for external developers
├── data/                # FastF1 cache (gitignored)
├── docker-compose.dev.yml
├── Dockerfile
├── entrypoint.sh
├── Makefile
├── requirements.txt
└── .github/workflows/ci.yml
```

## Current status

- Iteration 1: project skeleton + Docker + CI (done)
- Iteration 2: data model + base endpoints + tests (done)
- Iteration 3: FastF1 ingestion service + CLI + tests (done)
- Iteration 4: ingestion API + session stats analytics + tests (done)
- Iteration 5: docker-first DX, auto migrations, docs polish (done)
- Iteration 6: pace analytics endpoint + installable Python SDK (done)

## Python SDK

The repo ships a developer-facing SDK at `sdk/f1telemetry_sdk`.

Install locally:

```bash
make sdk-install
```

Example:

```python
from f1telemetry_sdk import F1TelemetryClient, IngestRequest

client = F1TelemetryClient(base_url="http://localhost:8000")
client.health()

client.ingest(IngestRequest(year=2024, grand_prix="Bahrain", session_type="R"))
session_id = client.list_sessions()[0]["id"]

stats = client.session_stats(session_id)
pace = client.session_pace(session_id, window_size=5)
```

## Notes

- FastF1 cache path is configured via `FASTF1_CACHE_PATH`
- Cache is persisted in `./data` (ignored in git)
- First ingestion can take longer due to initial data downloads
