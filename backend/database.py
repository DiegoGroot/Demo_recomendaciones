import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Credenciales ─────────────────────────────────────────────────────────────
# En Render define estas variables de entorno en el dashboard.
# Para local, copia .env.example → .env y llena los valores.
# IMPORTANTE: Nunca incluyas credenciales en el código. Use variables de entorno.

def _get_required_env(key: str, description: str) -> str:
    """Obtiene una variable de entorno requerida."""
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"Variable de entorno requerida '{key}' no configurada. {description}"
        )
    return value

# Validar variables de entorno requeridas
try:
    DB_HOST     = _get_required_env("DB_HOST", "Host de la base de datos")
    DB_USER     = _get_required_env("DB_USER", "Usuario de la base de datos")
    DB_PASSWORD = _get_required_env("DB_PASSWORD", "Contraseña de la base de datos")
    DB_NAME     = _get_required_env("DB_NAME", "Nombre de la base de datos")
except ValueError as e:
    print(f"⚠️  ERROR DE CONFIGURACIÓN: {e}")
    print("Por favor, configura las variables de entorno en .env o en el dashboard de Render")
    raise

DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_SSL_CA   = os.getenv("DB_SSL_CA", None)

# ─── Schema ───────────────────────────────────────────────────────────────────
# Si tus tablas están en el schema "sira" dentro de defaultdb, este valor es "sira".
# Si están directamente en defaultdb (sin schema), ponlo vacío: DB_SCHEMA = ""
DB_SCHEMA = os.getenv("DB_SCHEMA", "sira")

def _build_config():
    cfg = {
        "host":         DB_HOST,
        "user":         DB_USER,
        "password":     DB_PASSWORD,
        "database":     DB_NAME,
        "port":         DB_PORT,
        "ssl_disabled": False,
        "connection_timeout": 30,
        "autocommit":   False,
    }
    if DB_SSL_CA:
        cfg["ssl_ca"] = DB_SSL_CA
    return cfg


def get_db():
    """Dependencia FastAPI: abre una conexión y la cierra al terminar el request."""
    db = mysql.connector.connect(**_build_config())
    # Si las tablas están en el schema "sira", lo seleccionamos.
    if DB_SCHEMA:
        db.cmd_query(f"USE `{DB_SCHEMA}`")
    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass
