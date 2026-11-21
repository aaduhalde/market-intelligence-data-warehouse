# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase5_etl.py
# Description: Fase 5 — ETL Warehouse (Carga Parquet -> Staging -> Modelo Estrella)
# =============================================================================

import sys
from pathlib import Path
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine
from src.ingestion.load_warehouse import load_parquet_to_staging, run_dw_transformation

def run_phase_5() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 5 - ETL WAREHOUSE & STAR SCHEMA POPULATION")
    print("=" * 50)

    tests_results = []
    engine = get_sql_engine()
    staged_parquet = ROOT_DIR / "data" / "2_staged" / "vacantes_staged.parquet"

    # P5-01: Verificación de disponibilidad del dataset Staged (Parquet)
    p51_pass = staged_parquet.exists()
    tests_results.append(("P5-01: Staged Dataset Availability", p51_pass, f"Parquet staged encontrado: {staged_parquet.name}"))

    if not p51_pass:
        print("   ❌ [FAIL] No se encontró el archivo Parquet staged en data/2_staged/. Ejecuta la Fase 3 primero.")
        sys.exit(1)

    records_loaded = 0
    try:
        # P5-02: Carga desde Parquet hacia la tabla staging en SQL Server
        print("   ℹ️ Cargando Parquet a staging en SQL Server...")
        records_loaded = load_parquet_to_staging(staged_parquet, engine)
        p52_pass = records_loaded > 0
        tests_results.append(("P5-02: Parquet to Staging Load", p52_pass, f"Registros cargados en staging: {records_loaded}"))
    except Exception as e:
        tests_results.append(("P5-02: Parquet to Staging Load", False, f"Error cargando a staging: {e}"))
        p52_pass = False

    if not p52_pass:
        print("   ❌ [FAIL] La carga a staging falló. Abortando pipeline.")
        sys.exit(1)

    try:
        # P5-03: Ejecución de Transformación ETL (Staging al Modelo Estrella)
        print("   ℹ️ Ejecutando transformación set-based hacia el Data Warehouse...")
        run_dw_transformation(engine)
        tests_results.append(("P5-03: DW Transformation & Star Schema Load", True, "Script 01_load_dw_from_staging ejecutado con éxito"))
    except Exception as e:
        tests_results.append(("P5-03: DW Transformation & Star Schema Load", False, f"Error en transformación DW: {e}"))
        print(f"   ❌ Error crítico en ETL: {e}")

    try:
        # P5-04: Validación de población en Tabla de Hechos y Dimensiones
        with engine.connect() as conn:
            fact_count = conn.execute(text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta")).scalar() or 0
            facts_ok = fact_count > 0
            tests_results.append(("P5-04: Fact Table Population Check", facts_ok, f"Registros en fact_observacion_oferta: {fact_count}"))

            dims_result = conn.execute(text("""
                SELECT 
                    (SELECT COUNT(*) FROM warehouse.dim_empresa) as empresas,
                    (SELECT COUNT(*) FROM warehouse.dim_rol) as roles,
                    (SELECT COUNT(*) FROM warehouse.dim_ubicacion) as ubicaciones,
                    (SELECT COUNT(*) FROM warehouse.dim_skill) as skills,
                    (SELECT COUNT(*) FROM warehouse.rel_oferta_skill) as rels
            """)).fetchone()

            dims_ok = dims_result and all(val > 0 for val in dims_result)
            tests_results.append(("P5-05: Dimensions & Bridge Population Integrity", dims_ok, 
                                  f"Empresas: {dims_result[0]} | Roles: {dims_result[1]} | Ubicaciones: {dims_result[2]} | Skills: {dims_result[3]} | Relaciones M:N: {dims_result[4]}"))

    except Exception as e:
        tests_results.append(("P5-04/05: DW Validation", False, f"Error validando dimensiones/hechos: {e}"))

    # Reporte de resultados del Gate 5
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
    run_phase_5()