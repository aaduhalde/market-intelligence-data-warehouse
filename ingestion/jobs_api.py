import requests
import pandas as pd
from datetime import datetime, timezone, date
import os

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"

# Fecha de hoy para versionar el raw
today = date.today().strftime("%Y_%m_%d")
OUTPUT_DIR = "../outputs/raw"
OUTPUT_PATH = f"{OUTPUT_DIR}/raw_jobs_{today}.csv"

def fetch_jobs():
    response = requests.get(REMOTIVE_URL)
    response.raise_for_status()
    return response.json()

def normalize_jobs(raw_data):
    jobs = []

    for job in raw_data.get("jobs", []):
        jobs.append({
            "job_id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company_name"),
            "category": job.get("category"),
            "job_type": job.get("job_type"),
            "candidate_required_location": job.get("candidate_required_location"),
            "salary": job.get("salary"),
            "publication_date": job.get("publication_date"),
            "url": job.get("url"),
            "extracted_at": datetime.now(timezone.utc)
        })

    return pd.DataFrame(jobs)

def fetch_and_normalize():
    raw = fetch_jobs()
    df = normalize_jobs(raw)
    return df

if __name__ == "__main__":
    # Crear carpeta outputs/raw si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = fetch_and_normalize()

    # Guardar raw layer versionado por fecha
    df.to_csv(OUTPUT_PATH, index=False)

    print(df.head())
    print(f"Total jobs fetched: {len(df)}")
    print(f"Raw data saved to: {OUTPUT_PATH}")
