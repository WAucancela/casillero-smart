# Despliegue — Casilleros Automatizados

## Estructura del proyecto completo

```
casilleros/
├── backend/          ← Código FastAPI (del repo principal)
├── frontend-angular/ ← SPA Angular 22 (AdminLTE); nginx la compila con su Dockerfile
├── postgres/
│   └── init.sql      ← Extensiones y permisos iniciales
├── mosquitto/
│   └── config/
│       ├── mosquitto.conf
│       └── passwd    ← Generado por setup.sh (no en git)
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       ├── default.conf  ← Producción
│       └── dev.conf      ← Desarrollo
├── scripts/
│   ├── setup.sh      ← Instalación inicial
│   ├── dev.sh        ← Comandos de desarrollo
│   └── prod.sh       ← Comandos de producción
├── .env.example      ← Template de variables de entorno
├── .env              ← Variables reales (NO en git)
├── docker-compose.yml
└── docker-compose.dev.yml
```

---

## Requisitos del servidor

| Componente | Mínimo | Recomendado |
|---|---|---|
| CPU | 2 núcleos | 4 núcleos |
| RAM | 4 GB | 8 GB |
| Disco | 20 GB SSD | 50 GB SSD |
| SO | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Docker | 24.x | 26.x |
| Docker Compose | 2.x | 2.x |

---

## Instalación desde cero

### 1. Clonar el repositorio

```bash
git clone https://github.com/tuempresa/casilleros.git
cd casilleros
```

### 2. Verificar que el código esté en su lugar

```bash
# El código del backend debe estar en ./backend/
# El frontend Angular (fuente, sin compilar) debe estar en ./frontend-angular/
ls backend/main.py            # ← debe existir
ls frontend-angular/package.json  # ← debe existir
```

El frontend se compila automáticamente: `docker compose build nginx` corre
`npm ci && npm run build` dentro de `frontend-angular/Dockerfile` y sirve el
resultado con nginx. No hace falta compilarlo ni copiarlo a mano.

### 3. Ejecutar el setup inicial

```bash
bash scripts/setup.sh
```

Este script hace todo automáticamente:
- Genera `.env` con contraseñas seguras aleatorias
- Crea el archivo de contraseñas de Mosquitto
- Construye la imagen del backend
- Ejecuta las migraciones de Alembic
- Carga los datos iniciales (seeds)
- Levanta todos los servicios

### 4. Verificar que todo funciona

```bash
bash scripts/prod.sh status
```

```
Acceder al panel: http://IP_DEL_SERVIDOR
Email:    admin@empresa.com
Password: Admin123!   ← Cambiar inmediatamente
```

---

## Desarrollo local

```bash
# Levantar en modo desarrollo (hot-reload, puertos expuestos)
bash scripts/dev.sh up

# Ver logs del backend en tiempo real
bash scripts/dev.sh logs backend

# Abrir consola de PostgreSQL
bash scripts/dev.sh psql

# Ejecutar tests
bash scripts/dev.sh test

# Ejecutar migraciones nuevas
bash scripts/dev.sh migrate
```

---

## Operación en producción

### Deploy de nueva versión

```bash
bash scripts/prod.sh deploy
```

Esto hace: `git pull` → rebuild del backend → migraciones → restart sin downtime.

### Backup de la base de datos

```bash
bash scripts/prod.sh backup
# Guarda en ./backups/casilleros_YYYYMMDD_HHMMSS.sql.gz
# Se mantienen solo los últimos 7 backups automáticamente
```

### Backup automático con cron

```bash
# Agregar al crontab del servidor (crontab -e):
0 2 * * * cd /ruta/del/proyecto && bash scripts/prod.sh backup >> /var/log/casilleros-backup.log 2>&1
```

### Ver logs

```bash
bash scripts/prod.sh logs backend    # FastAPI
bash scripts/prod.sh logs nginx      # Nginx
bash scripts/prod.sh logs postgres   # PostgreSQL
bash scripts/prod.sh logs mosquitto  # MQTT
```

---

## Arquitectura de red

```
Internet / Red local
        │
        ▼ :80 (HTTP)
   ┌─────────┐
   │  Nginx  │  Sirve build de Angular (SPA) + proxy reverso
   └────┬────┘
        │ red interna: casilleros_backend
   ┌────┴────┐
   │ Backend │  FastAPI (Gunicorn + Uvicorn workers)
   │  :8000  │
   └────┬────┘
        │ red interna
   ┌────┴────────────────────────┐
   │  PostgreSQL  │  Mosquitto   │
   │    :5432     │  :1883       │
   └─────────────────────────────┘
        │ red iot: casilleros_iot
   ┌────┴────────────────────────┐
   │  ZKTeco SenseFace 2A        │  Dispositivos físicos (LAN)
   │  Controladores Hikvision    │  Push ADMS → /iclock/
   └─────────────────────────────┘
```

---

## Variables de entorno importantes

| Variable | Descripción | Ejemplo |
|---|---|---|
| `POSTGRES_PASSWORD` | Contraseña de la BD | Generada automáticamente |
| `SECRET_KEY` | Clave para firmar JWT | Generada automáticamente |
| `MQTT_PASSWORD` | Contraseña del broker | Generada automáticamente |
| `BIOMETRIC_ENCRYPTION_KEY` | Clave Fernet para vectores | Generada automáticamente |
| `SMTP_USER` | Email para notificaciones | tu@empresa.com |
| `SMTP_PASSWORD` | App password del email | Manual |
| `ALLOWED_ORIGINS` | CORS | URL del frontend |

---

## Solución de problemas

### El backend no arranca
```bash
bash scripts/dev.sh logs backend
# Si falta la BD:
bash scripts/dev.sh migrate
```

### El login falla con "Sin conexión al servidor"
```bash
# Verificar que nginx proxy pasa a backend:
curl http://localhost/api/health
# Si falla, revisar logs de nginx:
bash scripts/dev.sh logs nginx
```

### Mosquitto no acepta conexiones
```bash
# Verificar que el archivo de contraseñas existe:
ls mosquitto/config/passwd
# Si no existe, regenerar:
bash scripts/setup.sh  # Solo regenera lo que falta
```

### El ZKTeco no envía eventos
```bash
# Verificar que el dispositivo alcanza el servidor:
# En el SenseFace 2A: Menú → Comm → Cloud Server
# Server Address: IP_DEL_SERVIDOR
# Server Port: 80   ← nginx recibe en 80 y hace proxy a /iclock/
```

### Restaurar backup
```bash
bash scripts/prod.sh restore backups/casilleros_20260310_020000.sql.gz
```
