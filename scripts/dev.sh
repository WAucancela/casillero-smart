#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  dev.sh — Comandos rápidos para desarrollo
#  Uso: bash scripts/dev.sh [up|down|logs|restart|shell|psql|reset]
# ══════════════════════════════════════════════════════════════
set -euo pipefail
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.dev.yml"

case "${1:-help}" in
  up)
    echo "▶ Levantando entorno de desarrollo..."
    $COMPOSE up -d
    echo "✓ Listo en http://localhost  |  API: http://localhost:8000/docs"
    ;;
  down)
    echo "⏹ Deteniendo servicios..."
    $COMPOSE down
    ;;
  logs)
    $COMPOSE logs -f --tail=100 "${2:-backend}"
    ;;
  restart)
    echo "♻ Reiniciando ${2:-backend}..."
    $COMPOSE restart "${2:-backend}"
    ;;
  build)
    echo "🔨 Rebuilding ${2:-backend}..."
    $COMPOSE build "${2:-backend}"
    $COMPOSE up -d "${2:-backend}"
    ;;
  shell)
    echo "🐚 Shell en contenedor ${2:-backend}..."
    $COMPOSE exec "${2:-backend}" /bin/bash
    ;;
  psql)
    echo "🐘 Conectando a PostgreSQL..."
    $COMPOSE exec postgres psql -U casilleros_user -d casilleros
    ;;
  migrate)
    echo "🔄 Ejecutando migraciones..."
    $COMPOSE run --rm migrate
    ;;
  seed)
    echo "🌱 Cargando datos de prueba..."
    $COMPOSE run --rm backend python database/seeds/seed_data.py
    ;;
  test)
    echo "🧪 Ejecutando tests..."
    $COMPOSE run --rm backend pytest tests/ -v "${@:2}"
    ;;
  reset)
    echo "⚠ RESET: esto borrará todos los datos. ¿Continuar? [y/N]"
    read -r confirm
    [ "$confirm" = "y" ] || exit 0
    $COMPOSE down -v
    echo "✓ Volúmenes eliminados. Ejecuta: bash scripts/setup.sh"
    ;;
  status)
    $COMPOSE ps
    ;;
  *)
    echo "Uso: bash scripts/dev.sh [comando]"
    echo ""
    echo "  up          Levantar todos los servicios en modo desarrollo"
    echo "  down        Detener todos los servicios"
    echo "  logs [svc]  Ver logs (default: backend)"
    echo "  restart [svc] Reiniciar servicio"
    echo "  build [svc] Reconstruir imagen"
    echo "  shell [svc] Abrir shell en contenedor"
    echo "  psql        Abrir consola PostgreSQL"
    echo "  migrate     Ejecutar migraciones Alembic"
    echo "  seed        Cargar datos de prueba"
    echo "  test        Ejecutar suite de tests"
    echo "  reset       ⚠ Eliminar todos los datos (volúmenes)"
    echo "  status      Ver estado de los contenedores"
    ;;
esac
