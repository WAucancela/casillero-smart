# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Casillero Smart** is a full-stack IoT locker management system. It integrates ZKTeco SenseFace 2A facial recognition hardware with software-controlled smart lockers, connected via MQTT. Administrators manage users, locker assignments, and access schedules through a web dashboard.

## Common Commands

### Development

```bash
# First-time setup (generates secrets, builds images, runs migrations, seeds data)
bash scripts/setup.sh

# Start with hot-reload
bash scripts/dev.sh up

# Stream backend logs
bash scripts/dev.sh logs backend

# Run tests
bash scripts/dev.sh test

# Apply Alembic migrations
bash scripts/dev.sh migrate

# Access PostgreSQL shell
bash scripts/dev.sh psql

# Stop all services
bash scripts/dev.sh down
```

### Production

```bash
# Full deploy: git pull → rebuild → migrate → restart
bash scripts/prod.sh deploy

# View logs for a service (backend|postgres|nginx|mosquitto)
bash scripts/prod.sh logs backend

# Backup database
bash scripts/prod.sh backup

# Restore a backup
bash scripts/prod.sh restore backups/casilleros_YYYYMMDD_HHMMSS.sql.gz

# Service status
bash scripts/prod.sh status
```

### Direct Docker

```bash
# Dev mode with file watching
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production build (no cache)
docker compose build --no-cache

# Shell into backend container
docker compose exec backend bash
```

## Architecture

### Services

| Service | Tech | Purpose |
|---------|------|---------|
| `backend` | FastAPI + Gunicorn/Uvicorn | REST API, business logic, hardware control |
| `postgres` | PostgreSQL 16 | Primary data store |
| `mosquitto` | Eclipse Mosquitto 2.0 | MQTT broker for locker hardware |
| `nginx` | Nginx 1.25 | Reverse proxy + static frontend serving |

Two Docker networks: `casilleros_backend` (internal services) and `casilleros_iot` (MQTT/hardware).

### Backend Layer Structure (`backend/`)

```
api/routes/         → HTTP endpoints (auth, usuarios, casilleros, accesos, reportes, hardware, admin)
application/        → Use cases / business logic (crear_usuario, asignar_casillero, validar_acceso, etc.)
domain/entities/    → Domain models (Usuario, Casillero, AccesoLog)
infrastructure/
  database/         → SQLAlchemy async repositories
  biometria/        → DeepFace facial recognition + Fernet-encrypted vector storage
  hardware/         → MQTT client + locker control (cerradura_service)
  zkteco/           → ADMS Push Protocol webhook handler (POST /iclock/cdata)
  notificaciones/   → SMTP email alerts
config/             → Settings (Pydantic BaseSettings) and logging config
main.py             → FastAPI app entry point
```

### Access Flow (Happy Path)

1. ZKTeco device detects a face → pushes `POST /iclock/cdata` (ADMS protocol)
2. `zkteco/adms_router.py` parses the event, resolves user by PIN
3. `application/validar_acceso` checks rules: user status, schedule, locker assignment
4. On approval: `infrastructure/hardware/cerradura_service` publishes MQTT command → locker opens
5. Event logged to `accesos_log` table

### Database Schema (key tables)

- `administradores` — web panel users (roles: superadmin, admin, viewer)
- `usuarios` — employees with locker access
- `biometria` — Fernet-encrypted facial vectors
- `casilleros` — individual locker units
- `controladores` — physical lock controllers
- `terminales` — ZKTeco devices
- `accesos_log` — full access attempt history
- `horarios_acceso` — time-based access windows

Migrations are managed with **Alembic** (config: `database/alembic.ini`, migrations: `database/migrations/`).

### Frontend

Static HTML/CSS/JS using AdminLTE template, served directly by Nginx. No build step required — files in `frontend/` are served as-is.

## Environment Configuration

Copy `.env.example` → `.env`. `setup.sh` auto-generates all secrets except SMTP credentials.

Key variables:
- `SECRET_KEY` / `ALGORITHM` / `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT config
- `MQTT_BROKER_HOST` / `MQTT_USER` / `MQTT_PASSWORD` — MQTT broker
- `BIOMETRIC_CONFIDENCE_THRESHOLD` / `BIOMETRIC_ENCRYPTION_KEY` — facial recognition
- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` — email notifications (Gmail App Password)

## Default Credentials

**Admin panel**: `admin@empresa.com` / `Admin123!` (change immediately in production)

## API Documentation

Swagger UI available at `http://localhost/docs` when running.
