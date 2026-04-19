# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant SaaS CRM with omnichannel support. FastAPI backend + React frontend, PostgreSQL, Redis, Celery.

## Common Commands

### Running the stack
```bash
docker compose up                          # Start all services (api, db, redis, worker, beat)
docker compose up --build                  # Rebuild images before starting
docker compose logs -f api                 # Stream API logs
```

### Frontend development
```bash
cd frontend
npm run dev        # Dev server at http://localhost:5173
npm run build      # Production build
npm run lint       # ESLint
```

### Database migrations
```bash
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "description"
```

### Useful endpoints
- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `GET /health`

## Architecture

### Backend (`backend/app/`)

**Layered architecture:**
1. `api/v1/` — FastAPI route handlers (thin controllers)
2. `services/` — Business logic
3. `repositories/` — Data access; every repo extends `BaseRepository` which auto-filters by `tenant_id`
4. `models/` — SQLAlchemy 2.0 async ORM models
5. `schemas/` — Pydantic v2 request/response models

**Multitenancy** is row-level via `TenantMiddleware` (`core/middleware.py`). The middleware reads `tenant_id` from the JWT and sets it in a context var. `BaseRepository` uses this context var to scope every query — never bypass it by querying models directly.

**Auth flow:** JWT HS256 tokens. `sub` = user_id, `tenant_id` claim drives tenant isolation. Access tokens expire in 30 min, refresh tokens in 7 days. Public paths (no auth required) are declared in `core/middleware.py`.

**Omnichannel layer** (`channels/`): registry + base class pattern. Channel credentials are encrypted before storage (`core/encryption.py`). `AgentChannel` model links agents to channels.

**Async task queue:** Celery + Redis broker. Workers defined in `workers/`. The `celerybeat-schedule` file persists the beat scheduler state.

### Frontend (`frontend/src/`)

- **Routing:** React Router 7 with auth-guarded routes
- **State:** Zustand (`store/authStore.ts`) — only auth state is global
- **HTTP:** Axios clients in `api/` directory, one file per resource
- **Styling:** Tailwind CSS 4

### Key Models

| Model | Purpose |
|---|---|
| `Tenant` | Top-level account/org |
| `User` | Agent/admin, belongs to Tenant |
| `Customer` | End user/contact |
| `Ticket` | Support case, has status/priority |
| `TicketConfig` | Per-tenant ticket configuration |
| `Message` | Individual message within a ticket |
| `Channel` | Communication channel config (email, WhatsApp, etc.) |
| `AgentChannel` | Many-to-many: Agent ↔ Channel |

### Database

PostgreSQL 16. All migrations in `backend/migrations/versions/`. Migrations are **not** applied automatically on container start — run `alembic upgrade head` manually after schema changes.

## Environment Setup

Copy `.env.example` to `.env` before running. The backend reads config from `app/core/config.py` using `pydantic-settings`.

## Current State

### Phase 4 — Metrics, Admin & Testing (completed)

**Backend — new files:**
- `backend/app/repositories/metrics_repo.py` — MetricsRepository with 8 query methods
- `backend/app/services/metrics_service.py` — orchestrates MetricsRepository
- `backend/app/schemas/metrics.py` — response schemas for metrics
- `backend/app/api/v1/metrics.py` — 7 metrics endpoints
- `backend/app/api/v1/admin.py` — User CRUD + tenant management

**Frontend — new files:**
- `frontend/src/pages/Dashboard.tsx` — Recharts dashboard (BarChart, PieChart donut, AreaChart)
- `frontend/src/pages/Reports.tsx` — reports page with 3 tabs (agents, types, channels)
- `frontend/src/pages/Admin.tsx` — admin panel with 3 tabs (users, channels, account)
- `frontend/src/api/admin.ts` — API functions for admin panel
- `frontend/src/api/tickets.ts` — 7 metrics functions added

**Testing — new files:**
- `backend/pytest.ini` — pytest config with `asyncio_mode = auto`
- `backend/tests/conftest.py` — global fixtures, `crm_test` DB, `NullPool`
- `backend/tests/test_auth.py` — 7 tests
- `backend/tests/test_tickets.py` — 11 tests
- `backend/tests/test_customers.py` — 7 tests
- `backend/tests/test_metrics.py` — 8 tests
- `backend/tests/test_admin.py` — 8 tests
- **Total: 41/41 PASSED**

