# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase0_env.py
# Description: Fase 0 — Validación de Entorno, Dependencias y Configuración Base
# =============================================================================

import sys
import os
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def run_phase_0() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 0 - ENVIRONMENT & DEPENDENCIES VALIDATION")
    print("=" * 50)

    tests_results = []

    # P0-01: Python version
    py_version = sys.version_info
    p01_pass = py_version >= (3, 10)
    tests_results.append(("Python version >= 3.10", p01_pass, f"Actual: {py_version.major}.{py_version.minor}.{py_version.micro}"))

    # P0-02: Requirements file exists and not empty
    req_path = ROOT_DIR / "requirements.txt"
    p02_pass = req_path.exists() and req_path.stat().st_size > 0
    tests_results.append(("Requirements file exists", p02_pass, str(req_path)))

    # P0-03 & P0-04: Dependencies and pip check simulation
    # Verificamos paquetes críticos definidos en requirements.txt (pandas, sqlalchemy, pyodbc, yaml, etc.)
    critical_packages = ["pandas", "yaml", "sqlalchemy", "pyodbc", "dotenv", "serpapi"]
    missing_pkgs = [pkg for pkg in critical_packages if importlib.util.find_spec(pkg) is None]
    p03_pass = len(missing_pkgs) == 0
    tests_results.append(("Critical dependencies installed", p03_pass, f"Faltantes: {missing_pkgs if missing_pkgs else 'Ninguna'}"))

    # P0-05: Project paths
    required_dirs = ["config", "data", "data/1_raw", "data/2_staged", "data/3_csv", "src", "sql", "images"]
    missing_dirs = [d for d in required_dirs if not (ROOT_DIR / d).exists()]
    p05_pass = len(missing_dirs) == 0
    tests_results.append(("Project directory structure", p05_pass, f"Faltantes: {missing_dirs if missing_dirs else 'Ninguna'}"))

    # P0-06: Config YAML files presence
    required_yamls = [
        "config/sources.yaml",
        "config/roles.yaml",
        "config/skills.yaml",
        "config/metrics.yaml",
        "config/candidate_profile.yaml"
    ]
    missing_yamls = [y for y in required_yamls if not (ROOT_DIR / y).exists()]
    p06_pass = len(missing_yamls) == 0
    tests_results.append(("Configuration YAML files presence", p06_pass, f"Faltantes: {missing_yamls if missing_yamls else 'Ninguna'}"))

    # P0-07: Source compilation
    try:
        import compileall
        compilation_success = compileall.compile_dir(str(ROOT_DIR / "src"), quiet=True)
        p07_pass = bool(compilation_success)
    except Exception as e:
        p07_pass = False
    tests_results.append(("Source syntax compilation", p07_pass, "Sin errores de sintaxis en src/"))

    # P0-08: Internal imports resolution
    try:
        from src.utils.config_loader import get_env_variable
        from src.utils.db_connector import get_sql_engine
        p08_pass = True
    except Exception as e:
        p08_pass = False
    tests_results.append(("Internal module imports", p08_pass, "Módulos utils resueltos correctamente"))

    # P0-09: Environment variables (DB_SERVER, DB_NAME, etc.)
    load_dotenv(ROOT_DIR / ".env")
    db_server = os.getenv("DB_SERVER")
    db_name = os.getenv("DB_NAME")
    p09_pass = bool(db_server and db_name)
    tests_results.append(("Environment variables (.env)", p09_pass, f"DB_SERVER={db_server}, DB_NAME={db_name}"))

    # Imprimir reporte detallado
    passed_count = 0
    failed_count = 0
    for test_name, passed, detail in tests_results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"{status_str} {test_name:<35} | {detail}")

    print("-" * 50)
    print(f"RESULT: {'PASS' if failed_count == 0 else 'FAIL'}")
    print(f"Tests: {len(tests_results)} | Passed: {passed_count} | Failed: {failed_count}")
    print("-" * 50)

    if failed_count > 0:
        sys.exit(1)
    return True

if __name__ == "__main__":
    run_phase_0()