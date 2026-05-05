#!/bin/bash

# Script para configurar la base de datos SIRA
# Uso: ./setup_database.sh <contraseña_mysql>

if [ -z "$1" ]; then
  echo "Uso: $0 <contraseña_mysql>"
  echo "Ejemplo: $0 root123"
  exit 1
fi

MYSQL_PASSWORD=$1

echo "================================"
echo "Configurando BD SIRA..."
echo "================================"

# Crear base de datos y cargar schema
mysql -u root -p"$MYSQL_PASSWORD" < schema.sql

if [ $? -eq 0 ]; then
  echo "✅ Base de datos configurada exitosamente"
else
  echo "❌ Error al configurar la base de datos"
  exit 1
fi

echo ""
echo "✅ BD SIRA lista para usar"
echo ""
echo "Datos de prueba:"
echo "- Admin: admin@sira.com / admin123"
echo "- Tutor: tutor@sira.com / tutor123"
echo "- Maestro: maestro@sira.com / maestro123"
echo "- Estudiante: estudiante@sira.com / estudiante123"
