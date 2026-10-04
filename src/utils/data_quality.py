# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: tests/test_data_quality.py (o correspondiente)
# Description: Pruebas de calidad de datos y validación de reglas de negocio
# =============================================================================

import sys
from sqlalchemy import text
from src.utils.db_connector import get_sql_engine


def test_prueba_1_deduplicacion_snapshot(conn) -> bool:
    """Prueba 1: Deduplicación e Idempotencia en Staging / DW (BR-001, BR-011, BR-012)"""
    print("\n   [PRUEBA 1] Validando Deduplicación e Idempotencia Snapshot (BR-001, BR-011, BR-012)...")
    
    # 1. Total de registros en la tabla de hechos
    total_facts = conn.execute(
        text("SELECT COUNT(*) FROM warehouse.fact_observacion_oferta;")
    ).scalar() or 0

    # 2. Búsqueda de duplicados por la clave de unicidad UQ_observacion_snapshot
    query_duplicados = text("""
        SELECT 
            proveedor_ingesta,
            source_job_id,
            fecha_captura_id,
            COUNT(*) AS cantidad_duplicados
        FROM warehouse.fact_observacion_oferta
        GROUP BY proveedor_ingesta, source_job_id, fecha_captura_id
        HAVING COUNT(*) > 1;
    """)
    duplicados = conn.execute(query_duplicados).fetchall()

    print(f"      ℹ️ Total observaciones cargadas en Fact Table: {total_facts}")
    
    if duplicados:
        print(f"   ❌ [FAIL] Se encontraron {len(duplicados)} grupos de registros duplicados por UQ_observacion_snapshot.")
        return False

    print("   ✅ [PASS] Deduplicación Snapshot OK (0 registros duplicados encontrados).")
    return True


def test_prueba_2_integridad_referencial(conn) -> bool:
    """Prueba 2: Integridad Referencial de Atributos y Mapeo Mínimo (BR-004, BR-006, BR-007, BR-025)"""
    print("\n   [PRUEBA 2] Validando Integridad Referencial de Atributos (BR-004, BR-006, BR-007, BR-025)...")
    
    query = text("""
        SELECT 
            COUNT(*) AS total_ofertas,
            SUM(CASE WHEN rol_id IS NULL OR rol_id = -1 THEN 1 ELSE 0 END) AS sin_rol_clasificado,
            SUM(CASE WHEN empresa_id IS NULL OR empresa_id = -1 THEN 1 ELSE 0 END) AS sin_empresa,
            SUM(CASE WHEN ubicacion_id IS NULL OR ubicacion_id = -1 THEN 1 ELSE 0 END) AS sin_ubicacion
        FROM warehouse.fact_observacion_oferta;
    """)
    row = conn.execute(query).fetchone()

    total = row.total_ofertas or 0
    sin_rol = row.sin_rol_clasificado or 0
    sin_empresa = row.sin_empresa or 0
    sin_ubicacion = row.sin_ubicacion or 0

    print(f"      ℹ️ Total Ofertas analizadas: {total}")
    print(f"      ℹ️ Con Empresa mapeada (dim_empresa): {total - sin_empresa} | Huérfanas: {sin_empresa}")
    print(f"      ℹ️ Con Rol clasificado (dim_rol): {total - sin_rol} | Sin Clasificar/Other (-1): {sin_rol}")
    print(f"      ℹ️ Con Ubicación mapeada (dim_ubicacion): {total - sin_ubicacion} | Sin Ubicación (-1): {sin_ubicacion}")

    if sin_empresa > 0:
        print(f"   ❌ [FAIL] Integridad Comprometida: Existen {sin_empresa} registros en fact_observacion_oferta sin empresa mapeada.")
        return False

    print("   ✅ [PASS] Integridad Referencial OK (0 registros huérfanos de empresa).")
    return True


def test_prueba_3_unicidad_y_categorizacion_skills(conn) -> bool:
    """Prueba 3: Integridad M:N y Taxonomía de Habilidades (BR-015, BR-016, BR-017)"""
    print("\n   [PRUEBA 3] Validando Tabla Puente M:N y Taxonomía de Skills (BR-015, BR-016, BR-017)...")

    # 1. Validación de Unicidad en Tabla Puente
    query_duplicados = text("""
        SELECT 
            observacion_oferta_id,
            skill_id,
            COUNT(*) AS duplicados
        FROM warehouse.rel_oferta_skill
        GROUP BY observacion_oferta_id, skill_id
        HAVING COUNT(*) > 1;
    """)
    duplicados = conn.execute(query_duplicados).fetchall()

    if duplicados:
        print(f"   ❌ [FAIL] Se encontraron {len(duplicados)} pares duplicados en rel_oferta_skill.")
        return False

    # 2. Métricas de Cobertura en la Tabla Puente
    metrics_query = text("""
        SELECT 
            COUNT(DISTINCT observacion_oferta_id) AS ofertas_con_skills,
            COUNT(*) AS total_relaciones_skills
        FROM warehouse.rel_oferta_skill;
    """)
    m_row = conn.execute(metrics_query).fetchone()
    ofertas_con_skills = m_row.ofertas_con_skills or 0
    total_relaciones = m_row.total_relaciones_skills or 0
    avg_skills = (total_relaciones / ofertas_con_skills) if ofertas_con_skills > 0 else 0.0

    print(f"      ℹ️ Relaciones M:N creadas (rel_oferta_skill): {total_relaciones}")
    print(f"      ℹ️ Ofertas que contienen al menos 1 skill: {ofertas_con_skills}")
    print(f"      ℹ️ Promedio de skills detectadas por oferta: {avg_skills:.2f}")

    # 3. Distribución y Categorización según Taxonomía
    query_categorias = text("""
        SELECT 
            ISNULL(s.categoria_skill, 'Unassigned') AS categoria_skill,
            COUNT(*) AS cantidad_skills
        FROM warehouse.dim_skill s
        GROUP BY s.categoria_skill;
    """)
    categorias = conn.execute(query_categorias).fetchall()

    total_dim_skills = sum(qty for _, qty in categorias)
    unassigned_count = sum(qty for cat, qty in categorias if cat in ('Unassigned', 'Unknown', 'NULL'))
    categorized_pct = ((total_dim_skills - unassigned_count) / total_dim_skills * 100) if total_dim_skills > 0 else 0.0

    print(f"      ℹ️ Cobertura de Taxonomía en dim_skill: {categorized_pct:.1f}% categorizados ({total_dim_skills - unassigned_count}/{total_dim_skills} skills)")
    print("      ℹ️ Desglose por Categoria:")
    for cat, qty in categorias:
        print(f"         - {cat}: {qty} skill(s)")

    print("   ✅ [PASS] Tabla Puente M:N (sin duplicados) y Taxonomía de Skills OK.")
    return True


def run_all_data_quality_tests():
    """Ejecuta la suite completa de Data Quality."""
    engine = get_sql_engine()
    results = []

    with engine.connect() as conn:
        results.append(test_prueba_1_deduplicacion_snapshot(conn))
        results.append(test_prueba_2_integridad_referencial(conn))
        results.append(test_prueba_3_unicidad_y_categorizacion_skills(conn))

    if not all(results):
        raise ValueError("Fallaron una o más pruebas de calidad de datos en el Data Warehouse.")


if __name__ == "__main__":
    run_all_data_quality_tests()