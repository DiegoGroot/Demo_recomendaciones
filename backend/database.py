import mysql.connector
from mysql.connector import pooling
import os

# ─── Credenciales ────────────────────────────────────────────────────────────
# En Render define estas variables de entorno en el dashboard del servicio.
# Para pruebas locales puedes dejar los valores por defecto aquí,
# pero NO subas contraseñas reales a Git.

db_config = {
    "host":     os.getenv("DB_HOST",     "mysql-sira-dieguitogroot-mysql.c.aivencloud.com"),
    "user":     os.getenv("DB_USER",     "avnadmin"),
    "password": os.getenv("DB_PASSWORD", "AVNS_pCkFUvAZSqrrPy_Bmq4"),
    "database": os.getenv("DB_NAME",     "defaultdb"),
    "port":     int(os.getenv("DB_PORT", "27373")),
    # Aiven EXIGE SSL — no lo desactives
    "ssl_disabled": False,
}

# CA certificate: en Render sube el archivo o pega la ruta en DB_SSL_CA.
# Si no lo tienes configurado, Aiven igual conecta con ssl_disabled=False
# (verifica el certificado del servidor usando los CAs del sistema).
_ssl_ca = os.getenv("DB_SSL_CA", None)
if _ssl_ca:
    db_config["ssl_ca"] = _ssl_ca

# ─── Pool ─────────────────────────────────────────────────────────────────────
connection_pool = None


def get_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="sira_pool",
                pool_size=10,          # Aiven free tier: máx ~10 conexiones
                **db_config,
            )
            print("✅ Pool de conexiones creado correctamente")
        except Exception as e:
            print(f"❌ Error creando el pool: {e}")
            raise e
    return connection_pool


def get_db():
    db = mysql.connector.connect(**db_config)
    try:
        yield db
    finally:
        db.close()