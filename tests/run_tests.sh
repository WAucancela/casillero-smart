#!/bin/bash
# run_tests.sh — Ejecuta todas las pruebas de la capa API

echo "══════════════════════════════════════════"
echo "  Pruebas Unitarias — Capa API"
echo "  Casilleros Automatizados v1.0"
echo "══════════════════════════════════════════"

# Instalar dependencias de test si no existen
pip install -q -r requirements-test.txt --break-system-packages

# Ir al directorio del backend
cd ../backend

# Ejecutar todos los tests con salida verbose
pytest ../tests/ -v --tb=short

echo ""
echo "══════════════════════════════════════════"
echo "  Ejecución completada"
echo "══════════════════════════════════════════"
