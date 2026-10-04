# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: export_csv.py (o correspondiente)
# Description: Módulo de exportación de tablas y vistas a CSV
# =============================================================================

import os
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.utils.db_connector import get_sql_engine


def export_all_tables_and_views_to_csv():
    """
    Inspecciona los esquemas 'staging', 'warehouse' y 'analytics' de la base de datos
    y exporta todas las tablas y vistas a la carpeta 'data/3_csv/' en formato CSV (UTF-8).
    Sobrescribe los archivos existentes en cada corrida para mantener la incrementalidad.
    """
    engine = get_sql_engine()
    
    # 1. Definir y asegurar la existencia de la carpeta de destino
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "data" / "3_csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Obtener todas las tablas y vistas de los esquemas objetivo
    metadata_query = text("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA IN ('staging', 'warehouse', 'analytics')
          AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
        ORDER BY TABLE_SCHEMA, TABLE_NAME;
    """)

    print("   ℹ️ Consultando objetos a exportar...")

    with engine.connect() as conn:
        objects_to_export = conn.execute(metadata_query).fetchall()

        if not objects_to_export:
            print("   ⚠️ No se encontraron tablas ni vistas para exportar.")
            return

        print(f"   ℹ️ Se exportarán {len(objects_to_export)} objetos a '{output_dir.relative_to(base_dir)}'...")

        for schema, name in objects_to_export:
            # Construir el nombre del archivo: esquema_nombre.csv
            file_name = f"{schema}_{name}.csv"
            file_path = output_dir / file_name

            # Consultar y cargar datos a pandas
            query = f"SELECT * FROM {schema}.{name};"
            df = pd.read_sql_query(query, conn)

            # Exportar a CSV sobrescribiendo el archivo previo
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            print(f"   ✅ [{schema}.{name}] -> {file_name} ({len(df)} registros)")

    print(f"   ✅ [PASO 7] Exportación incremental a CSV completada exitosamente en: {output_dir}")


if __name__ == "__main__":
    export_all_tables_and_views_to_csv()