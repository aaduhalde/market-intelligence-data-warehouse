# Market Intelligence Data Warehouse
### Enterprise Data Modeling, Data Quality & SQL Analytics Platform

![SQL Server](https://img.shields.io/badge/SQL_Server-CC2927?style=for-the-badge&logo=microsoft-sql-server&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![NodeJS](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)
![Azure](https://img.shields.io/badge/Azure_CLI-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)

---

## Executive Summary

This repository implements a **production-style analytics platform** designed to simulate real enterprise responsibilities performed by a **Senior Data Analyst / Analytics Engineer**.

The solution ingests public market and economic datasets, applies validation and transformation logic, and delivers a **performance-optimized dimensional data warehouse** ready for analytics and BI consumption.

The project demonstrates real-world practices used in enterprise environments:

- Enterprise data modeling (OLTP → Dimensional DW)
- Source-to-target mapping (STTM)
- SQL-based data validation & reconciliation
- Data quality monitoring framework
- Incremental ETL pipelines
- Query performance optimization
- Analytics-ready datasets for BI tools

The architecture mirrors delivery standards commonly used in consulting, telecom, fintech, and large-scale analytics teams.

---

## Business Context

Organizations require reliable datasets to analyze labor markets and macroeconomic trends.

### Job Market Intelligence
- Most demanded technical skills
- Remote job distribution by region
- Hiring trend evolution
- Salary benchmarking

### Economic Indicators
- Exchange rate history
- Currency volatility
- Inflation signals
- Crypto vs USD correlations

The platform ensures:

- Data accuracy and reconciliation
- Scalable processing (millions of records)
- Transparent transformation logic
- BI-ready analytical models

---

## Architecture Overview

```text
Public APIs
   ↓
Python ETL Layer
   ↓
SQL Server (Docker / Local)
   ├── Staging Layer (3NF)
   ├── Data Profiling
   ├── Data Quality Checks
   ├── Dimensional Warehouse (Star Schema)
   ├── Incremental Loads (Watermark Pattern)
   └── Analytical Views
   ↓
CSV Export / API Layer (Node.js)
   ↓
Power BI / Tableau / SQL Consumers
```
---

## Technology Stack

Fully executable in a Linux local environment.

| Layer            | Technology                         |
| ---------------- | ---------------------------------- |
| Database         | SQL Server (Docker)                |
| ETL              | Python                             |
| Data Processing  | Pandas / NumPy                     |
| API / Export     | Node.js                            |
| Containerization | Docker                             |
| Cloud Tooling    | Azure CLI                          |
| Query Language   | T-SQL                              |
| Modeling         | Dimensional Modeling (Star Schema) |

---
## Dimensional Model

### Fact Tables

- `fact_jobs`  
  **Grain:** one job posting per day per country

- `fact_exchange_rates`  
  **Grain:** currency pair per date

- `fact_crypto_prices`  
  **Grain:** asset price per timestamp

### Dimensions

- `dim_date`
- `dim_country`
- `dim_role`
- `dim_skill`

Features included:

- Surrogate keys
- Slowly Changing Dimension (SCD Type 2)
- Historical tracking
- Business-aligned grain definition

---
## Source-to-Target Mapping (STTM)

Enterprise-style mapping documentation defines:

- Source attributes
- Target warehouse columns
- Transformation rules
- Data type conversions
- Business logic
- Validation rules

Examples:

- JSON API → relational staging tables
- Staging → dimensional warehouse transformations

This simulates real analyst deliverables used by data engineering teams.

---
## Data Profiling

Profiling executed prior to modeling:

- Null distribution analysis
- Cardinality checks
- Outlier detection
- Statistical summaries
- Schema validation

Profiling outputs directly inform modeling and DQ rules.

---

## Data Quality Framework

Implemented validation controls:

- Completeness checks
- Duplicate detection
- Referential integrity validation
- Aggregation reconciliation
- Range validation
- Source vs target record comparison

All rules are version-controlled and reproducible.

---

## Incremental Loading Strategy

Watermark-based incremental processing:

- Tracks last processed timestamp
- Loads only new data
- Prevents duplication
- Maintains historical consistency

Standard enterprise ETL pattern.

---

## Performance Optimization

Techniques demonstrated:

- Clustered vs Nonclustered indexes
- Composite indexing strategies
- Execution plan analysis
- Query cost comparison
- Large dataset simulation (5M+ rows)

---

## Analytical Outputs

Validated warehouse enables analysis such as:

- Remote job demand growth by country
- Skill demand clustering
- Hiring trend evolution
- Currency volatility analysis

All insights rely on reconciled and validated datasets.

---

## Enterprise Cloud Equivalent (Azure Architecture)
Conceptual deployment using Azure services:
```text
Azure Data Factory
   ↓
Azure Blob Storage (Raw)
   ↓
Synapse Serverless (External Tables)
   ↓
Dedicated SQL Pool (Warehouse)
   ↓
Power BI
```
## Includes:

- Orchestration strategy
- Lakehouse layering
- External table design
- Deployment considerations

---

## Repository Structure
´´´text
Market-Intelligence-DW
│
├── architecture/
├── modeling/
│   ├── oltp_to_dw/
│   └── sttm/
├── data_quality/
│   ├── rules/
│   └── monitoring/
├── profiling/
├── sql/
├── etl/
├── api/
├── azure/
├── bi/
├── governance/
└── executive/
´´´
---

## Skills Demonstrated

| Skill Area               | Evidence                               |
| ------------------------ | -------------------------------------- |
| Data Modeling            | Star schema & SCD implementation       |
| Source-to-Target Mapping | Transformation documentation           |
| Advanced SQL             | Stored procedures & validation queries |
| Data Quality             | Reconciliation framework               |
| Data Profiling           | Statistical validation                 |
| Performance Tuning       | Index & execution analysis             |
| Incremental ETL          | Watermark loading                      |
| Azure Architecture       | Synapse & ADF design                   |
| Analytics Delivery       | BI-ready views                         |

---

## Local Setup (Linux)

### 1. Start SQL Server using Docker
```bash
docker compose up -d
```
### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```
### 3. Configure environment variables
Create .env file:
DB_SERVER=localhost
DB_USER=sa
DB_PASSWORD=YourPassword123
DB_NAME=MarketDW

### 4. Run ETL Pipeline
```bash
python etl/run_pipeline.py
```

### 5. Export datasets
```bash
node api/export.js
```
