# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase7_analytics.py
# Description: Fase 7 — Despliegue y Validación de Vistas y KPIs Analíticos
# =============================================================================

import sys
import re
from pathlib import Path
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine

def run_phase_7() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 7 - ANALYTICS VIEWS DEPLOYMENT & KPI VALIDATION")
    print("=" * 50)

    tests_results = []
    engine = get_sql_engine()

    try:
        # P7-01 & P7-02: View deployment and execution check
        sql_file = ROOT_DIR / "sql" / "analytics" / "01_create_analytics_views.sql"
        if not sql_file.exists():
            raise FileNotFoundError(f"No se encontró el archivo SQL en: {sql_file}")

        sql_content = sql_file.read_text(encoding="utf-8")
        batches = [
            batch.strip()
            for batch in re.split(r'^\s*GO\s*$', sql_content, flags=re.MULTILINE | re.IGNORECASE)
            if batch.strip()
        ]

        with engine.connect() as conn:
            for stmt in batches:
                conn.execute(text(stmt))
                if getattr(conn, "commit", None):
                    conn.commit()
        
        tests_results.append(("P7-01 & P7-02: Analytics Views Deployment & Execution", True, "Vistas desplegadas y ejecutadas sin errores SQL"))

        with engine.connect() as conn:
            # P7-03: Total jobs reconciliation
            total_facts = conn.execute(text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta;")).scalar() or 0
            summary_count = conn.execute(text("SELECT COUNT(*) FROM analytics.vw_market_intelligence_summary;")).scalar() or 0
            p73_pass = (total_facts == summary_count) and (total_facts > 0)
            tests_results.append(("P7-03: Total Jobs Reconciliation", p73_pass, f"Hechos: {total_facts} | Vista summary: {summary_count}"))

            # P7-04: Skill demand view execution check
            skill_demand_count = conn.execute(text("SELECT COUNT(*) FROM analytics.vw_market_skill_demand;")).scalar() or 0
            p74_pass = skill_demand_count >= 0
            tests_results.append(("P7-04: Skill Demand KPI Calculation", p74_pass, f"Skills analizados en demanda: {skill_demand_count}"))

            # P7-05: Role distribution check
            roles_dist = conn.execute(text("""
                SELECT TOP 5 nombre_rol, COUNT(*) as q
                FROM analytics.vw_market_intelligence_summary
                GROUP BY nombre_rol
                ORDER BY q DESC;
            """)).fetchall()
            p75_pass = len(roles_dist) > 0
            tests_results.append(("P7-05: Role Distribution Analysis", p75_pass, f"Roles principales detectados en analítica: {len(roles_dist)}"))

            # P7-06 & P7-07: Geographic & Remote analysis
            geo_dist = conn.execute(text("""
                SELECT market_tier, COUNT(*) as q
                FROM analytics.vw_market_intelligence_summary
                GROUP BY market_tier;
            """)).fetchall()
            p76_pass = len(geo_dist) > 0
            tests_results.append(("P7-06 & P7-07: Geographic & Market Tiers Breakdown", p76_pass, f"Market Tiers analizados: {len(geo_dist)}"))

            # P7-08: Snapshot analysis validation
            snapshots = conn.execute(text("""
                SELECT DISTINCT fecha_captura_id 
                FROM analytics.vw_market_intelligence_summary;
            """)).fetchall()
            p78_pass = len(snapshots) > 0
            tests_results.append(("P7-08: Snapshot Analysis & Temporal Traceability", p78_pass, f"Snapshots de captura activos: {len(snapshots)}"))

            # P7-09: Double counting prevention check
            double_count_check = conn.execute(text("""
                SELECT source_job_id, fecha_captura_id, COUNT(*) 
                FROM analytics.vw_market_intelligence_summary 
                GROUP BY source_job_id, fecha_captura_id 
                HAVING COUNT(*) > 1;
            """)).fetchall()
            p79_pass = len(double_count_check) == 0
            tests_results.append(("P7-09: Double Counting Prevention", p79_pass, f"Duplicados detectados en vistas: {len(double_count_check)}"))

            # P7-10: Empty dataset controlled behavior
            p710_pass = total_facts > 0  # Valida que el dataset no esté vacío al momento de la analítica
            tests_results.append(("P7-10: Dataset Population Control", p710_pass, f"Dataset con registros aptos para analítica: {total_facts}"))

    except Exception as e:
        print(f"   ❌ Error crítico en Fase 7: {e}")
        tests_results.append(("P7-Analytics Pipeline Execution", False, f"Error: {e}"))

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
    run_phase_7()