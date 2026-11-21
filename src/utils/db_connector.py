# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/db_connector.py
# Description: Conector SQLAlchemy configurado para SQL Server local con auto-creación
# =============================================================================

import sys
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine, Engine, text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.config_loader import get_env_variable


def get_sql_engine(database_override: str | None = None) -> Engine:
    server = get_env_variable("DB_SERVER", default="localhost")
    database = database_override or get_env_variable("DB_NAME", default="JobMarketDB")
    username = get_env_variable("DB_USER", default="sa")
    password = get_env_variable("DB_PASSWORD")
    port = get_env_variable("DB_PORT", default="1433")
    driver = get_env_variable("DB_DRIVER", default="ODBC Driver 18 for SQL Server")

    if "," in server or "\\" in server or ":" in server:
        server_host = server
    else:
        server_host = f"{server},{port}"

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_host};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )

    params = quote_plus(connection_string)

    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    return engine


def ensure_database_exists():
    """
    Se conecta a la base 'master' de SQL Server y crea la base de datos 
    configurada en DB_NAME si es que todavía no existe.
    """
    target_db = get_env_variable("DB_NAME", default="JobMarketDB")
    
    # Conectamos a 'master' para poder ejecutar CREATE DATABASE
    master_engine = get_sql_engine(database_override="master")
    
    try:
        # En SQL Server, CREATE DATABASE no puede ejecutarse dentro de una transacción explícita (autocommit=True)
        with master_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            query = text(f"""
                IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{target_db}')
                BEGIN
                    CREATE DATABASE [{target_db}];
                END
            """)
            conn.execute(query)
            print(f"✅ Base de datos '{target_db}' verificada/creada exitosamente en SQL Server.")
    except Exception as e:
        print(f"❌ Error al asegurar la existencia de la base de datos '{target_db}': {e}")
        raise e


if __name__ == "__main__":
    try:
        ensure_database_exists()
        engine = get_sql_engine()
        with engine.connect() as conn:
            print("✅ Conexión exitosa a SQL Server local.")
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")