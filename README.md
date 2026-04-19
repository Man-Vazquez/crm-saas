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
# Backend
docker compose up

# Frontend
cd frontend && npm run dev
```

Backend: `http://localhost:8000`  
Frontend: `http://localhost:5173`  
Docs API: `http://localhost:8000/docs`

## Estructura

crm-saas/
├── backend/
│   ├── app/
│   │   ├── api/          ← endpoints HTTP
│   │   ├── core/         ← config, auth, middleware
│   │   ├── models/       ← SQLAlchemy ORM
│   │   ├── repositories/ ← acceso a datos
│   │   ├── schemas/      ← Pydantic I/O
│   │   └── services/     ← lógica de negocio
│   └── migrations/       ← Alembic
└── frontend/
└── src/
├── api/          ← clientes HTTP
├── pages/        ← vistas
├── components/   ← UI reutilizable
├── store/        ← Zustand
├── layouts/      ← estructuras de página
├── router/       ← rutas y guards
└── types/        ← TypeScript types

## Fases

| Fase | Estado | Descripción |
|---|---|---|
| Fase 1 | ✅ Completa | Base técnica, autenticación, multitenancy |
| Fase 2 | ✅ Completa | Tickets, clientes, mensajes — backend + frontend |
| Fase 3 | 🔜 Pendiente | Omnicanalidad — Email + WhatsApp |
| Fase 4 | 🔜 Pendiente | Dashboard, reportería, panel admin |

## Variables de entorno

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