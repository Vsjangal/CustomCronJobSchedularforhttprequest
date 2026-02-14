# API Scheduler

A backend service that lets users schedule HTTP requests to external targets — "cron for API calls".

## Features

- **Targets** — Define an HTTP endpoint (URL, method, headers, body template).
- **Schedules** — Trigger requests on an interval or within a time window, with pause/resume support.
- **Runs & Attempts** — Full execution history with per-attempt metadata (status code, latency, error classification).
- **Metrics** — Aggregated success/failure counts and average latency per schedule.
- **Restart-safe** — All state lives in the database; the scheduler resumes where it left off.
- **Duplicate-safe** — In-memory active-execution set prevents the same schedule from firing twice concurrently.

---

## Quick start

### Prerequisites

- Python 3.11+

### 1. Clone & install

```bash
cd api_scheduler
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure (optional)

```bash
cp .env.example .env
# Edit .env if you want to use PostgreSQL or change defaults
```

Default configuration uses **SQLite** — no external database required.

### 3. Run

```bash
uvicorn app.main:app --reload
```

The server starts at **http://127.0.0.1:8000**.  
Interactive docs at **http://127.0.0.1:8000/docs**.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/targets` | Create a target |
| `GET` | `/targets` | List all targets |
| `GET` | `/targets/{id}` | Get a target |
| `PUT` | `/targets/{id}` | Update a target |
| `DELETE`| `/targets/{id}` | Delete a target (cascades) |
| `POST` | `/schedules` | Create a schedule |
| `GET` | `/schedules` | List all schedules |
| `GET` | `/schedules/{id}` | Get a schedule |
| `POST` | `/schedules/{id}/pause` | Pause an active schedule |
| `POST` | `/schedules/{id}/resume` | Resume a paused schedule |
| `DELETE`| `/schedules/{id}` | Delete a schedule (cascades) |
| `GET` | `/runs` | List runs (filter by schedule, status, time range) |
| `GET` | `/runs/{id}` | Get a run with attempt history |
| `GET` | `/metrics` | Aggregated metrics |
| `GET` | `/health` | Liveness probe |

---

## Key design decisions

### Custom polling scheduler vs APScheduler

Chose a **custom async polling loop** over APScheduler because:
- Full control over scheduling logic and error handling.
- No pickle serialisation of jobs (APScheduler's SQLAlchemyJobStore uses pickle).
- Easier to reason about and debug.
- Natively async — no thread-pool overhead.

### SQLite by default

SQLite requires zero setup and is ideal for local development and demos. The code uses SQLAlchemy's async dialect (`aiosqlite`), so switching to PostgreSQL is a one-line config change (`DATABASE_URL=postgresql+asyncpg://...`).

### Naive UTC datetimes

All timestamps are stored as **naive UTC** datetimes. This avoids timezone-handling quirks in SQLite while keeping comparisons predictable.

### Duplicate execution prevention

An in-memory `_active_executions` set tracks schedule IDs currently being executed. The scheduler will not dispatch a schedule that is already in-flight. This prevents overlapping executions when a target is slow.

### Run → Attempt separation

Each scheduled trigger creates a **Run**. Each HTTP request within a Run (including retries) is an **Attempt**. This gives clean observability: you can see at a glance whether a Run succeeded on the first try or required retries.

### Error classification

HTTP errors are classified into categories — `timeout`, `dns`, `connection`, `http_4xx`, `http_5xx`, `unknown` — captured at the Attempt level for easy filtering and alerting.

---

## Architecture

```
┌─────────────┐      ┌───────────────────┐      ┌──────────────┐
│  FastAPI     │      │  SchedulerEngine  │      │  External    │
│  REST API    │      │  (async poll loop)│─────▶│  Targets     │
│  (CRUD +     │      │                   │      │  (HTTP)      │
│   Control)   │      └────────┬──────────┘      └──────────────┘
└──────┬───────┘               │
       │                       ▼
       │               ┌──────────────┐
       └──────────────▶│   SQLite /   │
                       │  PostgreSQL  │
                       └──────────────┘
```

---

## What I would do next for production

1. **PostgreSQL** — Switch from SQLite for proper concurrent writes and advisory locking.
2. **Alembic migrations** — Replace `create_all` with versioned schema migrations.
3. **Distributed locking** — Use `SELECT ... FOR UPDATE SKIP LOCKED` to support multiple worker instances.
4. **Retry backoff** — Exponential backoff between retry attempts instead of immediate retry.
5. **Rate limiting** — Per-target rate limits to avoid hammering external services.
6. **Webhook notifications** — Alert on repeated failures or schedule completion.
7. **Structured logging** — JSON logs for aggregation in ELK/Datadog.
8. **Prometheus metrics** — `/metrics` in Prometheus exposition format for Grafana dashboards.
9. **Authentication** — API key or JWT-based auth for multi-tenant usage.
10. **Containerisation** — Dockerfile + docker-compose for reproducible deploys.
