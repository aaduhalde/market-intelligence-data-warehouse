# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/analytics/deploy_views.py (o correspondiente)
# Description: Despliegue de vistas analíticas en Azure SQL Database
# =============================================================================

import re
import sys
from pathlib import Path
from sqlalchemy import text

# Garantizar resolución correcta de la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine


def execute_analytics_views():
    engine = get_sql_engine()
    sql_file = ROOT_DIR / "sql" / "analytics" / "01_create_analytics_views.sql"

    if not sql_file.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL en: {sql_file}")

    print("   ℹ️ Desplegando vistas en el esquema analytics...")
    
    sql_content = sql_file.read_text(encoding="utf-8")
    
    # Separar correctamente por lotes (batches) de T-SQL respetando saltos de línea e insensibilidad a mayúsculas
    batches = [
        batch.strip()
        for batch in re.split(r'^\s*GO\s*$', sql_content, flags=re.MULTILINE | re.IGNORECASE)
        if batch.strip()
    ]

    with engine.connect() as conn:
        for idx, stmt in enumerate(batches, start=1):
            conn.execute(text(stmt))
            if getattr(conn, "commit", None):
                conn.commit()

    print("   ✅ [PASO 6] Vistas analíticas desplegadas correctamente en 'analytics'.")


if __name__ == "__main__":
    execute_analytics_views()