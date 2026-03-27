#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  prod.sh — Comandos para producción
#  Uso: bash scripts/prod.sh [deploy|rollback|backup|logs|status]
# ══════════════════════════════════════════════════════════════
set -euo pipefail
COMPOSE="docker compose"
BACKUP_DIR="./backups"

case "${1:-help}" in
  deploy)
    echo "🚀 Desplegando nueva versión..."
    git pull --rebase
    $COMPOSE build --no-cache backend
    $COMPOSE run --rm migrate
    $COMPOSE up -d --no-deps backend nginx
    echo "✓ Deploy completado"
    $COMPOSE ps
    ;;
  restart)
    echo "♻ Reiniciando ${2:-backend}..."
    $COMPOSE restart "${2:-backend}"
    ;;
  logs)
    $COMPOSE logs -f --tail=200 "${2:-backend}"
    ;;
  status)
    echo "═══ Contenedores ═══"
    $COMPOSE ps
    echo ""
    echo "═══ Uso de recursos ═══"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
      casilleros-backend casilleros-postgres casilleros-mosquitto casilleros-nginx 2>/dev/null || true
    ;;
  backup)
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/casilleros_${TIMESTAMP}.sql.gz"
    echo "💾 Backup de base de datos → $BACKUP_FILE"
    source .env
    docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_FILE"
    echo "✓ Backup guardado: $(du -sh $BACKUP_FILE | cut -f1)"
    # Mantener solo los últimos 7 backups
    ls -t "${BACKUP_DIR}"/*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm
    echo "✓ Backups anteriores limpiados (se mantienen los últimos 7)"
    ;;
  restore)
    [ -z "${2:-}" ] && echo "Uso: prod.sh restore <archivo.sql.gz>" && exit 1
    echo "⚠ Esto restaurará la BD desde $2. ¿Continuar? [y/N]"
    read -r confirm
    [ "$confirm" = "y" ] || exit 0
    source .env
    gunzip -c "$2" | docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"
    echo "✓ Base de datos restaurada"
    ;;
  *)
    echo "Uso: bash scripts/prod.sh [comando]"
    echo ""
    echo "  deploy        Pull + build + migrate + restart backend/nginx"
    echo "  restart [svc] Reiniciar un servicio"
    echo "  logs [svc]    Ver logs en tiempo real"
    echo "  status        Estado de contenedores + uso de recursos"
    echo "  backup        Backup de PostgreSQL comprimido"
    echo "  restore <f>   Restaurar backup"
    ;;
esac
