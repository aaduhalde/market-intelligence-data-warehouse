#!/usr/bin/env python3
"""
main.py
-------
Orquestador central de Market Intelligence Data Platform.
Permite ejecutar de forma secuencial (pipeline completo) o aislada 
cada una de las fases del roadmap con sus tests de validación correspondientes.
"""

import sys
import argparse
from pathlib import Path

# Configurar el PYTHONPATH para incluir la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importar los scripts de ejecución por fase
from src.phases.phase0_env import run_phase_0
from src.phases.phase1_config import run_phase_1
from src.phases.phase2_ingestion import run_phase_2
from src.phases.phase3_processing import run_phase_3
from src.phases.phase4_database import run_phase_4
from src.phases.phase5_etl import run_phase_5
from src.phases.phase6_dq import run_phase_6
from src.phases.phase7_analytics import run_phase_7
from src.phases.phase8_matcher import run_phase_8
from src.phases.phase9_export import run_phase_9


def main():
    parser = argparse.ArgumentParser(
        description="Market Intelligence Data Platform — Orquestador de Fases con Validación",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=list(range(10)),
        help=(
            "Ejecuta una fase específica del roadmap con sus tests:\n"
            "  0: Validación de entorno y dependencias (Fase 0).\n"
            "  1: Validación de taxonomías y archivos YAML (Fase 1).\n"
            "  2: Ingesta de datos crudos / SerpAPI (Fase 2).\n"
            "  3: Procesamiento incremental y Staging Parquet (Fase 3).\n"
            "  4: Inicialización de Base de Datos y Warehouse DDL (Fase 4).\n"
            "  5: ETL Staging hacia Modelo Estrella (Fase 5).\n"
            "  6: Suite de Pruebas de Calidad de Datos / Data Quality (Fase 6).\n"
            "  7: Despliegue de Vistas Analíticas (Fase 7).\n"
            "  8: Ejecución del Candidate Matcher y Scoring (Fase 8).\n"
            "  9: Exportación de Tablas y Vistas a CSV (Fase 9)."
        )
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecuta de forma secuencial todo el pipeline completo (Fases 0 a 9 con paradas automáticas en caso de FAIL)."
    )

    args = parser.parse_args()

    print("=" * 70)
    print("  MARKET INTELLIGENCE DATA PLATFORM — GESTOR DE PIPELINES POR FASE")
    print("=" * 70)

    fases = [
        (0, "Entorno y Dependencias", run_phase_0),
        (1, "Configuración y Taxonomías", run_phase_1),
        (2, "Ingesta de Datos Crudos", run_phase_2),
        (3, "Procesamiento Incremental", run_phase_3),
        (4, "Inicialización de Base de Datos", run_phase_4),
        (5, "ETL a Modelo Estrella", run_phase_5),
        (6, "Calidad de Datos (Data Quality)", run_phase_6),
        (7, "Despliegue Capa Analítica", run_phase_7),
        (8, "Candidate Matcher Engine", run_phase_8),
        (9, "Exportación a CSV", run_phase_9)
    ]

    if args.all:
        print("\n🚀 Ejecutando pipeline completo de forma secuencial (Gate Control activo)...")
        for p_num, p_name, p_func in fases:
            print(f"\n--- [GATEWAY] Iniciando Fase {p_num}: {p_name} ---")
            try:
                p_func()
                print(f"✅ [PASS] Fase {p_num} superada con éxito.")
            except Exception as e:
                print(f"❌ [FAIL] La Fase {p_num} ({p_name}) falló: {e}")
                print("🛑 Pipeline detenido por violación de Quality Gate.")
                sys.exit(1)
        print("\n🎉 ¡Pipeline completo ejecutado exitosamente de punta a punta!")
        return

    if args.phase is not None:
        p_num, p_name, p_func = fases[args.phase]
        print(fn_msg := f"\n--- Ejecutando exclusivamente Fase {p_num}: {p_name} ---")
        try:
            p_func()
            print(f"\n✅ [PASS] Fase {p_num} completada exitosamente.")
        except Exception as e:
            print(f"\n❌ [FAIL] Error en Fase {p_num}: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()