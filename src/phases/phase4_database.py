# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase4_database.py
# Description: Fase 4 — Despliegue Ordenado e Idempotente del DDL (/sql) con Parser de 'GO'
# =============================================================================

import sys
import re
from pathlib import Path
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_connector import ensure_database_exists, get_sql_engine

def run_phase_4() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 4 - DATABASE INFRASTRUCTURE & DDL DEPLOYMENT")
    print("=" * 50)

    tests_results = []

    # P4-01: Auto-creación de Base de Datos y Conectividad
    try:
        ensure_database_exists()
        engine = get_sql_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        tests_results.append(("P4-01: SQL Server Connectivity & Auto-Create", True, "Base de datos disponible y conexión exitosa"))
    except Exception as e:
        tests_results.append(("P4-01: SQL Server Connectivity & Auto-Create", False, f"Error de conexión/creación: {e}"))
        print("-" * 50)
        print("RESULT: FAIL")
        print("Tests: 1 | Passed: 0 | Failed: 1")
        print("-" * 50)
        sys.exit(1)

    try:
        engine = get_sql_engine()
        with engine.connect() as conn:
            # P4-02: Verificación de Esquemas Requeridos
            required_schemas = ['staging', 'warehouse', 'analytics']
            for sch in required_schemas:
                conn.execute(text(f"""
                    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{sch}')
                    BEGIN
                        EXEC('CREATE SCHEMA [{sch}]');
                    END
                """))
            conn.commit()

            result_sch = conn.execute(text("""
                SELECT SCHEMA_NAME 
                FROM INFORMATION_SCHEMA.SCHEMATA 
                WHERE SCHEMA_NAME IN ('staging', 'warehouse', 'analytics')
            """))
            schemas = [row[0] for row in result_sch.fetchall()]
            schemas_ok = all(s in schemas for s in required_schemas)
            tests_results.append(("P4-02: Required Schemas (staging, warehouse, analytics)", schemas_ok, f"Esquemas validados: {schemas}"))

            # --- P4-03: EJECUCIÓN ORDENADA DE SCRIPTS DDL DESDE LA CARPETA /sql ---
            sql_dir = ROOT_DIR / "sql"
            
            ordered_scripts = [
                sql_dir / "warehouse" / "01_database_setup.sql",
                sql_dir / "warehouse" / "02_star_schema.sql",
                sql_dir / "staging" / "01_load_dw_from_staging.sql",
                sql_dir / "analytics" / "01_create_analytics_views.sql"
            ]

            executed_files = 0
            for script_path in ordered_scripts:
                if script_path.exists():
                    try:
                        with open(script_path, "r", encoding="utf-8") as f:
                            script_content = f.read()

                        # Separar lotes utilizando regex para detectar líneas que contengan únicamente 'GO'
                        batches = re.split(r'^\s*GO\s*$', script_content, flags=re.IGNORECASE | re.MULTILINE)
                        
                        # Ejecutar cada lote de manera transaccional
                        with engine.begin() as trans_conn:
                            for batch in batches:
                                clean_batch = batch.strip()
                                if clean_batch:
                                    trans_conn.execute(text(clean_batch))
                        
                        executed_files += 1
                        print(f"   ℹ️ Ejecutado con éxito: {script_path.relative_to(ROOT_DIR)}")
                    except Exception as ex:
                        print(f"   ❌ Error ejecutando {script_path.name}: {ex}")
                else:
                    print(f"   ⚠️ Script no encontrado: {script_path}")

            tests_results.append(("P4-03: Ordered DDL Scripts Execution", executed_files == len(ordered_scripts), f"Scripts DDL/ETL procesados: {executed_files}/{len(ordered_scripts)}"))

            # --- P4-04: VALIDACIÓN ESTRICTA DE TABLAS Y VISTAS CLAVE ---
            expected_tables = [
                ('staging', 'stg_observacion_oferta'),
                ('warehouse', 'dim_empresa'),
                ('warehouse', 'dim_ubicacion'),
                ('warehouse', 'dim_modalidad'),
                ('warehouse', 'dim_rol'),
                ('warehouse', 'dim_skill'),
                ('warehouse', 'dim_fecha'),
                ('warehouse', 'fact_observacion_oferta'),
                ('warehouse', 'rel_oferta_skill')
            ]

            result_tables = conn.execute(text("""
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
            """))
            existing_tables = [(row[0], row[1]) for row in result_tables.fetchall()]

            all_tables_exist = all(t in existing_tables for t in expected_tables)
            found_count = len([t for t in expected_tables if t in existing_tables])
            
            tests_results.append(("P4-04: Strict Star Schema & Tables Validation", all_tables_exist, f"Tablas base encontradas: {found_count}/{len(expected_tables)}"))

    except Exception as e:
        print(f"   ❌ Error crítico en Fase 4: {e}")
        tests_results.append(("P4-03/04: Database Deployment Pipeline", False, f"Error: {e}"))

    # Reporte de resultados
    passed_count = 0
    failed_count = 0
    for test_name, passed, detail in tests_results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"{status_str} {test_name:<50} | {detail}")

    print("-" * 50)
    print(f"RESULT: {'PASS' if failed_count == 0 else 'FAIL'}")
    print(f"Tests: {len(tests_results)} | Passed: {passed_count} | Failed: {failed_count}")
    print("-" * 50)

    if failed_count > 0:
        sys.exit(1)
    return True

if __name__ == "__main__":
    run_phase_4()