# CRM SaaS

CRM multitenant construido desde cero con FastAPI + React + PostgreSQL.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 + asyncpg |
| Frontend | React + Vite + TypeScript + Zustand |
| Base de datos | PostgreSQL 16 |
| Migraciones | Alembic |
| Infraestructura | Docker + Docker Compose |

## Levantar el proyecto

```bash
docker compose up
```

API disponible en `http://localhost:8000`  
Documentación en `http://localhost:8000/docs`

## Estructura
crm-saas/
├── backend/        ← FastAPI
│   ├── app/
│   │   ├── api/        ← endpoints HTTP
│   │   ├── core/       ← config, auth, middleware
│   │   ├── models/     ← SQLAlchemy ORM
│   │   ├── repositories/ ← acceso a datos
│   │   ├── schemas/    ← Pydantic I/O
│   │   └── services/   ← lógica de negocio
│   └── migrations/   ← Alembic
└── frontend/       ← React (Fase 2)

## Fases

| Fase | Estado | Descripción |
|---|---|---|
| Fase 1 | ✅ Completa | Base técnica, autenticación, multitenancy |
| Fase 2 | ✅ Completa | Tickets, clientes, mensajes, tipificaciones |
| Fase 3 | 🔜 Pendiente | Omnicanalidad — Email + WhatsApp |
| Fase 4 | 🔜 Pendiente | Dashboard, reportería, panel admin |

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```bash
cp .env.example .env
```

## Comandos útiles

```bash
# Migraciones
docker compose exec api alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "descripcion"

# Logs
docker compose logs -f api
```