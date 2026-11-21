# Market Intelligence Data Warehouse
### End-to-End Analytics Platform | Data Engineering, Data Modeling & Business Intelligence

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server_Local-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![T-SQL](https://img.shields.io/badge/T--SQL-5C2D91?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C94C?style=for-the-badge&logo=power-bi&logoColor=black)

---

## Project Overview

This project implements an end-to-end data platform (**Market Intelligence Data Platform**) designed to capture, process, model, and analyze the tech job market in LATAM (focusing on Peru and Argentina, including remote and on-site/hybrid work modalities).

It transforms job posting data obtained via **SerpAPI (Google Jobs)** or local raw files into an **analytical Data Warehouse (Star Schema)** deployed on **Local SQL Server (`JobMarketDB`)**, featuring automated data quality validations, a candidate profile *matching* engine, and CSV exports for analysis and consumption in **Power BI**.

---

## Architecture & Data Flow (Phases 0 to 9)

```text
  [ SerpAPI / Local Raw JSONs ]
               │
               ▼
1. Conditional Ingestion (RUN_SERPAPI_INGEST) ──► data/1_raw/*.json & data/ingestion_state.json
               │
               ▼
2. Processing & Normalization                 ──► data/2_staged/vacantes_staged.parquet
               │
               ▼
3. Local SQL Server Setup (JobMarketDB)       ──► Schemas: staging, warehouse, analytics
               │
               ▼
4. Staging Load & Star Schema ETL             ──► staging.stg_* ─► warehouse.fact_* & Dims
               │
               ▼
5. Data Quality Audit                         ──► Uniqueness, FK/orphans, M:N & skill taxonomy
               │
               ▼
6. Analytics Layer & Candidate Matcher        ──► analytics.vw_* & CandidateMatcher
               │
               ▼
7. CSV Export & Reconciliation                ──► data/3_csv/*.csv (Power BI / BI)
```

---

## Local Environment Configuration (`.env`)

Create or update the `.env` file in the project root with the following variables:

```env
# SerpAPI Credential
SERPAPI_API_KEY=YOUR_DATA
RUN_SERPAPI_INGEST=N
# Remember to set the flag to Y to consume the API; when set to N, it reuses local JSONs in data/1_raw

# Pipeline Settings
RAW_DATA_PATH=data/1_raw

# Local SQL Server
DB_SERVER=localhost
DB_NAME=JobMarketDB
DB_USER=YOUR_DATA
DB_PASSWORD=YOUR_DATA
DB_PORT=1433
DB_DRIVER=ODBC Driver 18 for SQL Server
```

---

## Pipeline Execution

The central orchestrator (`main.py`) allows you to run the entire pipeline with *gate control* (halting execution if any phase fails) or run a specific phase in isolation:

```bash
# Run all phases sequentially (Phases 0 to 9)
python main.py --all

# Run a specific phase in isolation (0 to 9)
python main.py --phase 0
python main.py --phase 2
python main.py --phase 5
```

---

## Key Business Rules

- **Deduplication & Identifier (`BR-001` / `BR-012`)**: Deterministic hash generation (`job_id`) and uniqueness constraint per snapshot (`proveedor_ingesta`, `source_job_id`, `fecha_captura_id`).
- **Role & Skill Taxonomy (`BR-004` / `BR-015` / `BR-017`)**: Standardized role classification (`primary`, `secondary`, `legacy_leverage`) according to `config/roles.yaml` and technical skill extraction via regex against `config/skills.yaml`, dynamically enriched in `warehouse.dim_skill`.
- **Geography & Market Priority (`BR-006` / `BR-007`)**: Location normalization (`ciudad`, `pais`, `market_tier`) while preserving the original `ubicacion_raw` value.
- **Candidate Matching Engine (`BR-020` / `BR-021`)**: Calculation engine for candidate-to-job fit (`skill_match_score`, `candidate_accessibility_index` combining geography and language, and `effective_match_score`) based on `config/candidate_profile.yaml` and `config/metrics.yaml`.
- **Data Quality & Reconciliation (`BR-025`)**: Automated validations at every phase (referential integrity, M:N uniqueness, taxonomy coverage) and row-by-row and schema reconciliation between Local SQL Server and `data/3_csv/`.

---

## Repository Structure

```text
market-intelligence-jobs/
├── .github/workflows/     # CI/CD: GitHub Actions pipeline workflow
├── config/                # candidate_profile.yaml, metrics.yaml, roles.yaml, skills.yaml, sources.yaml
├── data/
│   ├── 1_raw/             # Raw JSON responses from SerpAPI
│   ├── 2_staged/          # Normalized intermediate dataset (vacantes_staged.parquet)
│   ├── 3_csv/             # CSV exports of tables and views (schema_object.csv)
│   └── ingestion_state.json
├── data_specification/    # business_rules.md and taxonomy.md
├── project_specification/ # business_requirements.md and project_definition.md
├── sql/
│   ├── warehouse/         # 01_database_setup.sql, 02_star_schema.sql
│   ├── staging/           # 01_load_dw_from_staging.sql
│   └── analytics/         # 01_create_analytics_views.sql
├── src/
│   ├── analytics/         # init_analytics.py, candidate_matcher.py
│   ├── export/            # export_tables_to_csv.py
│   ├── ingestion/         # serpapi_ingest.py, procesar_vacantes.py, load_warehouse.py
│   ├── phases/            # phase0_env.py to phase9_export.py (Quality Gates)
│   └── utils/             # config_loader.py, db_connector.py, init_db.py
├── main.py                # CLI orchestrator by phase (--phase / --all)
└── requirements.txt       # Project dependencies
```

---

## Key Modules

- **Flag-Controlled Incremental Ingestion (`serpapi_ingest.py` + `phase2_ingestion.py`)**: Honors `RUN_SERPAPI_INGEST` (`Y`/`N`), tracks state in `data/ingestion_state.json`, and dynamically adjusts the time window (`today`, `3days`, `week`, `month`) based on the days elapsed since the last ingestion.
- **Parquet Processing & Staging (`procesar_vacantes.py`)**: Extracts skills, classifies roles, parses locations and relative dates, detects seniority and English language requirements, and performs incremental deduplication on `data/2_staged/vacantes_staged.parquet`.
- **Set-Based Star Schema Load (`load_warehouse.py` + `01_load_dw_from_staging.sql`)**: Loads `staging.stg_observacion_oferta` and `staging.stg_skill_taxonomy`, and populates dimensions (`dim_empresa`, `dim_ubicacion`, `dim_rol`, `dim_modalidad`, `dim_skill`, `dim_fecha`), the fact table (`fact_observacion_oferta`), and the bridge table (`rel_oferta_skill`).
- **Candidate Matcher (`candidate_matcher.py`)**: Evaluates each Data Warehouse job posting against the candidate profile, calculating effective match scores and skill gaps.

---

## Phase-by-Phase Testing & Audit Guide (`src/phases/`)

Each phase runs a suite of verification checks outputting `[PASS]` / `[FAIL]`. Below is a breakdown of what each phase audits and what points can be tuned or adjusted based on project requirements:

| Phase | Script | Current Checks (`P*-*`) | Tuning, Fix, or Audit Points |
| :--- | :--- | :--- | :--- |
| **Phase 0** | `phase0_env.py` | Python $\ge 3.10$, `requirements.txt`, critical packages, directories, YAMLs, `src/` syntax, imports, and `.env` (`DB_SERVER`, `DB_NAME`). | **In `P0-09`**: Expand validation to also require `DB_USER`, `DB_PASSWORD`, `DB_PORT`, and `DB_DRIVER`.<br>**In `P0-05`**: Adjust `required_dirs` if `images/` is not required. |
| **Phase 1** | `phase1_config.py` | Syntax and root keys of the 5 YAMLs, uniqueness of roles/skills, categories, metrics, and `[0.0, 1.0]` ranges in `candidate_profile.yaml`. | **In `P1-04/05` & `P1-06/07`**: Normalize with `.strip().lower()` to catch case-insensitive duplicates.<br>**In `P1-08`**: Explicitly validate expected metric keys (`skill_match_score`, `effective_match_score`, etc.). |
| **Phase 2** | `phase2_ingestion.py` | `RUN_SERPAPI_INGEST` (`Y`/`N`) flag, presence and valid JSON in `data/1_raw/*.json`, `jobs_results` schema, minimum fields, and `ingestion_state.json`. | **In `P2-03`**: Adjust the `total_jobs_found > 0` threshold if runs with zero new postings are allowed.<br>**In `P2-07/08/09`**: Enforce the existence of `ingestion_state.json` whenever `RUN_SERPAPI_INGEST=Y`. |
| **Phase 3** | `phase3_processing.py` | Raw JSON reading, `procesar_incremental()` execution, `vacantes_staged.parquet` schema, `job_id` stability/uniqueness, and reproducibility. | **In `procesar_vacantes.py`**: `extraer_seniority` and `extraer_requisito_ingles` only evaluate the job title; they can be expanded to the full description.<br>**In `P3-12`**: Compare `job_id` hashes/values in addition to row counts. |
| **Phase 4** | `phase4_database.py` | `JobMarketDB` auto-creation and connection (`P4-01`), schemas (`staging`, `warehouse`, `analytics`), `GO` batch execution, and existence of the 9 base tables. | **In `P4-03`**: Ensure any SQL exception explicitly fails the quality gate.<br>**In `P4-04`**: Also include `analytics` views when verifying created database objects. |
| **Phase 5** | `phase5_etl.py` | Staged Parquet availability, load into `staging.stg_observacion_oferta`, execution of `01_load_dw_from_staging.sql`, and counts $> 0$ in fact, dimensions, and M:N bridge. | **In `P5-05`**: Adjust the `rels > 0` check if testing batches without detected skills.<br>**In `01_load_dw_from_staging.sql`**: Audit records assigned default fallback values (`-1` or date `19000101`). |
| **Phase 6** | `phase6_dq.py` | Snapshot uniqueness in `fact_observacion_oferta`, zero orphaned companies, uniqueness in `rel_oferta_skill`, and category coverage in `dim_skill`. | **In `P6-02`**: Expand orphan checks to `rol_id`, `ubicacion_id`, and `fecha_captura_id`.<br>**In `P6-04`**: Define a minimum acceptable percentage of categorized skills (e.g., $\ge 80\%$). |
| **Phase 7** | `phase7_analytics.py` | Deployment of analytics views, count reconciliation vs. `fact_observacion_oferta`, role/market distribution, snapshots, and duplicate prevention. | **In `P7-04`**: Change `skill_demand_count >= 0` to `> 0` when populated demand is expected.<br>**In `P7-09`**: Include `proveedor_ingesta` in the uniqueness verification key. |
| **Phase 8** | `phase8_matcher.py` | Loading `candidate_profile.yaml`, evaluating DW job postings, and validating the `[0.0, 100.0]` range for `effective_match_score`. | **In `candidate_matcher.py`**: Sync `self.target_roles` with `config/roles.yaml` and audit geography/language weights against `metrics.yaml`. |
| **Phase 9** | `phase9_export.py` | Export to `data/3_csv/`, `schema_object.csv` naming, `utf-8-sig` encoding, column order, row count vs. SQL, data sampling, and read-only mode. | **In `P9-08`**: Expand consistency sampling beyond the first row/column (`iloc[0]`).<br>**In `export_tables_to_csv.py`**: Filter schemas if only `warehouse` and `analytics` exports are desired. |

---

## Technologies Used

- **Language & Libraries**: Python 3.12 (`pandas`, `SQLAlchemy`, `pyodbc`, `PyYAML`, `python-dotenv`, `serpapi`).
- **Database**: Local SQL Server (`JobMarketDB`), T-SQL (schemas, views, uniqueness constraints, and referential integrity).
- **CI/CD & BI**: GitHub Actions, Parquet / CSV (`utf-8-sig`), Power BI.