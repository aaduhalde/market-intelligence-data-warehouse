# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/config_loader.py
# Description: Cargador de variables de entorno (.env) y configuraciones en /config
# =============================================================================

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Configuraciones (market-intelligence-data-warehouse)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"

# Cargar explícitamente el archivo .env desde la raíz
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_env_variable(var_name: str, default: str = None) -> str:
    """
    Obtiene una variable de entorno (.env local o Secret de GitHub Actions).
    Lanza un ValueError si la variable es crítica y no está definida.
    """
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(f"CRITICAL: La variable de entorno '{var_name}' no está configurada.")
    return value


def load_yaml_config(file_path: str | Path) -> Dict[str, Any]:
    """
    Carga un archivo YAML pasando una ruta relativa, absoluta o dentro de /config.
    """
    path = Path(file_path)
    
    # Si la ruta no es absoluta, buscar primero desde ROOT_DIR
    if not path.is_absolute():
        path = ROOT_DIR / path

    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config_from_dir(filename: str) -> Dict[str, Any]:
    """
    Helper para cargar directo cualquier archivo dentro de la carpeta /config/
    Ejemplo: load_config_from_dir("skills.yaml")
    """
    return load_yaml_config(CONFIG_DIR / filename)