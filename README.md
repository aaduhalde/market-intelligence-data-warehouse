# API to Analytics – Weekly Market & Economic Reports Pipeline

End-to-end analytics pipeline that consumes free public APIs and generates
weekly CSV datasets ready for BI and reporting.

This project simulates how a data team would automate the generation of
market intelligence and economic indicators for decision making.

It is designed as a **Data Analyst + Analytics Engineer portfolio project**.

---

## Business Use Case

Every week, the company needs updated datasets for:

### Job Market Analytics
- Most demanded skills
- Countries with the highest number of remote job offers
- Weekly evolution of job vacancies
- Average salaries by role / country

### Economic Indicators
- Historical exchange rates
- Inflation by country
- Weekly volatility of currencies
- Correlation between USD and Bitcoin

All data is collected from **free public APIs**, processed, validated and
exported as structured CSV files for BI tools.

---

## Architecture Overview

# API to Analytics – Weekly Market & Economic Reports Pipeline

End-to-end analytics pipeline that consumes free public APIs and generates
weekly CSV datasets ready for BI and reporting.

This project simulates how a data team would automate the generation of
market intelligence and economic indicators for decision making.

It is designed as a **Data Analyst + Analytics Engineer portfolio project**.

---

## Business Use Case

Every week, the company needs updated datasets for:

### Job Market Analytics
- Most demanded skills
- Countries with the highest number of remote job offers
- Weekly evolution of job vacancies
- Average salaries by role / country

### Economic Indicators
- Historical exchange rates
- Inflation by country
- Weekly volatility of currencies
- Correlation between USD and Bitcoin

All data is collected from **free public APIs**, processed, validated and
exported as structured CSV files for BI tools.

---

## Architecture Overview

```text
[ Free Public APIs ]
       ↓
[ Ingestion Layer ]
       ↓
[ Processing & Analytics Logic ]
       ↓
[ Weekly CSV Outputs ]
       ↓
[ Power BI / Looker / SQL ]
```

Key principles:
- Analytics-first design 
- Reproducibility 
- Modular pipelines  
- Real-world reporting use case  

---

## 📁 Project Structure

```text
api-to-analytics-etl-showcase/
│
├── README.md
├── config/
│   └── settings.yaml            # APIs, endpoints, paths, fechas, etc.
│
├── ingestion/
│   ├── jobs_api.py               # Skills, remote jobs, salaries
│   ├── forex_api.py              # Exchange rates
│   ├── inflation_api.py          # Inflation by country
│   └── crypto_api.py             # BTC prices
│
├── processing/
│   ├── jobs_processing.py
│   ├── economy_processing.py
│   └── correlations.py           # USD vs BTC correlation, volatility
│
├── outputs/
│   ├── weekly_reports/
│   │   ├── jobs/
│   │   │   ├── skills_demanded_YYYY_MM_DD.csv
│   │   │   ├── remote_jobs_by_country_YYYY_MM_DD.csv
│   │   │   ├── weekly_job_growth_YYYY_MM_DD.csv
│   │   │   └── average_salaries_YYYY_MM_DD.csv
│   │   │
│   │   └── economy/
│   │       ├── exchange_rate_history_YYYY_MM_DD.csv
│   │       ├── inflation_by_country_YYYY_MM_DD.csv
│   │       ├── weekly_volatility_YYYY_MM_DD.csv
│   │       └── usd_btc_correlation_YYYY_MM_DD.csv
│
├── orchestrator/
│   └── run_weekly_pipeline.py    # Ejecuta todo
│
├── notebooks/
│   └── analysis_examples.ipynb   # Exploración 
│
├── requirements.txt
└── .gitignore

```
---

## Generated Reports (CSV)
### Job Market
| File                                  | Description                      |
| ------------------------------------- | -------------------------------- |
| skills_demanded_YYYY_MM_DD.csv        | Top skills by frequency          |
| remote_jobs_by_country_YYYY_MM_DD.csv | Remote job offers per country    |
| weekly_job_growth_YYYY_MM_DD.csv      | Week-over-week vacancy evolution |
| average_salaries_YYYY_MM_DD.csv       | Salary averages by role/country  |

---

### Economy
| File                                 | Description            |
| ------------------------------------ | ---------------------- |
| exchange_rate_history_YYYY_MM_DD.csv | FX historical rates    |
| inflation_by_country_YYYY_MM_DD.csv  | Inflation metrics      |
| weekly_volatility_YYYY_MM_DD.csv     | FX volatility          |
| usd_btc_correlation_YYYY_MM_DD.csv   | USD vs BTC correlation |

---

## Tech Stack

- Python 3.10+
- Pandas / NumPy
- Requests
- Public APIs (no paid services)
- CSV as analytics delivery format

---

## What This Project Demonstrates

This repository validates skills for:

| Skill                 | Evidence                                |
| --------------------- | --------------------------------------- |
| Data Engineering      | API ingestion, pipelines, orchestration |
| Analytics Engineering | Metric design, datasets, aggregations   |
| Data Analysis         | Trends, correlations, market indicators |
| BI Readiness          | Clean, documented CSV outputs           |
| Automation            | Fully repeatable weekly execution       |

---

## How to Run

* pip install -r requirements.txt
* python orchestrator/run_weekly_pipeline.py

