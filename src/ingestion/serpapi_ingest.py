import os
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Set
from serpapi import GoogleSearch

from src.utils.config_loader import get_env_variable, load_yaml_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class JobMarketIngestion:
    def __init__(self, sources_config_path: str, force_full_refresh: bool = False):
        self.api_key = get_env_variable("SERPAPI_API_KEY")
        self.raw_data_dir = get_env_variable("RAW_DATA_PATH", "data/1_raw")
        self.sources_config = load_yaml_config(sources_config_path)
        
        self.source_settings = self._get_source_settings()
        self.incremental_cfg = self.source_settings.get("incremental", {})
        self.state_file = self.incremental_cfg.get("state_file", "data/ingestion_state.json")
        
        self.force_full_refresh = force_full_refresh
        self.processed_ids: Set[str] = set() if force_full_refresh else self._load_state()

        os.makedirs(self.raw_data_dir, exist_ok=True)

    def _get_source_settings(self) -> Dict[str, Any]:
        for src in self.sources_config.get("job_sources", []):
            if src.get("id") == "google_jobs":
                return src
        return {}

    def _load_state(self) -> Set[str]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("processed_job_ids", []))
            except Exception as e:
                logger.warning(f"No se pudo cargar el archivo de estado: {e}")
        return set()

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_update_utc": datetime.now(timezone.utc).isoformat(),
                "total_unique_jobs": len(self.processed_ids),
                "processed_job_ids": list(self.processed_ids)
            }, f, indent=2)

    def _determine_date_filter(self) -> str:
        if self.force_full_refresh or not os.path.exists(self.state_file):
            logger.info("Modo Full Refresh o primer run detectado: aplicando filtro 'month'")
            return "month"

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                last_update_str = state.get("last_update_utc")

            if not last_update_str:
                return "month"

            last_update = datetime.fromisoformat(last_update_str)
            now_utc = datetime.now(timezone.utc)
            delta_days = (now_utc - last_update).days

            if delta_days <= 1:
                filter_val = "today"
            elif delta_days <= 3:
                filter_val = "3days"
            elif delta_days <= 7:
                filter_val = "week"
            else:
                filter_val = "month"

            logger.info(f"Última ingesta hace {delta_days} días. Filtro incremental asignado: '{filter_val}'")
            return filter_val

        except Exception as e:
            logger.warning(f"Error determinando filtro incremental ({e}). Fallback a 'week'")
            return "week"

    def execute_ingestion(self):
        date_posted_filter = self._determine_date_filter()
        search_groups = self.source_settings.get("search_groups", {})
        role_groups = search_groups.get("roles", [])
        markets = search_groups.get("markets", [])

        logger.info(f"Iniciando ingesta optimizada. Ventana de tiempo: '{date_posted_filter}'")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        total_api_calls = 0

        for market in markets:
            market_name = market.get("name")
            location = market.get("location")
            gl_code = market.get("gl", "us")
            hl_code = market.get("hl", "es")
            is_remote = market.get("remote_only", False)

            for role_group in role_groups:
                group_name = role_group["name"]
                base_query = role_group["query"]

                query_str = f"{base_query} remoto" if is_remote else base_query

                params = {
                    "engine": "google_jobs",
                    "q": query_str,
                    "location": location,
                    "gl": gl_code,
                    "hl": hl_code,
                    "api_key": self.api_key
                }

                if self.incremental_cfg.get("enabled", True) and date_posted_filter != "month":
                    params["chips"] = f"date_posted:{date_posted_filter}"

                try:
                    logger.info(f"Llamada API #{total_api_calls + 1}: Mercado='{market_name}' | Grupo='{group_name}' | Location='{location}' (gl={gl_code}) | Query='{query_str}'")
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    total_api_calls += 1

                    error_msg = results.get("error")
                    if error_msg:
                        logger.warning(f"Sin resultados en SerpAPI para [{group_name} - {market_name}]: {error_msg}")
                        continue

                    raw_jobs = results.get("jobs_results", [])

                    if not raw_jobs:
                        logger.warning(f"La API respondió sin 'jobs_results' para [{group_name} - {market_name}]")
                        continue

                    new_jobs = []
                    for job in raw_jobs:
                        job_id = job.get("job_id") or f"{job.get('title')}_{job.get('company_name')}"
                        if job_id not in self.processed_ids:
                            new_jobs.append(job)
                            self.processed_ids.add(job_id)

                    if new_jobs:
                        results["jobs_results"] = new_jobs
                        results["_pipeline_metadata"] = {
                            "ingestion_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                            "search_group": group_name,
                            "target_market": market_name,
                            "target_location": location,
                            "date_filter_applied": date_posted_filter,
                            "new_records_count": len(new_jobs),
                            "provider": "serpapi"
                        }

                        sanitized_market = market_name.lower().replace(" ", "_")
                        file_name = f"raw_{sanitized_market}_{group_name}_{timestamp}.json"
                        file_path = os.path.join(self.raw_data_dir, file_name)

                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)

                        logger.info(f"Guardados {len(new_jobs)} registros en: {file_path}")
                    else:
                        logger.info(f"Skipping [{group_name} - {market_name}]: Registros duplicados en el estado.")

                except Exception as e:
                    logger.error(f"Error inesperado procesando [{group_name} - {market_name}]: {str(e)}")

        self._save_state()
        logger.info(f"Ingesta optimizada finalizada. Total de consultas consumidas a SerpAPI: {total_api_calls}")


def ejecutar_ingesta(sources_config_path: str = "config/sources.yaml", force_full_refresh: bool = False):
    """Función de entrada expuesta para invocar la ingesta desde main.py."""
    ingestor = JobMarketIngestion(
        sources_config_path=sources_config_path,
        force_full_refresh=force_full_refresh
    )
    ingestor.execute_ingestion()


if __name__ == "__main__":
    ejecutar_ingesta()