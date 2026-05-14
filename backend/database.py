import mysql.connector
import os

# ─── Credenciales ─────────────────────────────────────────────────────────────
# En Render define estas variables de entorno en el dashboard.
# Para local, copia .env.example → .env y llena los valores.

DB_HOST     = os.getenv("DB_HOST",     "mysql-sira-dieguitogroot-mysql.c.aivencloud.com")
DB_USER     = os.getenv("DB_USER",     "avnadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "AVNS_pCkFUvAZSqrrPy_Bmq4")
DB_NAME     = os.getenv("DB_NAME",     "defaultdb")
DB_PORT     = int(os.getenv("DB_PORT", "27373"))
DB_SSL_CA   = os.getenv("DB_SSL_CA",   None)

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