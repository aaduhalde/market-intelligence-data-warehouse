# API to Analytics ETL Showcase

Technical showcase of an end-to-end **ETL pipeline** that ingests data from an external API, applies transformations, and exposes analytics-ready datasets for BI and reporting.  
This project is designed as a **Data Engineering portfolio** piece, focused on architecture clarity, clean data processing, and reproducible pipelines.

---

## Project Objective

Simulate a real-world scenario where business data is:
1. Extracted from an external API  
2. Transformed and validated  
3. Loaded into an analytical storage layer  
4. Prepared for BI tools such as Power BI, Looker, or any SQL-based engine  

This repository demonstrates how to move from **raw API data → structured analytics data**.

---

## Architecture Overview
[ External API ]
↓
[ Ingestion Layer ]
↓
[ Data Processing & Validation ]
↓
[ Analytical Storage (SQL) ]
↓
[ BI / Dashboards ]


Key principles:
- Modular design  
- Clear separation of responsibilities  
- Reproducibility  
- Analytics-first modeling  

---

## 📁 Project Structure
```text

api-to-analytics-etl-showcase/
│
├── README.md
├── architecture/
│ └── pipeline_diagram.png
├── ingestion/
│ └── api_client.py
├── processing/
│ └── transform.py
├── storage/
│ └── load_to_db.py
└── requirements.txt
```

---

## ETL Flow Description

### 1. Extraction (Ingestion)
- Connects to a public REST API
- Fetches structured JSON data
- Normalizes it into a tabular format

Location:
ingestion/api_client.py

---

### 2. Transformation
- Cleans nulls and invalid values  
- Renames and standardizes fields  
- Applies business logic transformations  
- Prepares analytics-ready tables  

Location:
processing/transform.py


---

### 3. Load
- Persists transformed data into a SQL database (SQLite for demo purposes)
- Ensures data is ready for BI consumption  

Location:
storage/load_to_db.py

---

## Tech Stack

- **Python 3.10+**
- **Pandas / NumPy**
- **SQLite (demo analytical DB)**
- REST API consumption (Requests)
- Modular ETL design

This structure mirrors production systems that later scale to:
- PostgreSQL / Azure SQL / BigQuery
- Azure Data Factory
- AWS Lambda + S3
- Cloud orchestration

---

## BI & Analytics Usage

The final dataset is suitable for:
- Power BI  
- Looker  
- Tableau  
- SQL-based reporting  

Example KPIs that can be derived:
- Volume of records over time  
- Category distribution  
- Aggregations and trends  
- Data quality indicators  

---

## What This Project Demonstrates

This repository validates skills for:

| Role | Competency |
|------|-----------|
| Data Engineer | ETL pipelines, data modeling, ingestion, transformation |
| Integration Engineer | API integration, data normalization |
| Automation Engineer | Pipeline orchestration logic |
| BI Engineer | Analytics-ready data preparation |

---

## How to Run (Local)

1. Install dependencies:
```bash
pip install -r requirements.txt

