import sys
from pathlib import Path

from src.utils.wakeup import despertar_api_y_db
from src.ingestion.serpapi_ingest import ejecutar_ingesta
from src.ingestion.procesar_vacantes import procesar_incremental
from src.utils.init_db import initialize_warehouse
from src.ingestion.load_warehouse import execute_loading
from src.utils.data_quality import run_all_data_quality_tests
from src.analytics.init_analytics import execute_analytics_views
from src.analytics.candidate_matcher import run_candidate_matcher_analysis
from src.export.export_tables_to_csv import export_all_tables_and_views_to_csv


def pipeline():
    print("=" * 60)
    print("INICIANDO PIPELINE - market intelligence DW")
    print("=" * 60)

    print("\n[PASO 0] Despertando API y Azure SQL Database...")
    if not despertar_api_y_db():
        print("\n❌ [ERROR CRÍTICO] La base de datos no está disponible. Abortando ejecucion.")
        sys.exit(1)

    # Paso 1: Ingesta desde SerpApi hacia /data/1_raw
    print("\n[PASO 1] Ejecutando ingesta de datos...")
    ejecutar_ingesta()

    # Paso 2: Transformación e integración incremental
    print("\n[PASO 2] Procesando vacantes de forma incremental...")
    procesar_incremental()

    # Paso 3: Ingesta desde SerpApi hacia /data/1_raw
    print("\n[PASO 3] Inicializar la base de datos...")
    initialize_warehouse()

    # Paso 4: Loading
    print("\n[PASO 4] Carga del Data Warehouse...")
    execute_loading()

    # Paso 5: Pruebas de Calidad de Datos (Data Quality)
    print("\n[PASO 5] Ejecutando Pruebas de Calidad de Datos (Data Quality)...")
    run_all_data_quality_tests()

    # Paso 6: Analítica
    print("\n[PASO 6] Desplegando Capa Analítica y Candidate Matcher...")
    execute_analytics_views()
    run_candidate_matcher_analysis()

    # Paso 7: Analítica
    print("\n[PASO 7] Exportando tablas y vistas a CSV (data/3_csv)...")
    export_all_tables_and_views_to_csv()

    print("\n" + "=" * 60)
    print("PIPELINE EJECUTADO CON ÉXITO")
    print("=" * 60)


if __name__ == "__main__":
    pipeline()