**Dependencies added:**
- Backend: `pytest==8.3.3`, `pytest-asyncio==0.24.0`, `anyio==4.6.2`
- Frontend: `recharts`

**Frontend routes:**
- `/` → Dashboard
- `/tickets` → Ticket list
- `/tickets/:id` → Ticket detail
- `/customers` → Customers
- `/reports` → Reports
- `/admin` → Admin panel

### Phase 3 — Omnichannel (completed)
- Celery + Redis + Beat scheduler running
- `channels` and `agent_channels` tables in DB
- `BaseChannel` abstract interface with `InboundMessage` / `OutboundMessage`
- `EmailChannel` — SMTP send + IMAP polling (every 60s via Beat)
- Channel credentials encrypted at rest via `core/encryption.py`
- Full CRUD for channels with agent assignment
- `POST /api/v1/tickets/{id}/reply` — sends via real channel
- Inbound email processing: creates ticket or adds message to existing thread
  - Matches by `In-Reply-To` header first (email threading standard)
  - Falls back to cleaned subject match (strips Re:, RV:, Fwd:, etc.)
  - Auto-creates customer if not found
  - Full subject prefix cleaning: Re, Rr, RV, Fwd, FW, SV, AW, TR, 回复, 转发
- Silent refresh token in axios interceptor (queues in-flight requests during refresh)
- Ticket creation modal in frontend
- Reply routing: uses `/reply` for email tickets, `/messages` for manual/notes

**Pending (backlog):**
- Frontend does not auto-refresh when new inbound ticket arrives (polling or websocket needed)
- WhatsApp adapter (deferred)
- Error states in frontend components
- Pagination in ticket/customer lists
- openapi-typescript for auto-generated types
- Admin panel for channel management in frontend (UI exists, backend CRUD exists)
- `process_incoming_message` does not deduplicate yet (external_id check pending)

## Critical Conventions

### Frontend
- `NavLink` with `to="/"` requires `end={true}` — without it, the Dashboard link stays active on every route since all paths start with `/`

### Migrations
- Always use `sa.text('gen_random_uuid()')` for UUID server defaults — never a plain string
- One statement per `op.execute()` — asyncpg rejects multiple statements in one call
- Always review autogenerated migrations before applying — Alembic sometimes adds spurious index drops

### Pydantic v2
- Declare `DATABASE_URL` and `REDIS_URL` as `str`, not `PostgresDsn`/`RedisDsn`
- Pydantic v2 converts DSN types to `Url` objects which break SQLAlchemy and Celery

### Multitenancy
- Never query models directly — always go through `BaseRepository` or use `get_tenant_id()` from context
- `ChannelService` uses raw SQLAlchemy + `get_tenant_id()` directly (not BaseRepository pattern)

### Encryption
- Channel credentials (passwords, tokens) are encrypted before DB storage
- Fields ending in `_password`, `_token`, `_secret` are encrypted automatically
- Encrypted values are prefixed with `enc:` in JSONB

### Testing

```bash
docker compose exec api pytest -v                        # run all tests
docker compose exec api pytest tests/test_auth.py -v     # run single file
```

Test DB is `crm_test` (same Postgres instance). Tables are created once per session via `setup_database` fixture; data is truncated between tests via `clean_db` (autouse).

Key decisions in `conftest.py`:
- `NullPool` — required because `BaseHTTPMiddleware` spawns a new asyncio task per request; a shared connection pool causes greenlet context conflicts with asyncpg
- `_get_test_db` mirrors `get_db` exactly, including `await session.commit()` — without this, flushed data is rolled back when the session closes and subsequent requests see nothing
- `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` — asyncpg does not support `CREATE TYPE IF NOT EXISTS`
- `server_default` on UUID columns must use `sa_text("gen_random_uuid()")`, never a plain string — plain strings get quoted as literals in DDL and fail UUID type validation

### Known Tech Debt
1. TypeScript types are manually maintained — no openapi-typescript yet
2. No error states in frontend components
3. `channel` field in Ticket is still a free string (not FK-validated)
4. `process_incoming_message` does not deduplicate on `message_id` — duplicate emails can create duplicate messages
5. No real-time push for inbound tickets (frontend requires manual refresh)

## Test Data
- Tenant ID: `6a7fb298-bba8-4d52-90d4-157477f57d98` (Empresa Demo)
- Admin credentials: `admin@empresademo.com` / `Admin123!`