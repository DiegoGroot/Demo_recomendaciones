FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY backend/requirements.txt .
# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY backend/ .

# Crear archivo .env si no existe (para Render)
RUN echo "DB_HOST=${DB_HOST:-localhost}\nDB_USER=${DB_USER:-root}\nDB_PASSWORD=${DB_PASSWORD:-}\nDB_NAME=${DB_NAME:-sira}\nDB_PORT=${DB_PORT:-3306}" > .env || true

# Exponer puerto
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Comando para iniciar
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
