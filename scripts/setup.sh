#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  setup.sh — Configuración inicial del sistema (ejecutar 1 vez)
#  Uso: bash scripts/setup.sh
# ══════════════════════════════════════════════════════════════
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Casilleros Automatizados — Setup Inicial    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Verificar dependencias ─────────────────────────────────
info "Verificando dependencias..."
command -v docker        >/dev/null || error "Docker no instalado. Ver https://docs.docker.com/engine/install/"
command -v docker-compose >/dev/null 2>&1 || \
  docker compose version >/dev/null 2>&1   || error "Docker Compose no instalado."
success "Docker $(docker --version | awk '{print $3}' | tr -d ',')"

# ── 2. Crear .env si no existe ────────────────────────────────
if [ ! -f .env ]; then
  info "Creando .env desde .env.example..."
  cp .env.example .env

  # Generar claves seguras automáticamente
  PG_PASS=$(openssl rand -base64 32 | tr -d '=+/' | cut -c1-32)
  JWT_KEY=$(openssl rand -base64 48 | tr -d '=+/' | cut -c1-48)
  MQTT_PASS=$(openssl rand -base64 16 | tr -d '=+/' | cut -c1-16)
  FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "GENERAR_MANUALMENTE")

  sed -i "s/CAMBIA_ESTO_password_segura_2026/$PG_PASS/"    .env
  sed -i "s/CAMBIA_ESTO_clave_jwt_minimo_32_caracteres_random/$JWT_KEY/" .env
  sed -i "s/CAMBIA_ESTO_mqtt_password/$MQTT_PASS/"          .env
  sed -i "s/CAMBIA_ESTO_fernet_key_base64/$FERNET_KEY/"     .env

  success ".env creado con contraseñas generadas automáticamente"
  warn "Revisa .env y actualiza SMTP_USER y SMTP_PASSWORD antes de continuar"
else
  success ".env ya existe"
fi

# ── 3. Crear archivo de contraseñas MQTT ─────────────────────
info "Configurando contraseñas MQTT..."
if [ ! -f mosquitto/config/passwd ]; then
  source .env
  # Generar el hash con mosquitto_passwd dentro de un contenedor temporal
  docker run --rm eclipse-mosquitto:2.0 \
    sh -c "mosquitto_passwd -b -c /tmp/passwd ${MQTT_USER:-casilleros} ${MQTT_PASSWORD} && cat /tmp/passwd" \
    > mosquitto/config/passwd 2>/dev/null
  success "mosquitto/config/passwd creado"
else
  success "mosquitto/config/passwd ya existe"
fi

# ── 4. Crear directorios de datos ─────────────────────────────
info "Creando directorios de datos..."
mkdir -p mosquitto/{data,log} postgres
success "Directorios listos"

# ── 5. Verificar que el código del backend está presente ──────
if [ ! -f backend/main.py ]; then
  warn "No se encontró backend/main.py. Asegúrate de colocar el código del backend en ./backend/"
fi

if [ ! -f frontend/login.html ]; then
  warn "No se encontró frontend/login.html. Asegúrate de colocar el frontend en ./frontend/"
fi

# ── 6. Build de imágenes ──────────────────────────────────────
info "Construyendo imágenes Docker..."
docker compose build --no-cache backend
success "Imagen del backend construida"

# ── 7. Levantar servicios base ────────────────────────────────
info "Levantando PostgreSQL y Mosquitto..."
docker compose up -d postgres mosquitto
sleep 5

# ── 8. Ejecutar migraciones ───────────────────────────────────
info "Ejecutando migraciones de base de datos..."
docker compose run --rm migrate
success "Migraciones aplicadas"

# ── 9. Cargar datos iniciales (seeds) ────────────────────────
info "Cargando datos iniciales..."
docker compose run --rm backend python database/seeds/seed_data.py 2>/dev/null || \
  warn "Seeds no ejecutados (ejecutar manualmente: docker compose run --rm backend python database/seeds/seed_data.py)"

# ── 10. Levantar todo ─────────────────────────────────────────
info "Levantando todos los servicios..."
docker compose up -d

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Sistema instalado correctamente           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Panel de administración:${NC} http://localhost"
echo -e "  ${BLUE}API (Swagger):${NC}           http://localhost/docs"
echo -e "  ${BLUE}Backend directo:${NC}         (solo en dev) http://localhost:8000"
echo ""
echo -e "  ${YELLOW}Credenciales por defecto:${NC}"
echo -e "  Email:    admin@empresa.com"
echo -e "  Password: Admin123!  ← CAMBIAR inmediatamente en producción"
echo ""
