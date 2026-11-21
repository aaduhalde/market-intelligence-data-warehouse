# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/init_db.py
# Description: Verificación idempotente y despliegue inicial del Data Warehouse
#              (esquemas, dimensiones y tablas de hechos) a partir de los
#              scripts SQL en sql/warehouse/. Delega la conexión y creación
#              de la base de datos a src/utils/db_connector.py.
# =============================================================================

import re
import sys
import logging
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Configurar el PATH para garantizar acceso a src/ de forma portable
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.db_connector import ensure_database_exists, get_sql_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def is_warehouse_initialized() -> bool:
    """
    Comprueba en la base de datos activa si la tabla de hechos ya existe.
    """
    check_query = text("""
        SELECT COUNT(1)
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        WHERE LOWER(s.name) = 'warehouse'
          AND LOWER(t.name) = 'fact_observacion_oferta';
    """)

    engine = get_sql_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(check_query).scalar()
            return bool(result and result > 0)
    except OperationalError:
        return False
    except Exception as e:
        logger.error(f"Error al verificar la infraestructura: {e}")
        return False
    finally:
        engine.dispose()


def execute_sql_file(file_path: Path, engine) -> None:
    """
    Lee un archivo .sql, separa los lotes por la instrucción 'GO' y los ejecuta.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo SQL no existe: {file_path}")

    logger.info(f"Ejecutando script SQL: {file_path.relative_to(ROOT_DIR)}")

    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    batches = [
        batch.strip()
        for batch in re.split(r"^\s*GO\s*$", sql_content, flags=re.MULTILINE | re.IGNORECASE)
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
    """
    Asegura la existencia de la base de datos y despliega los scripts DDL del
    Data Warehouse si aún no se ha inicializado (o si force=True).
    """
    logger.info("Verificando base de datos e infraestructura del Data Warehouse...")

    try:
        # 1. Asegurar que la base de datos exista antes de verificar/desplegar tablas
        ensure_database_exists()

        # 2. Verificar si el Data Warehouse ya está inicializado
        if not force and is_warehouse_initialized():
            logger.info("El Data Warehouse ya está inicializado. Omitiendo DDL...")
            return

        sql_dir = ROOT_DIR / "sql" / "warehouse"
        script_01 = sql_dir / "01_database_setup.sql"
        script_02 = sql_dir / "02_star_schema.sql"

        app_engine = get_sql_engine()
        try:
            execute_sql_file(script_01, app_engine)
            execute_sql_file(script_02, app_engine)
        finally:
            app_engine.dispose()

        logger.info("Estructura del Data Warehouse desplegada exitosamente.")

    except Exception as e:
        logger.critical(f"Fallo durante la inicialización del Data Warehouse: {e}")
        sys.exit(1)


if __name__ == "__main__":
    initialize_warehouse()