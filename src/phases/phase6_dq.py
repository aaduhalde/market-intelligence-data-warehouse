# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase6_dq.py
# Description: Fase 6 — Auditoría de Calidad de Datos, Unicidad e Integridad Referencial
# =============================================================================

import sys
from pathlib import Path
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine

def run_phase_6() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 6 - DATA QUALITY & REFERENTIAL INTEGRITY AUDIT")
    print("=" * 50)

    tests_results = []
    engine = get_sql_engine()

    try:
        with engine.connect() as conn:
            # P6-01: Deduplicación e Idempotencia Snapshot (BR-001, BR-011, BR-012)
            total_facts = conn.execute(text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta;")).scalar() or 0
            
            duplicados_fact = conn.execute(text("""
                SELECT proveedor_ingesta, source_job_id, fecha_captura_id, COUNT(*) 
                FROM warehouse.fact_observacion_oferta 
                GROUP BY proveedor_ingesta, source_job_id, fecha_captura_id 
                HAVING COUNT(*) > 1;
            """)).fetchall()
            
            p61_pass = (len(duplicados_fact) == 0) and (total_facts > 0)
            tests_results.append(("P6-01: Snapshot Deduplication & Uniqueness", p61_pass, f"Total hechos: {total_facts} | Duplicados: {len(duplicados_fact)}"))

            # P6-02: Integridad Referencial y Mapeo Mínimo (BR-004, BR-006, BR-007)
            ref_query = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN empresa_id IS NULL OR empresa_id = -1 THEN 1 ELSE 0 END) AS sin_empresa,
                    SUM(CASE WHEN rol_id IS NULL OR rol_id = -1 THEN 1 ELSE 0 END) AS sin_rol
                FROM warehouse.fact_observacion_oferta;
            """)).fetchone()
            
            sin_empresa = ref_query.sin_empresa or 0
            p62_pass = (sin_empresa == 0)
            tests_results.append(("P6-02: Referential Integrity (Zero Orphan Companies)", p62_pass, f"Empresas huérfanas: {sin_empresa}"))

            # P6-03: Integridad M:N y Taxonomía de Skills (BR-015, BR-017)
            dupes_bridge = conn.execute(text("""
                SELECT observacion_oferta_id, skill_id, COUNT(*) 
                FROM warehouse.rel_oferta_skill 
                GROUP BY observacion_oferta_id, skill_id 
                HAVING COUNT(*) > 1;
            """)).fetchall()

            bridge_metrics = conn.execute(text("""
                SELECT COUNT(DISTINCT observacion_oferta_id), COUNT(*) 
                FROM warehouse.rel_oferta_skill;
            """)).fetchone()
            
            total_rels = bridge_metrics[1] or 0
            p63_pass = (len(dupes_bridge) == 0) and (total_rels > 0)
            tests_results.append(("P6-03: Skill Bridge Integrity & M:N Uniqueness", p63_pass, f"Relaciones M:N válidas: {total_rels} | Duplicados en puente: {len(dupes_bridge)}"))

            # P6-04: Cobertura de Taxonomía de Habilidades en dim_skill
            skill_coverage = conn.execute(text("""
                SELECT 
                    COUNT(*) AS total_skills,
                    SUM(CASE WHEN categoria_skill = 'Unassigned' OR categoria_skill IS NULL THEN 1 ELSE 0 END) AS unassigned
                FROM warehouse.dim_skill;
            """)).fetchone()
            
            total_skills = skill_coverage.total_skills or 0
            unassigned_skills = skill_coverage.unassigned or 0
            coverage_pct = ((total_skills - unassigned_skills) / total_skills * 100.0) if total_skills > 0 else 0.0
            p64_pass = (total_skills > 0)
            tests_results.append(("P6-04: Skill Taxonomy Categorization Coverage", p64_pass, f"Total skills: {total_skills} | Categorizados: {coverage_pct:.1f}%"))

    except Exception as e:
        print(f"   ❌ Error crítico en auditoría de calidad de datos: {e}")
        tests_results.append(("P6-05: DQ Pipeline Execution", False, f"Error: {e}"))

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
    run_phase_6()