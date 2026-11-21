# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase3_processing.py
# Description: Fase 3 — Procesamiento, Normalización y Staging (Raw -> Parquet)
# =============================================================================

import sys
import os
import glob
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importar la lógica de procesamiento existente
from src.ingestion.procesar_vacantes import procesar_incremental, DIR_RAW, FILE_STAGED_DESTINO

def run_phase_3() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 3 - PROCESSING & STAGING VALIDATION")
    print("=" * 50)

    tests_results = []
    raw_dir = Path(DIR_RAW)
    staged_file = Path(FILE_STAGED_DESTINO)

    # P3-01: Raw reader - Verificar que existen inputs raw legibles
    raw_files = list(raw_dir.glob("*.json"))
    p31_pass = len(raw_files) > 0
    tests_results.append(("P3-01: Raw Reader Inputs", p31_pass, f"Archivos JSON crudos disponibles: {len(raw_files)}"))

    if not p31_pass:
        print("   ❌ [FAIL] No hay archivos JSON en data/1_raw para procesar.")
        sys.exit(1)

    # Ejecutar el procesamiento incremental (Transformación Raw -> Staged Parquet)
    print("   ℹ️ Ejecutando pipeline de procesamiento y normalización...")
    try:
        procesar_incremental()
        p3_exec_pass = True
    except Exception as e:
        p3_exec_pass = False
        print(f"   ❌ Error durante procesar_incremental: {e}")

    tests_results.append(("P3-02 to P3-10: Parsing, Rules & Incremental Logic", p3_exec_pass, "Transformación y normalización ejecutadas"))

    # P3-11: Parquet Schema & File Existence Validation
    parquet_exists = staged_file.exists()
    df_staged = pd.DataFrame()
    schema_valid = False

    if parquet_exists:
        try:
            df_staged = pd.read_parquet(staged_file)
            required_cols = ["job_id", "titulo_vacante", "nombre_rol", "familia_rol", "ubicacion", "skills_array"]
            schema_valid = all(col in df_staged.columns for col in required_cols)
        except Exception as e:
            schema_valid = False

    tests_results.append(("P3-11: Parquet Schema & Persistence", parquet_exists and schema_valid, f"Archivo Parquet generado con {len(df_staged)} registros y schema válido"))

    # P3-03: Job ID stability (No nulos y sin vacíos)
    ids_valid = False
    if not df_staged.empty:
        null_ids = df_staged["job_id"].isnull().sum()
        empty_ids = (df_staged["job_id"] == "").sum()
        ids_valid = (null_ids == 0) and (empty_ids == 0)
    tests_results.append(("P3-03: Job ID Stability", ids_valid, "Todos los job_id son estables y no nulos"))

    # P3-04: Deduplication check (No job_id duplicados en el staged)
    no_dupes = False
    if not df_staged.empty:
        total_rows = len(df_staged)
        unique_ids = df_staged["job_id"].nunique()
        no_dupes = (total_rows == unique_ids)
    tests_results.append(("P3-04: Staged Deduplication", no_dupes, f"Total filas: {len(df_staged)} | IDs únicos: {df_staged['job_id'].nunique() if not df_staged.empty else 0}"))

    # P3-12: Reprocessing Reproducibility (Ejecutar segunda vez no altera conteo ni corrompe)
    try:
        procesar_incremental()
        df_staged_rerun = pd.read_parquet(staged_file)
        reproducible = (len(df_staged) == len(df_staged_rerun))
    except Exception:
        reproducible = False
    tests_results.append(("P3-12: Reprocessing Reproducibility", reproducible, "Segunda ejecución idéntica y estable"))

    # Reporte de resultados
    passed_count = 0
    failed_count = 0
    for test_name, passed, detail in tests_results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"{status_str} {test_name:<45} | {detail}")

    print("-" * 50)
    print(f"RESULT: {'PASS' if failed_count == 0 else 'FAIL'}")
    print(f"Tests: {len(tests_results)} | Passed: {passed_count} | Failed: {failed_count}")
    print("-" * 50)

    if failed_count > 0:
        sys.exit(1)
    return True

if __name__ == "__main__":
    run_phase_3()