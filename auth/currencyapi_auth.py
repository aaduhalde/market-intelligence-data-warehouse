import os
import json
from pathlib import Path


LOCAL_KEY_PATH = Path(
    "/home/aadm/GIT/aaduhalde/aaduhalde_api/currencyapi.json"
)

ENV_VAR_NAME = "CURRENCYAPI_KEY"


def load_currencyapi_key() -> str:
    """
    Prioridad:
    1. Variable de entorno (GitHub Actions / Prod)
    2. Archivo local JSON (Dev local)
    """

    # Variable de entorno
    api_key = os.getenv(ENV_VAR_NAME)
    if api_key:
        return api_key.strip()

    # Archivo local
    if LOCAL_KEY_PATH.exists():
        with LOCAL_KEY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        key = data.get("currencyapi_key")
        if key:
            return key.strip()

    raise RuntimeError(
        "CurrencyAPI key no encontrada. "
        "Defina la variable de entorno CURRENCYAPI_KEY "
        "o configure el archivo currencyapi.json"
    )
