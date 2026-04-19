# CRM SaaS

CRM multitenant construido desde cero con FastAPI + React + PostgreSQL. Resuelve gestión de tickets omnicanal para equipos de soporte.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 + asyncpg |
| Frontend | React 19 + Vite + TypeScript + Zustand + Recharts |
| Base de datos | PostgreSQL 16 |
| Migraciones | Alembic |
| Cola de tareas | Celery + Redis |
| Infraestructura | Docker + Docker Compose |
| Testing | Pytest + pytest-asyncio + httpx |

## Levantar el proyecto

```bash
# Backend (5 servicios: api, db, redis, worker, beat)
docker compose up

# Frontend
cd frontend && npm run dev
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

## Estructura

```
crm-saas/
├── backend/
│   ├── app/
│   │   ├── api/          ← endpoints HTTP (auth, tickets, customers, channels, metrics, admin)
│   │   ├── channels/     ← adaptadores de canales (Email, WhatsApp futuro)
│   │   ├── core/         ← config, auth, middleware, encryption, tenant context
│   │   ├── models/       ← SQLAlchemy ORM
│   │   ├── repositories/ ← acceso a datos con filtro de tenant automático
│   │   ├── schemas/      ← Pydantic I/O
│   │   ├── services/     ← lógica de negocio
│   │   └── workers/      ← Celery tasks (polling IMAP, procesamiento inbound)
│   ├── migrations/       ← Alembic
│   └── tests/            ← pytest (41 tests)
└── frontend/
    └── src/
        ├── api/          ← clientes HTTP (axios + interceptores)
        ├── pages/        ← Dashboard, Tickets, Clientes, Reportes, Admin
        ├── components/   ← UI reutilizable (modales, badges, formularios)
        ├── store/        ← Zustand (auth + tenant)
        ├── layouts/      ← MainLayout, AuthLayout
        ├── router/       ← rutas y guards
        └── types/        ← TypeScript types
```

## Módulos implementados

### Backend
| Módulo | Endpoints | Descripción |
|---|---|---|
| Auth | `/auth/login`, `/auth/refresh`, `/auth/me` | JWT + refresh tokens |
| Tickets | `/tickets/*` | CRUD + estados + tipificaciones + mensajes |
| Clientes | `/customers/*` | CRUD + búsqueda + custom fields |
| Canales | `/channels/*` | Email configurado por tenant + asignación de agentes |
| Métricas | `/metrics/*` | Dashboard: resumen, por estado, prioridad, agente, canal, diario |
| Admin | `/admin/*` | CRUD usuarios + configuración de tenant |

### Frontend
| Página | Ruta | Descripción |
|---|---|---|
| Dashboard | `/` | Métricas con gráficas (Recharts) |
| Tickets | `/tickets` | Bandeja con filtros + creación |
| Detalle de ticket | `/tickets/:id` | Hilo de conversación + compositor omnicanal |
| Clientes | `/customers` | Lista con búsqueda |
| Reportes | `/reports` | Por agente, tipificación y canal |
| Admin | `/admin` | Usuarios, canales y cuenta |

## Arquitectura

```
Browser (React)
    ↓ axios (JWT + refresh token silencioso)
FastAPI
    ↓
TenantMiddleware     ← valida JWT, inyecta tenant_id por request
    ↓
Router → Service → Repository → PostgreSQL

── Omnicanalidad (paralelo) ─────────────────────
Celery Beat (60s) → IMAP polling → crea tickets
Agente responde   → SMTP         → email al cliente
```

**Multitenancy:** row-level con `tenant_id` en todas las tablas. Filtro automático en `BaseRepository` — ningún query devuelve datos de otro tenant.

## Fases

| Fase | Estado | Descripción |
|---|---|---|
| Fase 1 | ✅ Completa | Base técnica, autenticación, multitenancy |
| Fase 2 | ✅ Completa | Tickets, clientes, mensajes — backend + frontend |
| Fase 3 | ✅ Completa | Omnicanalidad Email (IMAP + SMTP) + Celery |
| Fase 4 | ✅ Completa | Dashboard, reportería, panel admin, pytest 41/41 |
| Fase 5 | 🔜 Pendiente | WhatsApp, Tremor UI, responsive móvil |

## Variables de entorno

```bash
cp .env.example .env
```

```bash
# .env
POSTGRES_DB=crm_dev
POSTGRES_USER=crm_user
POSTGRES_PASSWORD=tu-password
DATABASE_URL=postgresql+asyncpg://crm_user:tu-password@db:5432/crm_dev
SECRET_KEY=minimo-32-caracteres-cambiar-en-produccion
ENVIRONMENT=development
REDIS_URL=redis://redis:6379/0
```

## Comandos útiles

```bash
# Migraciones
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "descripcion"

# Tests
docker compose exec api pytest -v
docker compose exec api pytest tests/test_auth.py -v

# Logs
docker compose logs -f api
docker compose logs -f worker

# DB directa
docker compose exec db psql -U crm_user -d crm_dev
```

## Seguridad

- Contraseñas hasheadas con bcrypt
- JWT con access token (30 min) + refresh token (7 días) con rotación
- Credenciales de canales encriptadas con Fernet antes de guardar en DB
- Multitenancy estricto — imposible acceder a datos de otro tenant