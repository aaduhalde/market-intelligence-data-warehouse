# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/ingestion/load_warehouse.py
# Description: Módulo de carga: Parquet -> Staging -> Data Warehouse
# =============================================================================

import os
import json
import logging
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text, VARCHAR, DATE, INT

# Garantizar que ROOT_DIR esté en sys.path para importaciones relativas/absolutas
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Importar utilidades centralizadas de configuración y base de datos
from src.utils.config_loader import load_yaml_config, load_config_from_dir
from src.utils.db_connector import get_sql_engine
from src.utils.init_db import execute_sql_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _normalizar_skills_json(val):
    if val is None or pd.isna(val) or val == "No data":
        return None

    if isinstance(val, str):
        val_clean = val.strip()
        if val_clean.startswith("[") and val_clean.endswith("]"):
            try:
                parsed = json.loads(val_clean)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return json.dumps(parsed, ensure_ascii=False)
                return None
            except json.JSONDecodeError:
                return None
        return None

    if isinstance(val, (list, tuple, pd.Series)) or hasattr(val, "tolist"):
        lista_elementos = val.tolist() if hasattr(val, "tolist") else list(val)
        elementos_filtrados = [str(x).strip() for x in lista_elementos if x and x != "No data"]
        if len(elementos_filtrados) > 0:
            return json.dumps(elementos_filtrados, ensure_ascii=False)

    return None


def load_skills_taxonomy_to_staging(engine) -> None:
    """Lee config/skills.yaml y carga la tabla de referencia staging.stg_skill_taxonomy."""
    try:
        data = load_config_from_dir("skills.yaml")
    except FileNotFoundError:
        logger.warning("No se encontró el archivo de taxonomía: config/skills.yaml")
        return

    taxonomy = data.get("skill_taxonomy", {})
    records = []

    for categoria, skills in taxonomy.items():
        if isinstance(skills, list):
            for skill in skills:
                if skill:
                    records.append({
                        "nombre_skill": str(skill).strip(),
                        "categoria_skill": str(categoria).strip()
                    })

    df_taxonomy = pd.DataFrame(records)

    with engine.connect() as conn:
        conn.execute(text("""
            IF OBJECT_ID('staging.stg_skill_taxonomy', 'U') IS NOT NULL
                DROP TABLE staging.stg_skill_taxonomy;

            CREATE TABLE staging.stg_skill_taxonomy (
                nombre_skill VARCHAR(255),
                categoria_skill VARCHAR(100)
            );
        """))
        if getattr(conn, "commit", None):
            conn.commit()

    if not df_taxonomy.empty:
        df_taxonomy.to_sql(
            name="stg_skill_taxonomy",
            con=engine,
            schema="staging",
            if_exists="append",
            index=False,
            dtype={
                "nombre_skill": VARCHAR(255),
                "categoria_skill": VARCHAR(100)
            }
        )
        logger.info(f"Cargadas {len(df_taxonomy)} reglas de taxonomía en staging.stg_skill_taxonomy.")


def load_parquet_to_staging(parquet_path: Path, engine) -> int:
    if not parquet_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo Staged: {parquet_path}")

    logger.info(f"Leyendo dataset Parquet desde: {parquet_path.relative_to(ROOT_DIR)}")
    df = pd.read_parquet(parquet_path)

    if df.empty:
        logger.warning("El archivo Parquet está vacío. Omitiendo carga...")
        return 0

    column_mapping = {
        "job_id": "source_job_id",
        "titulo_vacante": "titulo_puesto",
        "empresa": "nombre_empresa",
        "ubicacion": "ubicacion_raw",
        "tipo_trabajo": "modalidad_trabajo",
        "portal_fuente": "plataforma_origen",
        "fecha_scrapeo": "fecha_captura",
        "link_postulacion_directa": "url_oferta"
    }
    df = df.rename(columns=column_mapping)

    df["proveedor_ingesta"] = "SerpApi"
    df["nombre_empresa_raw"] = df["nombre_empresa"]

    df["fecha_captura"] = pd.to_datetime(df["fecha_captura"])
    df["fecha_captura_id"] = df["fecha_captura"].dt.strftime("%Y%m%d").astype(int)
    df["fecha_captura"] = df["fecha_captura"].dt.date

    if "fecha_publicacion" in df.columns:
        df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")
        df["fecha_publicacion_id"] = (
            df["fecha_publicacion"]
            .dt.strftime("%Y%m%d")
            .fillna(0)
            .astype(int)
            .replace(0, None)
        )
        df["fecha_publicacion"] = df["fecha_publicacion"].dt.date
    else:
        df["fecha_publicacion"] = None
        df["fecha_publicacion_id"] = None

    if "skills_array" in df.columns:
        df["skills_array"] = df["skills_array"].apply(_normalizar_skills_json)
    else:
        df["skills_array"] = None

    columnas_opcionales = [
        "ciudad", "pais", "nombre_rol", "familia_rol", 
        "seniority", "requisito_ingles", "search_query", "descripcion_oferta"
    ]
    for col in columnas_opcionales:
        if col not in df.columns:
            df[col] = None

    if "market_tier" not in df.columns:
        df["market_tier"] = "Unclassified"

    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE staging.stg_observacion_oferta;"))
        if getattr(conn, "commit", None):
            conn.commit()

    # 1. Cargar la taxonomía de skills a staging
    load_skills_taxonomy_to_staging(engine)

    logger.info(f"Cargando {len(df)} registros en staging.stg_observacion_oferta...")

    sql_dtypes = {
        "proveedor_ingesta": VARCHAR(50),
        "source_job_id": VARCHAR(1000),
        "titulo_puesto": VARCHAR(255),
        "nombre_empresa": VARCHAR(255),
        "nombre_empresa_raw": VARCHAR(255),
        "ubicacion_raw": VARCHAR(255),
        "ciudad": VARCHAR(100),
        "pais": VARCHAR(100),
        "market_tier": VARCHAR(50),
        "modalidad_trabajo": VARCHAR(50),
        "nombre_rol": VARCHAR(150),
        "familia_rol": VARCHAR(50),
        "seniority": VARCHAR(50),
        "requisito_ingles": VARCHAR(50),
        "fecha_captura": DATE(),
        "fecha_captura_id": INT(),
        "fecha_publicacion": DATE(),
        "fecha_publicacion_id": INT(),
        "plataforma_origen": VARCHAR(100),
        "search_query": VARCHAR(500),
        "descripcion_oferta": VARCHAR(None),
        "url_oferta": VARCHAR(None),
        "skills_array": VARCHAR(None),
    }

    df_staging = df[list(sql_dtypes.keys())]

    df_staging.to_sql(
        name="stg_observacion_oferta",
        con=engine,
        schema="staging",
        if_exists="append",
        index=False,
        chunksize=1000,
        dtype=sql_dtypes
    )

    logger.info("Carga en Staging completada con éxito.")
    return len(df_staging)


def run_dw_transformation(engine) -> None:
    sql_script = ROOT_DIR / "sql" / "staging" / "01_load_dw_from_staging.sql"
    logger.info("Iniciando transformación ETL de Staging al Modelo Estrella...")
    execute_sql_file(sql_script, engine)
    logger.info("Transformación y carga del Data Warehouse finalizada con éxito.")


def execute_loading() -> None:
    parquet_file = ROOT_DIR / "data" / "2_staged" / "vacantes_staged.parquet"
    engine = get_sql_engine()

    records_loaded = load_parquet_to_staging(parquet_file, engine)
    if records_loaded > 0:
        run_dw_transformation(engine)


if __name__ == "__main__":
    execute_loading()