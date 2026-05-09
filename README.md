# Market Intelligence Data Warehouse
### End-to-End Analytics Platform | Data Modeling, SQL, Data Quality & BI

![SQL Server](https://img.shields.io/badge/SQL_Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=aws-lambda&logoColor=white)
![Azure SQL](https://img.shields.io/badge/Azure_SQL-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

---

## Project Overview

This project simulates a **real-world Data Analyst / Analytics Engineer environment**, where raw data is transformed into **reliable, validated, and business-ready insights**.

It demonstrates how to:

- Turn raw data into **decision-ready dashboards**
- Ensure **data quality and trust**
- Build **scalable analytics pipelines**
- Deliver **real business insights**

This is the **core repository** of a broader ecosystem:

- `market-intelligence-data-warehouse` → Data foundation (this repo)
- `business-intelligence-ops` → Dashboards & BI layer
- `omnichannel-ai-agent-ecosystem` → Automation & AI layer

---

## Business Problem

Companies struggle with:

- Unreliable or inconsistent data
- Manual reporting processes
- Lack of visibility into KPIs
- Slow decision-making

This project solves that by building a **complete analytics pipeline**.

---

## Solution

An end-to-end data platform that:

1. Ingests market and economic data via APIs and web scraping
2. Validates and cleans the data  
3. Transforms it into a dimensional model  
4. Delivers analytics-ready datasets  
5. Enables BI dashboards and insights  

---

## Key Features

**Data Modeling**
- Star Schema (facts & dimensions)
- SCD Type 2 (historical tracking)

**Data Quality**
- Duplicate detection
- Null validation
- Reconciliation checks
- Referential integrity

**ETL & Processing**
- Incremental loads (watermark pattern)
- Python + SQL transformations
- Reproducible pipelines

**Performance**
- Index optimization
- Query tuning
- Execution plan analysis

---

## Business Insights & Operational KPIs

### Market Intelligence
- Remote job demand trends by country and industry
- Most in-demand technical skills (SQL, Python, BI, Automation)
- Salary benchmarking across regions and roles
- Emerging market and hiring trend analysis
- Skill gap detection between candidate profiles and job requirements

---

## Cloud Architecture (Conceptual)
```text
Data Sources
    ↓
GitHub Actions (Orchestration)
    ↓
Data Lake - Raw Layer (Google Drive)
    ↓
Python Transformation Layer
    ↓
AWS Lambda & Azure SQL
    ↓
Power BI / Looker
```

---

## Repository Structure
```text
market-intelligence-data-warehouse/
├── .github/workflows/
│   ├── scraper_pipeline.yml       # Orquestador (GitHub Actions)
│   └── data_validation.yml        # Tests de calidad de datos (Great Expectations/Pytest)
├── src/
│   ├── scrapers/                  # Lógica de extracción
│   │   ├── google_jobs_serp.py    # Integración con SerpApi
│   │   └── web_scraper_pw.py      # Playwright para sitios específicos
│   ├── drivers/                   # Conectores de almacenamiento
│   │   └── gdrive_client.py       # Lógica para subir archivos a Google Drive
│   └── utils/
│       └── logger.py
├── tests/                         # Pruebas unitarias para scrapers
├── requirements.txt
└── README.md                      # Documentación del Pipeline de Ingestión
```

---

## Tech Stack

- SQL Server
- Python (Pandas, NumPy)
- T-SQL
- Docker
- AWS & Azure (conceptual architecture)
- Power BI (consumption layer)
