#!/bin/bash

case "$1" in
  create)
    if [ -z "$2" ]; then
      echo "Error: Debes proporcionar un mensaje"
      echo "Uso: ./migrate.sh create 'mensaje de la migración'"
      exit 1
    fi
    alembic revision --autogenerate -m "$2"
    ;;
  up)
    alembic upgrade head
    ;;
  down)
    alembic downgrade -1
    ;;
  current)
    alembic current
    ;;
  history)
    alembic history --verbose
    ;;
  seed)
    python seed_rols_wf.py
    python seed_user.py
    ;;
  reset)
    echo "⚠️  ADVERTENCIA: Esto eliminará todas las tablas y recreará la base de datos"
    read -p "¿Estás seguro? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      alembic downgrade base
      alembic upgrade head
      python seed_rols_wf.py
      python seed_user.py
      echo "✅ Base de datos reseteada"
    else
      echo "Operación cancelada"
    fi
    ;;
  *)
    echo "SGT_v1 - Herramienta de Migraciones"
    echo ""
    echo "Uso: $0 {create|up|down|current|history|seed|reset}"
    echo ""
    echo "Comandos:"
    echo "  create 'mensaje'  - Crear nueva migración"
    echo "  up                - Aplicar migraciones pendientes"
    echo "  down              - Revertir última migración"
    echo "  current           - Ver estado actual"
    echo "  history           - Ver historial de migraciones"
    echo "  seed              - Ejecutar seeds"
    echo "  reset             - Resetear base de datos (PELIGROSO)"
    echo ""
    echo "Ejemplos:"
    echo "  $0 create 'Agregar campo descripción a tasks'"
    echo "  $0 up"
    echo "  $0 seed"
    exit 1
    ;;
esac