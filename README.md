# Market Intelligence Data Warehouse
### End-to-End Analytics Platform | Data Engineering, Data Modeling & Business Intelligence

![Azure SQL](https://img.shields.io/badge/Azure_SQL-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/T--SQL-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C94C?style=for-the-badge&logo=power-bi&logoColor=black)

---

## Resumen del Proyecto

Este proyecto implementa una plataforma de datos end-to-end (**Market Intelligence Data Platform**) orientada a capturar, procesar, modelar y analizar el mercado laboral tecnológico en LATAM. 

Transforma datos sin estructurar de ofertas de empleo (vía APIs y scraping) en un **Data Warehouse analítico (Modelo Estrella)** desplegado en **Azure SQL Database**, garantizando calidad de datos, automatización de pipeline con CI/CD y consumo optimizado para dashboards en Power BI.

---

## Arquitectura y Flujo de Datos

```text
  [ SerpAPI / Job Boards ]
             │
             ▼
   1. Ingesta (Raw JSON)         ──► /data/1_raw
             │
             ▼
   2. Transformación & Staging   ──► /data/2_staged (Parquet)
             │
             ▼
   3. Carga en Staging DB        ──► Azure SQL (staging.stg_observacion_oferta)
             │
             ▼
   4. Modelo Estrella (DW)       ──► Azure SQL (warehouse.fact_observacion_oferta & Dims)
             │
             ▼
   5. Capa Analítica & Matching  ──► analytics.vw_* & Candidate Matcher Engine
             │
             ▼
   6. Exportación & BI           ──► /data/3_csv / Power BI Dashboards
   ```
---

## Reglas de Negocio Clave (Business Rules)

- BR-001 / BR-012 (Deduplicación e Identificador): Deduplicación determinista basada en identificadores fuente o clave compuesta (empresa + título + ubicación + fecha).

- BR-004 / BR-015 (Taxonomía de Roles y Skills): Clasificación estandarizada de roles (Primary, Secondary, Legacy) y extracción normalizada de habilidades técnicas mediante regex/JSON contra config/skills.yaml.

- BR-006 / BR-007 (Geografía y Market Tiers): Priorización de mercado (Priority 1: Perú/Argentina, Priority 2: LATAM, Priority 3: Remoto Global) preservando el valor original ubicacion_raw.

- BR-020 / BR-021 (Candidate Matching Engine): Motor de cálculo de ajuste candidato vs. oferta (Skill Match Score, Accessibility Index, Effective Score).

- BR-025 (Calidad de Datos): Validaciones automatizadas pre-carga (integridad referencial, claves no nulas, detección de duplicados).

## Estructura del Repositorio

```text
market-intelligence-data-warehouse/
├── .github/workflows/   # CI/CD: Automatización semanal en GitHub Actions
├── config/              # Taxonomías de skills, roles, métricas y perfil candidato
├── data/                # Almacenamiento local por capas (1_raw, 2_staged, 3_csv)
├── data_specification/  # Reglas de negocio (business_rules.md) y taxonomía
├── sql/                 # Scripts DDL/DML por capa (staging, warehouse, analytics)
├── src/
│   ├── analytics/       # Vistas analíticas y Candidate Matcher Engine
│   ├── export/          # Exportador automático de tablas/vistas a CSV
│   ├── ingestion/       # Extracción API, deduplicación y carga a DW
│   └── utils/           # Conectores DB, verificadores DDL, logger y config loader
├── main.py              # Orquestador principal del pipeline ETL
└── requirements.txt     # Dependencias del proyecto
```

## Módulos Destacados

- Pipeline Incramental (ETL): Procesa ofertas de trabajo asegurando el patrón Watermark para evitar re-procesamientos innecesarios.

- Quality Checks Automáticos: Suite de validaciones T-SQL/Python ejecutadas antes de habilitar la capa analítica.

- Calentamiento de Infraestructura (wakeup.py): Gestión automática del cold start en Azure SQL Serverless y Web Apps.

- CI/CD Automatizado: Pipeline en GitHub Actions configurado para ejecutarse con sintaxis Cron y enviar reportes automáticos vía email.

## Tecnologías Utilizadas

* Lenguajes & Librerías: Python 3.12 (Pandas, SQLAlchemy, PyYAML, Requests).
* Base de Datos & SQL: Azure SQL Database, T-SQL (Stored Procedures, Vistas, Indexación).
* Orquestación & CI/CD: GitHub Actions, Linux Ubuntu Runners.
* Consumo de Datos: Power BI, Datasets exportados en CSV/Parquet.