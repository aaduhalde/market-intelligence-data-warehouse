import requests
import pandas as pd
from datetime import date, datetime, timezone
import os

# -----------------------------
# Config
# -----------------------------
WORLD_BANK_URL = "https://api.worldbank.org/v2/country"

# Países que vamos a consultar
COUNTRIES = {
    "ARG": "Argentina",
    "BRA": "Brazil",
    "CHL": "Chile",
    "MEX": "Mexico",
    "PER": "Peru",
    "USA": "United States"
}

INDICATOR = "FP.CPI.TOTL.ZG"  # Inflation, consumer prices (annual %)

today = date.today().strftime("%Y_%m_%d")
OUTPUT_DIR = "../outputs/raw"
OUTPUT_PATH = f"{OUTPUT_DIR}/raw_inflation_{today}.csv"

# -----------------------------
# API Call
# -----------------------------
def fetch_inflation(country_code):
    url = (
        f"{WORLD_BANK_URL}/{country_code}/indicator/{INDICATOR}"
        "?format=json&per_page=1"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

# -----------------------------
# Normalize
# -----------------------------
def normalize_inflation(raw, country_code, country_name):
    rows = []
    extracted_at = datetime.now(timezone.utc)

    # La API devuelve una lista: [metadata, data]
    data = raw[1]

    if not data or data[0]["value"] is None:
        print(f"No inflation data for {country_name}")
        return rows

    record = data[0]

    rows.append({
        "country_code": country_code,
        "country_name": country_name,
        "inflation_rate": record["value"],
        "year": record["date"],
        "source": "world_bank",
        "extracted_at": extracted_at
    })

    return rows

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_rows = []

    for code, name in COUNTRIES.items():
        print(f"Fetching inflation data for {name} ({code})...")
        raw = fetch_inflation(code)
        rows = normalize_inflation(raw, code, name)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df.to_csv(OUTPUT_PATH, index=False)

    print(df)
    print(f"Total inflation records fetched: {len(df)}")
    print(f"Raw inflation data saved to: {OUTPUT_PATH}")
