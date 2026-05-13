import mysql.connector
from mysql.connector import pooling
import os

db_config = {
    "host": "localhost",
    "user": "diego_user",
    "password": "Diego123*",
    "database": "sira",
    "port": 3306,
}

connection_pool = None

def get_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="sira_pool",
                pool_size=20,
                **db_config
            )
        except Exception as e:
            print(f"Error creando el pool: {e}")
            raise e
    return connection_pool

def get_db():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "diego_user"),
        password=os.getenv("DB_PASSWORD", "Diego123*"),
        database=os.getenv("DB_NAME", "sira"),
        port=os.getenv("DB_PORT", 3306)
    )
    try:
        yield db
    finally:
        db.close()