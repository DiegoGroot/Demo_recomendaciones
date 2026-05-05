#!/bin/bash

# Script rápido para iniciar todo el proyecto

echo "======================================"
echo "SIRA - Sistema de Recomendaciones"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar si MySQL está corriendo
echo "Verificando MySQL..."
if ! pgrep -x "mysqld" > /dev/null; then
  echo -e "${YELLOW}MySQL no está en ejecución. Inténtelo con:${NC}"
  echo "sudo service mysql start"
  exit 1
fi
echo -e "${GREEN}✓ MySQL corriendo${NC}"

# Pedir contraseña si no existe archivo .dbpass
if [ ! -f .dbpass ]; then
  echo ""
  echo "Primera vez que inicia el proyecto."
  read -sp "Ingrese contraseña de MySQL (root): " DB_PASS
  echo "$DB_PASS" > .dbpass
  chmod 600 .dbpass
  echo ""
  echo "Configurando base de datos..."
  bash setup_database.sh "$DB_PASS" || exit 1
fi

DB_PASS=$(cat .dbpass)

echo ""
echo "======================================"
echo "Opciones disponibles:"
echo "======================================"
echo ""
echo "1) Iniciar Backend (FastAPI)"
echo "2) Iniciar Frontend (Flutter Web)"
echo "3) Iniciar Backend + Frontend"
echo "4) Salir"
echo ""
read -p "Seleccione opción (1-4): " choice

case $choice in
  1)
    echo -e "${GREEN}Iniciando Backend...${NC}"
    cd backend
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ;;
  2)
    echo -e "${GREEN}Iniciando Flutter Web...${NC}"
    cd flutter_application
    flutter run -d web
    ;;
  3)
    echo -e "${GREEN}Iniciando Backend...${NC}"
    cd backend
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    sleep 2
    cd ../flutter_application
    echo -e "${GREEN}Iniciando Flutter Web...${NC}"
    flutter run -d web
    kill $BACKEND_PID
    ;;
  4)
    echo "Saliendo..."
    exit 0
    ;;
  *)
    echo "Opción inválida"
    exit 1
    ;;
esac
