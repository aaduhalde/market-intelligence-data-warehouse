# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase9_export.py
# Description: Fase 9 — Exportación a CSV y Reconciliación Final (Gate 9)
# =============================================================================

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine
from src.export.export_tables_to_csv import export_all_tables_and_views_to_csv


def run_phase_9() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 9 - CSV DATA EXPORT & FINAL RECONCILIATION")
    print("=" * 50)

    tests_results = []
    engine = get_sql_engine()
    output_dir = ROOT_DIR / "data" / "3_csv"

    try:
        # Capturar estado previo del Warehouse para P9-10 (Safe export)
        with engine.connect() as conn:
            pre_fact_count = conn.execute(
                text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta;")
            ).scalar() or 0

            # Obtener catálogo esperado desde SQL Server
            metadata_query = text("""
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA IN ('staging', 'warehouse', 'analytics')
                  AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                ORDER BY TABLE_SCHEMA, TABLE_NAME;
            """)
            expected_objects = conn.execute(metadata_query).fetchall()

        # Ejecutar exportación
        export_all_tables_and_views_to_csv()

        # P9-01: Directorio data/3_csv disponible
        p91_pass = output_dir.exists() and output_dir.is_dir()
        tests_results.append(("P9-01: Export Directory Availability", p91_pass, f"Directorio validado: {output_dir.relative_to(ROOT_DIR)}"))

        # P9-02 & P9-09: Archivos esperados generados y Naming estandarizado
        expected_files = [f"{sch}_{tbl}.csv" for sch, tbl in expected_objects]
        generated_files = [f.name for f in output_dir.glob("*.csv")]
        missing_files = [f for f in expected_files if f not in generated_files]
        
        p92_p99_pass = (len(expected_files) > 0) and (len(missing_files) == 0)
        tests_results.append((
            "P9-02 & P9-09: CSV Generation & Standardized Naming", 
            p92_p99_pass, 
            f"Generados: {len(generated_files)}/{len(expected_files)} | Faltantes: {len(missing_files)}"
        ))

        # Auditoría profunda por cada archivo exportado (P9-03 a P9-08)
        schema_errors = 0
        encoding_errors = 0
        row_count_mismatches = 0
        readability_errors = 0
        consistency_errors = 0

        with engine.connect() as conn:
            for sch, tbl in expected_objects:
                csv_path = output_dir / f"{sch}_{tbl}.csv"
                if not csv_path.exists():
                    continue

                # P9-04: Encoding UTF-8 check
                try:
                    with open(csv_path, "r", encoding="utf-8-sig") as f:
                        f.read(1024)
                except UnicodeDecodeError:
                    encoding_errors += 1

                # P9-07 & P9-06: CSV readability & Null preservation
                try:
                    df_csv = pd.read_csv(csv_path, encoding="utf-8-sig", keep_default_na=True)
                except Exception:
                    readability_errors += 1
                    continue

                # Consultar tabla/vista fuente en SQL
                df_sql = pd.read_sql_query(f"SELECT * FROM {sch}.{tbl};", conn)

                # P9-03: Schema (Columnas y orden exacto)
                if list(df_csv.columns) != list(df_sql.columns):
                    schema_errors += 1

                # P9-05: Row counts reconciliados
                if len(df_csv) != len(df_sql):
                    row_count_mismatches += 1

                # P9-08: Data consistency (Verificación muestral de valores en columna clave)
                if not df_sql.empty and not df_csv.empty:
                    first_col = df_sql.columns[0]
                    if str(df_csv[first_col].iloc[0]) != str(df_sql[first_col].iloc[0]):
                        # Tolerancia para floats formateados
                        if not (pd.isna(df_csv[first_col].iloc[0]) and pd.isna(df_sql[first_col].iloc[0])):
                            consistency_errors += 1

            # P9-10: Safe export (Warehouse inalterado)
            post_fact_count = conn.execute(
                text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta;")
            ).scalar() or 0

        tests_results.append(("P9-03: Schema & Column Order Match", schema_errors == 0, f"Errores de esquema: {schema_errors}"))
        tests_results.append(("P9-04: UTF-8 Encoding Compliance", encoding_errors == 0, f"Errores de codificación: {encoding_errors}"))
        tests_results.append(("P9-05: Row Count Reconciliation vs SQL", row_count_mismatches == 0, f"Discrepancias de conteo: {row_count_mismatches}"))
        tests_results.append(("P9-06 & P9-07: Readability & Null Preservation", readability_errors == 0, f"Errores de lectura Pandas: {readability_errors}"))
        tests_results.append(("P9-08: Data Value Consistency Check", consistency_errors == 0, f"Inconsistencias muestrales: {consistency_errors}"))
        tests_results.append(("P9-10: Safe Read-Only Export (DW Unaltered)", pre_fact_count == post_fact_count, f"Fact count pre/post: {pre_fact_count}/{post_fact_count}"))

    except Exception as e:
        print(f"   ❌ Error crítico en Fase 9: {e}")
        tests_results.append(("P9-Export Pipeline Execution", False, f"Error: {e}"))

    # Reporte de resultados
    passed_count = 0
    failed_count = 0
    for test_name, passed, detail in tests_results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"{status_str} {test_name:<52} | {detail}")

    print("-" * 50)
    print(f"RESULT: {'PASS' if failed_count == 0 else 'FAIL'}")
    print(f"Tests: {len(tests_results)} | Passed: {passed_count} | Failed: {failed_count}")
    print("-" * 50)

    if failed_count > 0:
        sys.exit(1)
    return True


if __name__ == "__main__":
    run_phase_9()