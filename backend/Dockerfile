# ══════════════════════════════════════════════════════════════
#  Dockerfile — Backend FastAPI (multi-stage)
#  Stage "base"        → dependencias comunes
#  Stage "development" → hot-reload para docker-compose.dev.yml
#  Stage "production"  → imagen mínima para producción
# ══════════════════════════════════════════════════════════════

# ── Base ──────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# deb.debian.org bloquea descargas de .deb por HTTP (403) en algunas redes
# corporativas; forzamos HTTPS en las fuentes antes de instalar.
RUN sed -i 's#http://deb.debian.org#https://deb.debian.org#g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
      libpq-dev gcc curl libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM base AS development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

RUN useradd -m -u 1001 appuser

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60"]
