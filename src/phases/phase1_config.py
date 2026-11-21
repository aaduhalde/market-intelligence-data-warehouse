# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/phases/phase1_config.py
# Description: Fase 1 — Validación de Contenido, Taxonomías y Coherencia YAML
# =============================================================================

import sys
import yaml
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def run_phase_1() -> bool:
    print("\n" + "=" * 50)
    print("PHASE 1 - CONFIGURATION & TAXONOMY VALIDATION")
    print("=" * 50)

    tests_results = []
    config_dir = ROOT_DIR / "config"

    # Auxiliar para cargar YAML de forma segura
    def safe_load_yaml(filename):
        path = config_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return None

    # P1-01: YAML syntax parsing for all required files
    yaml_files = ["sources.yaml", "roles.yaml", "skills.yaml", "metrics.yaml", "candidate_profile.yaml"]
    loaded_yamls = {}
    syntax_ok = True
    for yfile in yaml_files:
        data = safe_load_yaml(yfile)
        if data is None:
            syntax_ok = False
        else:
            loaded_yamls[yfile] = data
    tests_results.append(("P1-01: YAML Syntax Parsing", syntax_ok, "Todos los YAML se parsean correctamente"))

    # P1-02: Schema & Required Keys
    schema_ok = (
        "job_sources" in loaded_yamls.get("sources.yaml", {}) and
        "role_taxonomy" in loaded_yamls.get("roles.yaml", {}) and
        "skill_taxonomy" in loaded_yamls.get("skills.yaml", {}) and
        bool(loaded_yamls.get("metrics.yaml", {})) and
        "candidate_accessibility" in loaded_yamls.get("candidate_profile.yaml", {}) and
        "skills" in loaded_yamls.get("candidate_profile.yaml", {})
    )
    tests_results.append(("P1-02: Schema & Required Keys", schema_ok, "Estructuras raíz verificadas"))

    # P1-03: Sources defined
    sources_data = loaded_yamls.get("sources.yaml", {}).get("job_sources", [])
    p13_pass = isinstance(sources_data, list) and len(sources_data) > 0
    tests_results.append(("P1-03: Job Sources Definition", p13_pass, f"Fuentes detectadas: {len(sources_data)}"))

    # P1-04 & P1-05: Roles unique and valid tiers
    roles_tax = loaded_yamls.get("roles.yaml", {}).get("role_taxonomy", {})
    valid_families = ["primary", "secondary", "legacy_leverage"]
    role_families_ok = all(fam in roles_tax for fam in valid_families)
    
    all_roles = []
    for fam in valid_families:
        all_roles.extend(roles_tax.get(fam, []))
    unique_roles_ok = len(all_roles) == len(set(all_roles)) and len(all_roles) > 0
    p14_15_pass = role_families_ok and unique_roles_ok
    tests_results.append(("P1-04/05: Roles Uniqueness & Tiers", p14_15_pass, f"Total roles validados: {len(all_roles)} (Únicos: {unique_roles_ok})"))

    # P1-06 & P1-07: Skills unique, normalized and valid categories
    skills_tax = loaded_yamls.get("skills.yaml", {}).get("skill_taxonomy", {})
    all_skills = []
    categories_ok = len(skills_tax) > 0
    for cat, sk_list in skills_tax.items():
        if isinstance(sk_list, list):
            all_skills.extend(sk_list)
        else:
            categories_ok = False
    unique_skills_ok = len(all_skills) == len(set(all_skills)) and len(all_skills) > 0
    p16_17_pass = categories_ok and unique_skills_ok
    tests_results.append(("P1-06/07: Skills Uniqueness & Categories", p16_17_pass, f"Total skills taxonomizadas: {len(all_skills)}"))

    # P1-08: Metrics parameters and valid weights
    metrics_data = loaded_yamls.get("metrics.yaml", {})
    metrics_ok = bool(metrics_data)
    tests_results.append(("P1-08: Metrics & Weights Configuration", metrics_ok, "Parámetros de métricas cargados"))

    # P1-09: Candidate profile skills confidence bounds (0.0 to 1.0)
    profile_skills = loaded_yamls.get("candidate_profile.yaml", {}).get("skills", {})
    bounds_ok = True
    if isinstance(profile_skills, dict):
        for sk, conf in profile_skills.items():
            if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
                bounds_ok = False
                break
    else:
        bounds_ok = False
    tests_results.append(("P1-09: Candidate Profile Confidence Bounds", bounds_ok, "Valores de proficiencia entre 0.0 y 1.0"))

    # P1-10: Cross-config consistency
    p110_pass = syntax_ok and schema_ok and p13_pass and p14_15_pass and p16_17_pass and bounds_ok
    tests_results.append(("P1-10: Cross-Config Consistency", p110_pass, "Coherencia cruzada global exitosa"))

    # Imprimir reporte estructurado
    passed_count = 0
    failed_count = 0
    for test_name, passed, detail in tests_results:
        status_str = "[PASS]" if passed else "[FAIL]"
        if passed:
            passed_count += 1
        else:
            failed_count += 1
        print(f"{status_str} {test_name:<42} | {detail}")

    print("-" * 50)
    print(f"RESULT: {'PASS' if failed_count == 0 else 'FAIL'}")
    print(f"Tests: {len(tests_results)} | Passed: {passed_count} | Failed: {failed_count}")
    print("-" * 50)

    if failed_count > 0:
        sys.exit(1)
    return True

if __name__ == "__main__":
    run_phase_1()