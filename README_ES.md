# Market Intelligence Data Warehouse
### End-to-End Analytics Platform | Data Engineering, Data Modeling & Business Intelligence

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server_Local-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![T-SQL](https://img.shields.io/badge/T--SQL-5C2D91?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C94C?style=for-the-badge&logo=power-bi&logoColor=black)

---

## Resumen del Proyecto

Este proyecto implementa una plataforma de datos end-to-end (**Market Intelligence Data Platform**) orientada a capturar, procesar, modelar y analizar el mercado laboral tecnológico en LATAM (con foco en Perú y Argentina, incluyendo modalidades remotas y presenciales/híbridas).

Transforma datos de ofertas de empleo obtenidas vía **SerpAPI (Google Jobs)** o archivos crudos locales en un **Data Warehouse analítico (Modelo Estrella)** desplegado en **SQL Server Local (`JobMarketDB`)**, con validaciones de calidad de datos, motor de *matching* para el perfil del candidato y exportación a CSV para análisis y consumo en **Power BI**.

---

## Arquitectura y Flujo de Datos (Fases 0 a 9)

```text
  [ SerpAPI / Raw JSON locales ]
               │
               ▼
1. Ingesta Condicional (RUN_SERPAPI_INGEST) ──► data/1_raw/*.json & data/ingestion_state.json
               │
               ▼
2. Procesamiento & Normalización           ──► data/2_staged/vacantes_staged.parquet
               │
               ▼
3. Setup SQL Server Local (JobMarketDB)    ──► Esquemas: staging, warehouse, analytics
               │
               ▼
4. Carga Staging & ETL Modelo Estrella      ──► staging.stg_* ─► warehouse.fact_* & Dims
               │
               ▼
5. Auditoría de Calidad (Data Quality)     ──► Unicidad, FK/huérfanos, M:N y taxonomía skills
               │
               ▼
6. Capa Analítica & Candidate Matcher       ──► analytics.vw_* & CandidateMatcher
               │
               ▼
7. Exportación & Reconciliación CSV        ──► data/3_csv/*.csv (Power BI / BI)
```

---

## Configuración del Entorno Local (`.env`)

Crea o ajusta el archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# SerpAPI Credential
SERPAPI_API_KEY=TUS DATOS
RUN_SERPAPI_INGEST=N
# Recordar pasar el flag a Y para consumir la API; en N reutiliza los JSON locales en data/1_raw

# Pipeline Settings
RAW_DATA_PATH=data/1_raw

# SQL Server Local
DB_SERVER=localhost
DB_NAME=JobMarketDB
DB_USER=TUS DATOS
DB_PASSWORD=TUS DATOS
DB_PORT=1433
DB_DRIVER=ODBC Driver 18 for SQL Server
```

---

## Ejecución del Pipeline

El orquestador central (`main.py`) permite ejecutar el pipeline completo con *gate control* (detiene la ejecución si una fase falla) o ejecutar una fase específica de forma aislada:

```bash
# Ejecutar todas las fases en secuencia (Fases 0 a 9)
python main.py --all

# Ejecutar una fase específica de forma aislada (0 a 9)
python main.py --phase 0
python main.py --phase 2
python main.py --phase 5
```

---

## Reglas de Negocio Clave (Business Rules)

- **Deduplicación e Identificador (`BR-001` / `BR-012`)**: Generación de hash determinista (`job_id`) y restricción de unicidad por snapshot (`proveedor_ingesta`, `source_job_id`, `fecha_captura_id`).
- **Taxonomía de Roles y Skills (`BR-004` / `BR-015` / `BR-017`)**: Clasificación estandarizada de roles (`primary`, `secondary`, `legacy_leverage`) según `config/roles.yaml` y extracción de habilidades técnicas mediante regex contra `config/skills.yaml`, enriquecidas dinámicamente en `warehouse.dim_skill`.
- **Geografía y Prioridad de Mercado (`BR-006` / `BR-007`)**: Normalización de ubicación (`ciudad`, `pais`, `market_tier`) conservando el valor original `ubicacion_raw`.
- **Candidate Matching Engine (`BR-020` / `BR-021`)**: Motor de cálculo de ajuste candidato vs. oferta (`skill_match_score`, `candidate_accessibility_index` combinando geografía e idioma, y `effective_match_score`) basado en `config/candidate_profile.yaml` y `config/metrics.yaml`.
- **Calidad de Datos y Reconciliación (`BR-025`)**: Validaciones automatizadas en cada fase (integridad referencial, unicidad M:N, cobertura de taxonomías) y conciliación fila a fila y de esquema entre SQL Server Local y `data/3_csv/`.

---

## Estructura del Repositorio

```text
market-intelligence-jobs/
├── .github/workflows/     # CI/CD: Workflow de pipeline en GitHub Actions
├── config/                # candidate_profile.yaml, metrics.yaml, roles.yaml, skills.yaml, sources.yaml
├── data/
│   ├── 1_raw/             # Respuestas JSON crudas de SerpAPI
│   ├── 2_staged/          # Dataset intermedio normalizado (vacantes_staged.parquet)
│   ├── 3_csv/             # Exportaciones CSV de tablas y vistas (esquema_objeto.csv)
│   └── ingestion_state.json
├── data_specification/    # business_rules.md y taxonomy.md
├── project_specification/ # business_requirements.md y project_definition.md
├── sql/
│   ├── warehouse/         # 01_database_setup.sql, 02_star_schema.sql
│   ├── staging/           # 01_load_dw_from_staging.sql
│   └── analytics/         # 01_create_analytics_views.sql
├── src/
│   ├── analytics/         # init_analytics.py, candidate_matcher.py
│   ├── export/            # export_tables_to_csv.py
│   ├── ingestion/         # serpapi_ingest.py, procesar_vacantes.py, load_warehouse.py
│   ├── phases/            # phase0_env.py a phase9_export.py (Quality Gates)
│   └── utils/             # config_loader.py, db_connector.py, init_db.py
├── main.py                # Orquestador CLI por fases (--phase / --all)
└── requirements.txt       # Dependencias del proyecto
```

---

## Módulos Destacados

- **Ingesta Incremental y Controlada por Flag (`serpapi_ingest.py` + `phase2_ingestion.py`)**: Respeta `RUN_SERPAPI_INGEST` (`Y`/`N`), mantiene el estado en `data/ingestion_state.json` y ajusta la ventana temporal (`today`, `3days`, `week`, `month`) según los días transcurridos desde la última ingesta.
- **Procesamiento y Staging en Parquet (`procesar_vacantes.py`)**: Extrae skills, clasifica roles, parsea ubicaciones y fechas relativas, detecta seniority y requisito de inglés, y deduplica incrementalmente sobre `data/2_staged/vacantes_staged.parquet`.
- **Carga Set-Based a Modelo Estrella (`load_warehouse.py` + `01_load_dw_from_staging.sql`)**: Carga `staging.stg_observacion_oferta` y `staging.stg_skill_taxonomy`, y puebla dimensiones (`dim_empresa`, `dim_ubicacion`, `dim_rol`, `dim_modalidad`, `dim_skill`, `dim_fecha`), tabla de hechos (`fact_observacion_oferta`) y tabla puente (`rel_oferta_skill`).
- **Candidate Matcher (`candidate_matcher.py`)**: Evalúa cada oferta del Data Warehouse contra el perfil del candidato y calcula puntuaciones efectivas y brechas de habilidades.

---

## Guía de Pruebas y Auditoría por Fase (`src/phases/`)

Cada fase ejecuta una batería de verificaciones con salida `[PASS]` / `[FAIL]`. A continuación se detalla qué audita cada fase y qué puntos se pueden modificar o ajustar según las necesidades del proyecto:

| Fase | Script | Pruebas Actuales (`P*-*`) | Puntos de Ajuste, Corrección o Auditoría |
| :--- | :--- | :--- | :--- |
| **Fase 0** | `phase0_env.py` | Python $\ge 3.10$, `requirements.txt`, paquetes críticos, directorios, YAMLs, sintaxis de `src/`, imports y `.env` (`DB_SERVER`, `DB_NAME`). | **En `P0-09`**: Ampliar la validación para exigir también `DB_USER`, `DB_PASSWORD`, `DB_PORT` y `DB_DRIVER`.<br>**En `P0-05`**: Ajustar `required_dirs` si no se requiere `images/`. |
| **Fase 1** | `phase1_config.py` | Sintaxis y claves raíz de los 5 YAMLs, unicidad de roles/skills, categorías, métricas y rangos `[0.0, 1.0]` en `candidate_profile.yaml`. | **En `P1-04/05` y `P1-06/07`**: Normalizar con `.strip().lower()` para detectar duplicados insensibles a mayúsculas.<br>**En `P1-08`**: Validar explícitamente las claves de métricas esperadas (`skill_match_score`, `effective_match_score`, etc.). |
| **Fase 2** | `phase2_ingestion.py` | Flag `RUN_SERPAPI_INGEST` (`Y`/`N`), presencia y JSON válido en `data/1_raw/*.json`, esquema `jobs_results`, campos mínimos y `ingestion_state.json`. | **En `P2-03`**: Ajustar el umbral `total_jobs_found > 0` si se permiten corridas sin vacantes nuevas.<br>**En `P2-07/08/09`**: Exigir la existencia de `ingestion_state.json` siempre que `RUN_SERPAPI_INGEST=Y`. |
| **Fase 3** | `phase3_processing.py` | Lectura de JSON crudos, ejecución de `procesar_incremental()`, esquema de `vacantes_staged.parquet`, estabilidad/unicidad de `job_id` y reproducibilidad. | **En `procesar_vacantes.py`**: `extraer_seniority` y `extraer_requisito_ingles` solo evalúan el título; pueden ampliarse a la descripción completa.<br>**En `P3-12`**: Comparar también hashes/valores de `job_id` además del conteo de filas. |
| **Fase 4** | `phase4_database.py` | Auto-creación de `JobMarketDB` y conexión (`P4-01`), esquemas (`staging`, `warehouse`, `analytics`), ejecución por lotes `GO` y existencia de las 9 tablas base. | **En `P4-03`**: Hacer que cualquier excepción SQL falle el gate de forma explícita.<br>**En `P4-04`**: Incluir también las vistas de `analytics` en la verificación de objetos creados. |
| **Fase 5** | `phase5_etl.py` | Disponibilidad de Parquet staged, carga a `staging.stg_observacion_oferta`, ejecución de `01_load_dw_from_staging.sql` y conteos $> 0$ en hechos, dimensiones y puente M:N. | **En `P5-05`**: Ajustar la validación `rels > 0` si se prueban lotes sin skills detectadas.<br>**En `01_load_dw_from_staging.sql`**: Auditar registros asignados con valores por defecto (`-1` o fecha `19000101`). |
| **Fase 6** | `phase6_dq.py` | Unicidad de snapshots en `fact_observacion_oferta`, cero empresas huérfanas, unicidad en `rel_oferta_skill` y cobertura de categorías en `dim_skill`. | **En `P6-02`**: Ampliar la auditoría de huérfanos a `rol_id`, `ubicacion_id` y `fecha_captura_id`.<br>**En `P6-04`**: Definir un porcentaje mínimo aceptable de skills categorizadas (ej. $\ge 80\%$). |
| **Fase 7** | `phase7_analytics.py` | Despliegue de vistas analíticas, reconciliación de conteos vs `fact_observacion_oferta`, distribución de roles/mercados, snapshots y prevención de duplicados. | **En `P7-04`**: Cambiar `skill_demand_count >= 0` a `> 0` cuando se espere demanda poblada.<br>**En `P7-09`**: Incluir `proveedor_ingesta` en la llave de verificación de no duplicidad. |
| **Fase 8** | `phase8_matcher.py` | Carga de `candidate_profile.yaml`, evaluación de ofertas del DW y validación del rango `[0.0, 100.0]` en `effective_match_score`. | **En `candidate_matcher.py`**: Sincronizar `self.target_roles` con `config/roles.yaml` y auditar los pesos de geografía/idioma contra `metrics.yaml`. |
| **Fase 9** | `phase9_export.py` | Exportación a `data/3_csv/`, naming `esquema_objeto.csv`, encoding `utf-8-sig`, orden de columnas, conteo de filas vs SQL, muestreo de datos y modo solo lectura. | **En `P9-08`**: Ampliar el muestreo de consistencia más allá de la primera fila/columna (`iloc[0]`).<br>**En `export_tables_to_csv.py`**: Filtrar esquemas si solo se desea exportar `warehouse` y `analytics`. |

---

## Tecnologías Utilizadas

- **Lenguaje y Librerías**: Python 3.12 (`pandas`, `SQLAlchemy`, `pyodbc`, `PyYAML`, `python-dotenv`, `serpapi`).
- **Base de Datos**: SQL Server Local (`JobMarketDB`), T-SQL (esquemas, vistas, restricciones de unicidad e integridad referencial).
- **CI/CD y BI**: GitHub Actions, Parquet / CSV (`utf-8-sig`), Power BI.