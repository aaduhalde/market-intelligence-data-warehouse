from datetime import datetime, timedelta
import glob
import hashlib
import json
import logging
import os
import re
import pandas as pd
import yaml

# Configuración de logs
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Rutas de arquitectura de datos
DIR_RAW = os.path.join("data", "1_raw")
DIR_STAGED = os.path.join("data", "2_staged")
FILE_STAGED_DESTINO = os.path.join(DIR_STAGED, "vacantes_staged.parquet")
FILE_ROLES_YAML = os.path.join("config", "roles.yaml")
FILE_SOURCES_YAML = os.path.join("config", "sources.yaml")
FILE_SKILLS_YAML = os.path.join("config", "skills.yaml")


def cargar_skills_taxonomy() -> list:
    """Carga config/skills.yaml y devuelve una lista única de skills a buscar."""
    if not os.path.exists(FILE_SKILLS_YAML):
        logger.warning(f"No se encontró {FILE_SKILLS_YAML}")
        return []

    try:
        with open(FILE_SKILLS_YAML, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            taxonomy = cfg.get("skill_taxonomy", {})
            skills_set = set()
            for categoria, lista_skills in taxonomy.items():
                if isinstance(lista_skills, list):
                    for skill in lista_skills:
                        skills_set.add(skill)
            return sorted(list(skills_set), key=len, reverse=True)
    except Exception as e:
        logger.warning(f"Error cargando {FILE_SKILLS_YAML}: {e}")
        return []


def extraer_skills(texto_buscar: str, lista_skills: list) -> str:
    """
    Escanea el texto en busca de las habilidades definidas en config/skills.yaml.
    Retorna un JSON string con las skills encontradas o 'No data' si no hay coincidencias.
    """
    if not texto_buscar or not isinstance(texto_buscar, str) or not lista_skills:
        return "No data"

    encontradas = set()
    texto_lower = texto_buscar.lower()

    for skill in lista_skills:
        skill_clean = skill.strip()
        # Escapa caracteres especiales (ej: T-SQL, PL/SQL, etc.)
        pattern = rf"\b{re.escape(skill_clean.lower())}\b"
        if re.search(pattern, texto_lower):
            encontradas.add(skill_clean)

    if encontradas:
        return json.dumps(sorted(list(encontradas)), ensure_ascii=False)
    
    return "No data"


def cargar_mercados_config() -> dict:
    """
    Carga config/sources.yaml y retorna:
    - mercados: mapa {nombre_lowercase: Nombre_Normalizado}
    - lista_paises: lista de países configurados para matching dinámico
    """
    if not os.path.exists(FILE_SOURCES_YAML):
        return {}

    try:
        with open(FILE_SOURCES_YAML, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            job_sources = cfg.get("job_sources", [])
            mercados = {}
            for src in job_sources:
                for group, details in src.get("search_groups", {}).items():
                    if group == "markets":
                        for m in details:
                            # Extrae el país base (ej. "Peru" de "Peru" o "Peru_Remote")
                            nombre_mercado = m.get("location", m["name"])
                            pais_base = nombre_mercado.split("_")[0].strip()
                            mercados[pais_base.lower()] = pais_base
            return mercados
    except Exception as e:
        logger.warning(f"No se pudo cargar {FILE_SOURCES_YAML}: {e}")
        return {}


def cargar_roles_taxonomy() -> list:
    """Carga config/roles.yaml preservando la jerarquía de prioridad."""
    if not os.path.exists(FILE_ROLES_YAML):
        return []

    try:
        with open(FILE_ROLES_YAML, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            taxonomy = cfg.get("role_taxonomy", {})
            
            roles_ordenados = []
            for familia in ["primary", "secondary", "legacy_leverage"]:
                for r in taxonomy.get(familia, []):
                    roles_ordenados.append((r, familia))
            return roles_ordenados
    except Exception as e:
        logger.warning(f"No se pudo cargar {FILE_ROLES_YAML}: {e}")
        return []


def clasificar_rol_y_familia(titulo: str, roles_ordenados: list) -> tuple:
    """Clasifica rol y familia según la prioridad definida en roles.yaml."""
    if not titulo or not isinstance(titulo, str):
        return "Other / Unclassified", "Unclassified"

    t_lower = titulo.lower()
    for role_name, familia in roles_ordenados:
        pattern = rf"\b{re.escape(role_name.lower())}\b"
        if re.search(pattern, t_lower):
            return role_name, familia

    return "Other / Unclassified", "Unclassified"


def parsear_ubicacion_raw(ubicacion_raw: str, archivo_origen: str = "") -> tuple:
    """
    Parsea ubicacion_raw en (ciudad, pais) de forma dinámica usando la lista
    de países configurados en sources.yaml e inferencia por archivo/remoto.
    """
    if not ubicacion_raw or not isinstance(ubicacion_raw, str):
        return "No especificado", "No especificado"

    paises_config = cargar_mercados_config()
    
    sinonimos_paises = {
        "peru": "Peru", "perú": "Peru",
        "mexico": "Mexico", "méxico": "Mexico",
        "argentina": "Argentina", "chile": "Chile", "colombia": "Colombia"
    }
    paises_conocidos = {**sinonimos_paises, **paises_config}

    # 1. Limpiar sufijos de agregadores
    texto_limpio = re.sub(r"\s*\([^)]*ubicacion[es]*[^)]*\)", "", ubicacion_raw, flags=re.IGNORECASE).strip()
    texto_limpio = re.sub(r"\s*\(\+\d+.*\)", "", texto_limpio).strip()

    # 2. Manejo de trabajo Remoto
    if any(k in texto_limpio.lower() for k in ["remoto", "remote", "trabajo desde casa"]):
        for p_key, p_val in paises_conocidos.items():
            if re.search(rf"\b{re.escape(p_key)}\b", texto_limpio.lower()):
                return "Remoto", p_val
        return "Remoto", "Remoto"

    partes = [p.strip() for p in texto_limpio.split(",") if p.strip()]
    pais_encontrado = "No especificado"
    ciudad = partes[0] if partes else "No especificado"

    # 3. Escaneo dinámico de País
    for parte in reversed(partes):
        parte_lower = parte.lower()
        if parte_lower in paises_conocidos:
            pais_encontrado = paises_conocidos[parte_lower]
            break
        for p_key, p_val in paises_conocidos.items():
            if re.search(rf"\b{re.escape(p_key)}\b", parte_lower):
                pais_encontrado = p_val
                break
        if pais_encontrado != "No especificado":
            break

    # 4. Inferencia por nombre de archivo origen
    if pais_encontrado == "No especificado" and archivo_origen:
        archivo_lower = archivo_origen.lower()
        for p_key, p_val in paises_conocidos.items():
            if p_key in archivo_lower:
                pais_encontrado = p_val
                break

    if ciudad.lower() in paises_conocidos:
        ciudad = "No especificado"

    return ciudad, pais_encontrado


def extraer_seniority(texto: str) -> str:
    if not texto or not isinstance(texto, str):
        return "No data"
    t = texto.lower()
    if re.search(r"\b(sr|senior|lead|principal)\b", t):
        return "Senior"
    elif re.search(r"\b(semi[- ]?senior|ssr|mid[- ]?level|mid)\b", t):
        return "Semi-Senior"
    elif re.search(r"\b(jr|junior|trainee|entry[- ]?level)\b", t):
        return "Junior"
    return "No data"


def extraer_requisito_ingles(texto: str) -> str:
    if not texto or not isinstance(texto, str):
        return "No data"
    t = texto.lower()
    if re.search(r"\b(english|inglés|ingles|bilingual|bilingüe|advanced english|c1|b2)\b", t):
        return "Requerido"
    return "No data"


def generar_hash_id(cadena_original: str) -> str:
    if not cadena_original:
        return ""
    return hashlib.md5(cadena_original.encode("utf-8")).hexdigest()


def parse_relative_date(posted_at_str: str, base_date: datetime) -> str:
    if not posted_at_str or not isinstance(posted_at_str, str):
        return base_date.strftime("%Y-%m-%d")

    text = posted_at_str.lower().strip()

    if any(k in text for k in ["hora", "minuto", "segundo", "hour", "minute", "second"]):
        return base_date.strftime("%Y-%m-%d")
    elif "ayer" in text or "yesterday" in text:
        return (base_date - timedelta(days=1)).strftime("%Y-%m-%d")

    match = re.search(r"\d+", text)
    if match:
        num = int(match.group())
        if "día" in text or "day" in text:
            target_date = base_date - timedelta(days=num)
        elif "semana" in text or "week" in text:
            target_date = base_date - timedelta(weeks=num)
        elif "mes" in text or "month" in text:
            target_date = base_date - timedelta(days=num * 30)
        else:
            target_date = base_date
        return target_date.strftime("%Y-%m-%d")

    return base_date.strftime("%Y-%m-%d")


def extraer_y_validar_vacantes(ruta_json: str) -> list:
    vacantes_validas = []
    roles_ordenados = cargar_roles_taxonomy()
    skills_taxonomy = cargar_skills_taxonomy()
    nombre_archivo = os.path.basename(ruta_json)

    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_created_at = data.get("search_metadata", {}).get("created_at")
        if raw_created_at:
            try:
                clean_date_str = raw_created_at.replace(" UTC", "").strip()
                fecha_scrapeo_dt = datetime.strptime(
                    clean_date_str, "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                fecha_scrapeo_dt = datetime.utcnow()
        else:
            fecha_scrapeo_dt = datetime.utcnow()

        fecha_scrapeo_str = fecha_scrapeo_dt.strftime("%Y-%m-%d %H:%M:%S")

        KEYWORDS_TIPO_TRABAJO = [
            "tiempo completo", "tiempo parcial", "medio tiempo", "con contrato",
            "por contrato", "contrato", "prácticas", "practicas", "pasantía",
            "pasantia", "jornada completa", "jornada parcial", "full-time",
            "part-time", "contract", "internship", "temporal", "freelance",
        ]

        jobs_raw = data.get("jobs_results", [])
        for job in jobs_raw:
            raw_job_id = job.get("job_id") or f"{job.get('title')}_{job.get('company_name')}"
            titulo = job.get("title")
            fuente = job.get("via")

            if not raw_job_id or not str(raw_job_id).strip():
                continue
            if not titulo or not str(titulo).strip():
                continue
            if not fuente or not str(fuente).strip():
                continue

            job_id_corto = generar_hash_id(str(raw_job_id).strip())

            apply_options = job.get("apply_options", [])
            link_postulacion = (
                apply_options[0].get("link")
                if apply_options
                else job.get("share_link")
            )

            det_ext = job.get("detected_extensions", {})
            ext_list = job.get("extensions", [])
            if not isinstance(ext_list, list):
                ext_list = [str(ext_list)] if ext_list else []

            # Tipo de trabajo
            tipo_trabajo = det_ext.get("schedule_type")
            if not tipo_trabajo:
                for item in ext_list:
                    item_clean = str(item).strip()
                    if any(kw in item_clean.lower() for kw in KEYWORDS_TIPO_TRABAJO):
                        tipo_trabajo = item_clean
                        break

            if not tipo_trabajo:
                tipo_trabajo = "No especificado"

            # Fecha de publicación
            posted_at_texto = det_ext.get("posted_at")
            if not posted_at_texto:
                for item in ext_list:
                    item_str = str(item).lower()
                    if any(
                        t in item_str
                        for t in ["hace", "ayer", "ago", "yesterday", "día", "días", "semana", "mes"]
                    ):
                        posted_at_texto = item
                        break

            fecha_publicacion = parse_relative_date(posted_at_texto, fecha_scrapeo_dt)

            # Enriquecimiento de taxonomía, ubicación, seniority e inglés
            ubicacion_raw = job.get("location", "No especificado")
            ciudad, pais = parsear_ubicacion_raw(ubicacion_raw, nombre_archivo)
            nombre_rol, familia_rol = clasificar_rol_y_familia(titulo, roles_ordenados)
            seniority = extraer_seniority(titulo)
            requisito_ingles = extraer_requisito_ingles(titulo)

            # Construcción de bolsa de texto para auditar skills (Título + Descripción/Snippet + Metadatos)
            descripcion = job.get("description", "") or job.get("snippet", "")
            texto_completo_job = f"{titulo} {descripcion} {' '.join(ext_list)}"
            skills_array = extraer_skills(texto_completo_job, skills_taxonomy)

            vacantes_validas.append(
                {
                    "job_id": job_id_corto,
                    "titulo_vacante": str(titulo).strip(),
                    "nombre_rol": nombre_rol,
                    "familia_rol": familia_rol,
                    "empresa": job.get("company_name", "No especificado"),
                    "ubicacion": ubicacion_raw,
                    "ciudad": ciudad,
                    "pais": pais,
                    "seniority": seniority,
                    "requisito_ingles": requisito_ingles,
                    "tipo_trabajo": str(tipo_trabajo).strip(),
                    "portal_fuente": str(fuente).strip(),
                    "fecha_scrapeo": fecha_scrapeo_str,
                    "fecha_publicacion": fecha_publicacion,
                    "link_postulacion_directa": link_postulacion,
                    "skills_array": skills_array,
                    "archivo_origen": nombre_archivo,
                }
            )
    except Exception as e:
        logger.error(f"Error procesando {ruta_json}: {e}")

    return vacantes_validas


def procesar_incremental(
    dir_raw: str = DIR_RAW,
    dir_staged: str = DIR_STAGED,
    archivo_destino: str = FILE_STAGED_DESTINO,
):
    os.makedirs(dir_staged, exist_ok=True)

    df_existente = pd.DataFrame()
    ids_existentes = set()

    if os.path.exists(archivo_destino):
        try:
            df_existente = pd.read_parquet(archivo_destino)
            ids_existentes = set(df_existente["job_id"].dropna().unique())
            logger.info(
                f"Staged existente detectado con {len(ids_existentes)} registros."
            )
        except Exception as e:
            logger.warning(
                f"No se pudo leer el archivo staged existente, se creará uno nuevo: {e}"
            )

    archivos_json = glob.glob(os.path.join(dir_raw, "*.json"))

    if not archivos_json:
        logger.info(f"No se encontraron archivos .json en '{dir_raw}'.")
        return

    registros_nuevos = []

    for archivo in archivos_json:
        vacantes = extraer_y_validar_vacantes(archivo)
        for vacante in vacantes:
            if vacante["job_id"] not in ids_existentes:
                registros_nuevos.append(vacante)
                ids_existentes.add(vacante["job_id"])

    if registros_nuevos:
        df_nuevos = pd.DataFrame(registros_nuevos)

        if not df_existente.empty:
            df_consolidado = pd.concat(
                [df_existente, df_nuevos], ignore_index=True
            )
        else:
            df_consolidado = df_nuevos

        df_consolidado["fecha_scrapeo"] = pd.to_datetime(
            df_consolidado["fecha_scrapeo"]
        )
        df_consolidado["fecha_publicacion"] = pd.to_datetime(
            df_consolidado["fecha_publicacion"]
        )

        df_consolidado.to_parquet(archivo_destino, index=False)

        print("\n" + "=" * 50)
        print("DATA QUALITY & STAGING")
        print("=" * 50)
        print(f" Archivos JSON leídos   : {len(archivos_json)}")
        print(f" Registros agregados   : {len(registros_nuevos)}")
        print(f" Total acumulado Staged: {len(df_consolidado)}")
        print(f" Guardado en            : {archivo_destino}")
        print("=" * 50 + "\n")
    else:
        logger.info(
            "Sin cambios: No se encontraron vacantes nuevas o válidas para agregar."
        )


if __name__ == "__main__":
    procesar_incremental()