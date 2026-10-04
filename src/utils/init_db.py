# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/init_db.py
# Description: Inicialización idempotente y verificación del Warehouse.
# =============================================================================

import os
import re
import sys
import logging
from pathlib import Path
from sqlalchemy import text

# Configurar el PATH para garantizar acceso a src/ de forma portable
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Carga de variables de entorno mediante el cargador centralizado
from src.utils.config_loader import get_env_variable
from src.utils.db_connector import get_sql_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def is_warehouse_initialized() -> bool:
    """
    Comprueba en la base de datos activa si la tabla de hechos existe.
    """
    check_query = text("""
        SELECT COUNT(1)
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE LOWER(s.name) = 'warehouse'
          AND LOWER(t.name) = 'fact_observacion_oferta';
    """)

    try:
        engine = get_sql_engine()
        with engine.connect() as conn:
            result = conn.execute(check_query).scalar()
            return bool(result and result > 0)
    except Exception as e:
        logger.error(f"Error al verificar la infraestructura: {e}")
        return False


def execute_sql_file(file_path: Path, engine) -> None:
    """
    Lee un archivo .sql, separa por la instrucción 'GO' y ejecuta los bloques.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo SQL no existe: {file_path}")

    logger.info(f"Ejecutando script SQL: {file_path.relative_to(ROOT_DIR)}")

    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    batches = [
        batch.strip() 
        for batch in re.split(r'^\s*GO\s*$', sql_content, flags=re.MULTILINE | re.IGNORECASE) 
        if batch.strip()
    ]

    with engine.connect() as conn:
        for idx, batch in enumerate(batches, start=1):
            try:
                conn.execute(text(batch))
                if getattr(conn, "commit", None):
                    conn.commit()
            except Exception as e:
                logger.error(f"Error al ejecutar lote #{idx} en {file_path.name}: {e}")
                raise e

    logger.info(f"Script {file_path.name} ejecutado con éxito.")


def initialize_warehouse(force: bool = False) -> None:
    if not force and is_warehouse_initialized():
        logger.info("El Data Warehouse ya está inicializado. Omitiendo DDL...")
        return

    logger.info("Inicializando infraestructura del Data Warehouse...")

    sql_dir = ROOT_DIR / "sql" / "warehouse"
    script_01 = sql_dir / "01_database_setup.sql"
    script_02 = sql_dir / "02_star_schema.sql"

    try:
        app_engine = get_sql_engine()

        execute_sql_file(script_01, app_engine)
        execute_sql_file(script_02, app_engine)

        logger.info("Estructura del Data Warehouse desplegada exitosamente.")

    except Exception as e:
        logger.critical(f"Fallo durante la inicialización del Data Warehouse: {e}")
        sys.exit(1)


if __name__ == "__main__":
    initialize_warehouse()