import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
from datetime import date, datetime, timezone

from auth.currencyapi_auth import load_currencyapi_key

# -----------------------------
# Config
# -----------------------------
CURRENCYAPI_URL = "https://api.currencyapi.com/v3/latest"
BASE_CURRENCY = "USD"

TARGET_CURRENCIES = ["EUR", "ARS", "BRL", "CLP", "MXN", "PEN"]

API_KEY = load_currencyapi_key()

today = date.today().strftime("%Y_%m_%d")
OUTPUT_DIR = "../outputs/raw"
OUTPUT_PATH = f"{OUTPUT_DIR}/raw_forex_{today}.csv"

# -----------------------------
# API Call
# -----------------------------
def fetch_forex_data():
    params = {
        "apikey": API_KEY,
        "base_currency": BASE_CURRENCY,
        "currencies": ",".join(TARGET_CURRENCIES)
    }

    response = requests.get(CURRENCYAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# -----------------------------
# Normalize
# -----------------------------
def normalize_forex(raw):
    rows = []

    meta = raw.get("meta", {})
    data = raw.get("data", {})

    rate_date = meta.get("last_updated_at", "")[:10]

    for currency, payload in data.items():
        rows.append({
            "base_currency": BASE_CURRENCY,
            "target_currency": currency,
            "rate": payload.get("value"),
            "rate_date": rate_date,
            "source": "currencyapi",
            "extracted_at": datetime.now(timezone.utc)
        })

    return pd.DataFrame(rows)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Fetching FX data from currencyapi.com ...")
    raw = fetch_forex_data()
    df = normalize_forex(raw)

    df.to_csv(OUTPUT_PATH, index=False)

    print(df)
    print(f"Total FX rates fetched: {len(df)}")
    print(f"Raw forex data saved to: {OUTPUT_PATH}")
