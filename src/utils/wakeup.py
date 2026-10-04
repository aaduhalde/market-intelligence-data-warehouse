# =============================================================================
# MARKET INTELLIGENCE DATA PLATFORM
# File: src/utils/wakeup.py
# Description: Script de calentamiento (warm-up) para despertar la API y Azure SQL
# =============================================================================

import sys
import time
import requests
from pathlib import Path

# Garantizar acceso a módulos internos si se ejecuta de forma independiente
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Cargar variables centralizadamente usando config_loader
from src.utils.config_loader import get_env_variable

DEFAULT_API_URL = "https://market-intel-api.azurewebsites.net"

# Obtención de variables
API_URL = get_env_variable("API_URL", DEFAULT_API_URL).rstrip("/")
SECRET_KEY = get_env_variable("MY_API_SECRET_KEY", default="")


def despertar_api_y_db() -> bool:
    print(f"Despertando servicios en: {API_URL}...")

    if not SECRET_KEY:
        print(
            "❌ Error: MY_API_SECRET_KEY no está definida en las variables de"
            " entorno."
        )
        return False

    headers = {"X-API-KEY": SECRET_KEY}
    intentos = 0
    max_intentos = 3
    espera_segundos = 20

    while intentos < max_intentos:
        intentos += 1
        try:
            print(
                f"   ℹ️ Petición de calentamiento (Intento"
                f" {intentos}/{max_intentos})..."
            )
            response = requests.get(
                f"{API_URL}/db/test-conexion", headers=headers, timeout=60
            )

            if response.status_code == 200:
                print("   ✅ ¡Éxito! La API y la base de datos están despiertas.")
                return True

            elif response.status_code == 403:
                print(
                    "   ⛔ App Service suspendido/detenido por cuota de CPU o API Key"
                    " inválida (HTTP 403)."
                )
                return False

            elif response.status_code == 503:
                print(
                    "   ⚠️ Servicio no disponible (HTTP 503). El App Service se está"
                    " reiniciando."
                )

            else:
                detalle_limpio = response.text[:100].replace("\n", " ")
                print(
                    f"   ⚠ Respuesta HTTP {response.status_code}. Detalle:"
                    f" {detalle_limpio}"
                )

        except requests.exceptions.Timeout:
            print(
                "   ⏳ Tiempo de espera agotado (60s). Azure SQL está completando el"
                " Auto-resume."
            )
        except Exception as e:
            print(f"   ⚠️ Error en la conexión: {type(e).__name__} - {e}")

        if intentos < max_intentos:
            print(f"   ℹ️ Esperando {espera_segundos}s antes del siguiente intento...")
            time.sleep(espera_segundos)

    print("   ❌ Error: No se pudo despertar el servicio tras varios intentos.")
    return False


if __name__ == "__main__":
    if not despertar_api_y_db():
        sys.exit(1)