# backend/Dockerfile

# ── Etapa base ────────────────────────────────────────────────────────
# python:3.12-slim es Debian con solo lo mínimo para correr Python.
# Evitamos la imagen completa (700MB+) y la alpine (problemas con asyncpg).
FROM python:3.12-slim

# Variables de entorno que controlan el comportamiento de Python en Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── Directorio de trabajo ─────────────────────────────────────────────
# Todos los comandos siguientes se ejecutan desde /app
WORKDIR /app

# ── Dependencias del sistema ──────────────────────────────────────────
# asyncpg necesita un compilador C para instalarse.
# Instalamos, usamos, y luego limpiamos en el mismo RUN para no inflar la imagen.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencias Python ───────────────────────────────────────────────
# PRIMERO copiamos solo requirements.txt (no el código).
# Si el código cambia pero requirements.txt no, Docker usa el caché de esta capa.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ── Código de la aplicación ───────────────────────────────────────────
# Esto se copia al final porque cambia frecuentemente.
# En desarrollo esto no importa tanto (usamos volúmenes),
# pero en producción esta separación hace los builds mucho más rápidos.
COPY . .

# ── Puerto que expone el contenedor ──────────────────────────────────
# Solo documentativo. El mapeo real está en docker-compose.yml.
EXPOSE 8000

# ── Comando por defecto ───────────────────────────────────────────────
# En desarrollo docker-compose.yml lo sobreescribe con --reload.
# En producción este CMD es el que se usa.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]