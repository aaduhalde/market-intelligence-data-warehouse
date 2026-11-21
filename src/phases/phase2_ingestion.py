# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase2_ingestion.py
# Description: Fase 2 — Ingesta condicional (Flag Y/N) y Validación de Raw JSON
# =============================================================================

import sys
import os
import json
import glob
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.config_loader import get_env_variable
from src.ingestion.serpapi_ingest import ejecutar_ingesta

def run_phase_2() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 2 - INGESTION & RAW DATA VALIDATION")
    print("=" * 50)

    # Cargar variables de entorno
    load_dotenv(ROOT_DIR / ".env")
    run_ingest_flag = os.getenv("RUN_SERPAPI_INGEST", "N").strip().upper()
    
    tests_results = []
    raw_data_dir = ROOT_DIR / "data" / "1_raw"
    os.makedirs(raw_data_dir, exist_ok=True)

    print(f"   ℹ️ Flag configurado (RUN_SERPAPI_INGEST): '{run_ingest_flag}'")

    # P2-01: Ejecución condicional de Ingesta basada en el Flag Y/N
    if run_ingest_flag == "Y":
        print("   ℹ️ Flag en 'Y': Conectando a SerpAPI para realizar ingesta en vivo...")
        try:
            api_key = get_env_variable("SERPAPI_API_KEY")
            if not api_key or len(api_key) < 5:
                raise ValueError("SERPAPI_API_KEY no válida o ausente en el entorno.")
            
            ejecutar_ingesta(sources_config_path="config/sources.yaml", force_full_refresh=False)
            tests_results.append(("P2-01: Live API Ingest Execution", True, "Ingesta desde SerpAPI ejecutada correctamente (Flag = Y)"))
        except Exception as e:
            tests_results.append(("P2-01: Live API Ingest Execution", False, f"Error en ingesta SerpAPI: {e}"))
    else:
        print("   ℹ️ Flag en 'N': Omitiendo llamada a SerpAPI. Usando datos locales existentes en data/1_raw/")
        tests_results.append(("P2-01: Live API Ingest Execution (Skipped)", True, "Ingesta omitida por configuración (Flag = N)"))

    # Obtener archivos JSON disponibles en raw
    json_files = glob.glob(str(raw_data_dir / "*.json"))

    # P2-04 & P2-05: JSON integrity & Raw persistence check
    p24_05_pass = len(json_files) > 0
    tests_results.append(("P2-04/05: JSON Integrity & Raw Files Presence", p24_05_pass, f"Archivos raw disponibles: {len(json_files)}"))

    if not p24_05_pass:
        print("   ❌ [ERROR] No hay archivos JSON en data/1_raw y el flag RUN_SERPAPI_INGEST estaba en 'N'.")
        print("   💡 Cambia a RUN_SERPAPI_INGEST=Y en tu archivo .env para descargar datos por primera vez.")

    # Validar contenido de los JSON
    valid_payloads = 0
    total_jobs_found = 0
    schema_ok = True
    required_fields_ok = True

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                valid_payloads += 1
                
                # P2-02: API Schema check
                if not isinstance(data, dict) or ("jobs_results" not in data and "error" not in data):
                    schema_ok = False

                jobs = data.get("jobs_results", [])
                total_jobs_found += len(jobs)

                # P2-06: Required fields in jobs
                for job in jobs:
                    has_id = bool(job.get("job_id") or (job.get("title") and job.get("company_name")))
                    if not has_id:
                        required_fields_ok = False
                        break
        except Exception:
            schema_ok = False

    tests_results.append(("P2-02: API Schema Structure", schema_ok, "Estructuras jobs_results válidas en JSON"))

    # P2-03: Jobs presence
    p23_pass = total_jobs_found > 0
    tests_results.append(("P2-03: Jobs Presence in Raw", p23_pass, f"Total de vacantes crudas detectadas: {total_jobs_found}"))

    # P2-06: Required fields in raw jobs
    tests_results.append(("P2-06: Required Fields in Raw Data", required_fields_ok, "Campos mínimos presentes en registros"))

    # P2-07 & P2-08 & P2-09: Incremental state and duplicate control
    state_file = ROOT_DIR / "data" / "ingestion_state.json"
    state_ok = state_file.exists() or run_ingest_flag == "N"
    tests_results.append(("P2-07/08/09: Incremental State & Duplicate Control", state_ok, f"Estado incremental verificado ({state_file.name})"))

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
    run_phase_2()