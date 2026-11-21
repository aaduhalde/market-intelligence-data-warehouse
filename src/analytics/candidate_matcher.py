# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/analytics/candidate_matcher.py (o correspondiente)
# Description: Motor de scoring y emparejamiento de candidato vs ofertas
# =============================================================================

import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from sqlalchemy import text

# Garantizar resolución correcta de la raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.utils.db_connector import get_sql_engine
from src.utils.config_loader import load_config_from_dir


class CandidateMatcher:
    def __init__(self, profile_filename: str = "candidate_profile.yaml"):
        self.profile = self._load_profile(profile_filename)
        
        # Mapeo de skills desde el YAML: Dict[str, float]
        raw_skills = self.profile.get("skills", {})
        if isinstance(raw_skills, dict):
            self.candidate_skills: Dict[str, float] = {
                str(k).lower(): float(v) for k, v in raw_skills.items()
            }
        else:
            self.candidate_skills = {}

        # Roles objetivo desde roles.yaml o candidate_profile
        self.target_roles: Set[str] = {
            "data analyst", "analista de datos", "bi analyst", "analista de bi",
            "business intelligence analyst", "bi developer", "power bi developer",
            "data & bi specialist"
        }

    def _load_profile(self, filename: str) -> Dict[str, Any]:
        try:
            return load_config_from_dir(filename)
        except Exception:
            return {}

    def calculate_accessibility_index(self, market_tier: str, requisito_ingles: str) -> float:
        """Calcula el índice de accesibilidad combinando geografía e idioma (BR-022, BR-023)."""
        tier_str = (market_tier or "").upper()
        
        # Geografía
        if "PRIORITY 1" in tier_str or "TIER 1" in tier_str or "PERU" in tier_str or "ARGENTINA" in tier_str:
            geo_weight = 1.0
        elif "PRIORITY 2" in tier_str or "TIER 2" in tier_str:
            geo_weight = 0.85
        else:
            geo_weight = 0.65

        # Idioma
        ingles_str = (requisito_ingles or "").upper()
        if "ENGLISH" in ingles_str or "INGLES" in ingles_str:
            lang_weight = self.profile.get("candidate_accessibility", {}).get("english_latam_remote", {}).get("weight", 0.7)
        else:
            lang_weight = self.profile.get("candidate_accessibility", {}).get("spanish_local", {}).get("weight", 1.0)

        return round(geo_weight * lang_weight, 4)

    def evaluate_job(
        self,
        job_id: int,
        nombre_rol: str,
        market_tier: str,
        requisito_ingles: str,
        required_skills: List[str],
    ) -> Dict[str, Any]:
        """Aplica la fórmula de config/metrics.yaml para scoring técnico y brechas."""
        if not required_skills:
            return {
                "observacion_oferta_id": job_id,
                "skill_match_score": 0.0,
                "candidate_accessibility_index": self.calculate_accessibility_index(market_tier, requisito_ingles),
                "effective_match_score": 0.0,
                "matched_skills_count": 0,
                "missing_skills": [],
            }

        total_req = len(required_skills)
        matched_sum = 0.0
        missing_skills = []
        matched_count = 0

        for skill in required_skills:
            s_clean = skill.strip().lower()
            if s_clean in self.candidate_skills:
                matched_sum += self.candidate_skills[s_clean]
                matched_count += 1
            else:
                missing_skills.append(skill.strip())

        # Bono de alineación de rol
        role_bonus = 10.0 if (nombre_rol or "").lower() in self.target_roles else 0.0

        # Formula: min(100, (sum(candidate_confidence) / total_required) * 100 + role_bonus)
        base_score = (matched_sum / total_req) * 100.0
        skill_match_score = min(100.0, round(base_score + role_bonus, 2))
        
        access_index = self.calculate_accessibility_index(market_tier, requisito_ingles)
        effective_score = round(skill_match_score * access_index, 2)

        return {
            "observacion_oferta_id": job_id,
            "skill_match_score": skill_match_score,
            "candidate_accessibility_index": access_index,
            "effective_match_score": effective_score,
            "matched_skills_count": matched_count,
            "missing_skills_count": len(missing_skills),
            "missing_skills": missing_skills,
        }


def run_candidate_matcher_analysis():
    engine = get_sql_engine()
    matcher = CandidateMatcher()

    query = text("""
        SELECT 
            f.observacion_oferta_id,
            ISNULL(r.nombre_rol, 'Unclassified') AS nombre_rol,
            ISNULL(u.market_tier, 'Unclassified') AS market_tier,
            ISNULL(f.requisito_ingles, 'Not Specified') AS requisito_ingles,
            STRING_AGG(sk.nombre_skill, ',') AS skills_list
        FROM warehouse.fact_observacion_oferta f
        LEFT JOIN warehouse.dim_rol r ON f.rol_id = r.rol_id
        LEFT JOIN warehouse.dim_ubicacion u ON f.ubicacion_id = u.ubicacion_id
        LEFT JOIN warehouse.rel_oferta_skill ros ON f.observacion_oferta_id = ros.observacion_oferta_id
        LEFT JOIN warehouse.dim_skill sk ON ros.skill_id = sk.skill_id
        GROUP BY f.observacion_oferta_id, r.nombre_rol, u.market_tier, f.requisito_ingles;
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

        results = []
        for row in rows:
            skills = [s for s in (row.skills_list or "").split(",") if s]
            res = matcher.evaluate_job(
                job_id=row.observacion_oferta_id,
                nombre_rol=row.nombre_rol,
                market_tier=row.market_tier,
                requisito_ingles=row.requisito_ingles,
                required_skills=skills,
            )
            results.append(res)

    print(f"   ℹ️ Evaluadas {len(results)} ofertas en Candidate Matcher Engine.")
    if results:
        avg_effective = sum(r["effective_match_score"] for r in results) / len(results)
        print(f"   ℹ️ Promedio de Effective Match Score: {avg_effective:.2f}/100")

    return results


if __name__ == "__main__":
    run_candidate_matcher_analysis()