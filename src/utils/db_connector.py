# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/db_connector.py
# Description: Conector SQLAlchemy optimizado para Azure SQL Database
# =============================================================================

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine, Engine

# Garantizar que ROOT_DIR esté en sys.path para importaciones relativas/absolutas
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Carga de variables de entorno mediante el cargador centralizado
from src.utils.config_loader import get_env_variable


def get_sql_engine() -> Engine:
    """Crea un engine de SQLAlchemy configurado optimizadamente para Azure SQL Database."""
    server = get_env_variable("DB_SERVER")
    database = get_env_variable("DB_NAME")
    username = get_env_variable("DB_USER")
    password = get_env_variable("DB_PASSWORD")
    port = get_env_variable("DB_PORT", default="1433")
    driver = get_env_variable("DB_DRIVER", default="ODBC Driver 18 for SQL Server")

    # En Azure SQL el servidor suele terminar en .database.windows.net
    # Si solo pasas el hostname (ej. mi-servidor), nos aseguramos de que no falle
    server_host = server if "," in server or ":" in server else f"{server},{port}"

    # Construcción de la cadena de conexión ODBC obligatoria para Azure SQL
    # Encrypt=yes es requerido obligatoriamente por Azure SQL.
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server_host};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"  # Cambiar a 'no' en entornos de producción con CA certificada
        f"Connection Timeout=60;"
    )

    params = quote_plus(connection_string)

    # Engine configurado con fast_executemany y pool_pre_ping para reconexiones automáticas
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True,
        pool_pre_ping=True,  # Verifica salud de la conexión antes de ejecutar SQL
        pool_size=10,
        max_overflow=20,
    )

    return engine


if __name__ == "__main__":
    try:
        engine = get_sql_engine()
        with engine.connect() as conn:
            print("✅ Conexión exitosa a Azure SQL Database.")
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")