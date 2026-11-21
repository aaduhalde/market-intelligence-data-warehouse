# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase8_matcher.py
# Description: Fase 8 — Motor de Candidate Matching y Scoring de Oportunidades
# =============================================================================

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.analytics.candidate_matcher import CandidateMatcher, run_candidate_matcher_analysis
from src.utils.db_connector import get_sql_engine

def run_phase_8() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 8 - CANDIDATE MATCHER & SCORING ENGINE")
    print("=" * 50)

    tests_results = []

    try:
        # P8-01: Inicialización del Matcher y Carga del Perfil de Candidato
        matcher = CandidateMatcher()
        profile_loaded = bool(matcher.candidate_skills)
        tests_results.append(("P8-01: Candidate Profile & Skills Load", profile_loaded, f"Skills cargados desde perfil: {len(matcher.candidate_skills)}"))

        # P8-02 & P8-03: Ejecución del Motor de Matching sobre las ofertas del DW
        results = run_candidate_matcher_analysis()
        execution_ok = isinstance(results, list) and len(results) > 0
        tests_results.append(("P8-02 & P8-03: Job Evaluation & Scoring Execution", execution_ok, f"Ofertas evaluadas con éxito: {len(results) if results else 0}"))

        # P8-04: Verificación de métricas Effective Match Score calculadas
        if results:
            valid_scores = all(0.0 <= r["effective_match_score"] <= 100.0 for r in results)
            avg_score = sum(r["effective_match_score"] for r in results) / len(results)
            tests_results.append(("P8-04: Effective Match Score Range Validation", valid_scores, f"Promedio Effective Match: {avg_score:.2f}/100"))
        else:
            tests_results.append(("P8-04: Effective Match Score Range Validation", False, "No se obtuvieron resultados para evaluar"))

    except Exception as e:
        print(f"   ❌ Error crítico en Fase 8: {e}")
        tests_results.append(("P8-05: Matcher Pipeline Execution", False, f"Error: {e}"))

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
    run_phase_8()