import pandas as pd
import re
from collections import Counter
import os
import glob

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DIR = os.path.join(BASE_DIR, "..", "outputs", "raw")
REPORTS_PATH = os.path.join(BASE_DIR, "..", "outputs", "reports", "jobs")

# -----------------------------
# Load latest raw file
# -----------------------------
def get_latest_raw_file():
    files = glob.glob(os.path.join(RAW_DIR, "raw_jobs_*.csv"))
    if not files:
        raise FileNotFoundError(f"No raw files found in {RAW_DIR}")

    # raw_jobs_YYYY_MM_DD.csv ordena bien por fecha
    latest_file = max(files)
    print(f"Using raw file: {latest_file}")
    return latest_file


def extract_date_from_filename(filepath):
    filename = os.path.basename(filepath)
    # Devuelve YYYY_MM_DD
    return filename.replace("raw_jobs_", "").replace(".csv", "")


def load_raw_data():
    raw_file = get_latest_raw_file()
    df = pd.read_csv(raw_file)
    run_date = extract_date_from_filename(raw_file)
    return df, run_date


# -----------------------------
# Utils: append daily snapshot
# Cada corrida agrega UNA fila por fecha
# -----------------------------
def append_if_not_exists(df_new, output_file, date_column="run_date"):
    if os.path.exists(output_file):
        df_old = pd.read_csv(output_file)

        # Evita duplicar el mismo día
        if df_new[date_column].iloc[0] in df_old[date_column].astype(str).values:
            print(f"[SKIP] {os.path.basename(output_file)} already has data for {df_new[date_column].iloc[0]}")
            return

        df_final = pd.concat([df_old, df_new], ignore_index=True)
        print(f"[UPDATE] Appended daily data to {os.path.basename(output_file)}")
    else:
        df_final = df_new
        print(f"[CREATE] Created {os.path.basename(output_file)}")

    df_final.to_csv(output_file, index=False)


# -----------------------------
# Skills extraction (DAILY TOP 30)
# -----------------------------
STOPWORDS = {
    "remote", "job", "jobs", "senior", "junior", "sr", "jr",
    "developer", "engineer", "manager", "analyst",
    "full", "time", "part", "stack", "lead", "software"
}


def extract_skills(df):
    text = (df["title"].fillna("") + " " + df["category"].fillna("")).str.lower()

    tokens = []
    for row in text:
        words = re.findall(r"[a-zA-Z]{3,}", row)
        words = [w for w in words if w not in STOPWORDS]
        tokens.extend(words)

    counter = Counter(tokens)
    return pd.DataFrame(counter.most_common(30), columns=["skill", "count"])


# -----------------------------
# Country distribution (DAILY SNAPSHOT)
# -----------------------------
def remote_jobs_by_country(df):
    country_counts = (
        df["candidate_required_location"]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )
    country_counts.columns = ["country", "total_jobs"]
    return country_counts


# -----------------------------
# Daily growth (no weekly)
# -----------------------------
def job_growth_daily(df):
    df = df.copy()
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce", utc=True)
    df["publication_date"] = df["publication_date"].dt.tz_convert(None)
    df["day"] = df["publication_date"].dt.date

    daily = (
        df.groupby("day")
        .size()
        .reset_index(name="total_jobs")
        .sort_values("day")
    )
    return daily


# -----------------------------
# Salary analysis (DAILY AVERAGE)
# -----------------------------
def average_salaries(df):
    salaries = []

    for s in df["salary"].dropna():
        numbers = re.findall(r"\d+", str(s).replace(",", ""))
        if numbers:
            values = list(map(int, numbers))
            salaries.append(sum(values) / len(values))

    if not salaries:
        return pd.DataFrame(columns=["metric", "value"])

    return pd.DataFrame({
        "metric": ["average_salary"],
        "value": [sum(salaries) / len(salaries)]
    })


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    df, run_date = load_raw_data()

    # Solo reports (raw es tu único histórico real)
    os.makedirs(REPORTS_PATH, exist_ok=True)

    # Generación diaria de métricas
    skills = extract_skills(df)
    countries = remote_jobs_by_country(df)
    daily_growth = job_growth_daily(df)
    salaries = average_salaries(df)

    # Todas las métricas quedan marcadas por fecha de corrida
    skills["run_date"] = run_date
    countries["run_date"] = run_date
    daily_growth["run_date"] = run_date
    salaries["run_date"] = run_date

    # Guardado acumulativo DAILY
    append_if_not_exists(skills, os.path.join(REPORTS_PATH, "skills_demanded_daily.csv"))
    append_if_not_exists(countries, os.path.join(REPORTS_PATH, "remote_jobs_by_country_daily.csv"))
    append_if_not_exists(daily_growth, os.path.join(REPORTS_PATH, "job_growth_daily.csv"))
    append_if_not_exists(salaries, os.path.join(REPORTS_PATH, "average_salaries_daily.csv"))

    print(f"\nDaily pipeline completed successfully for run_date = {run_date}")
