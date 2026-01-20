import requests
import pandas as pd
from datetime import date, datetime, timezone
import os

# -----------------------------
# Config
# -----------------------------
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"

CRYPTO = "bitcoin"        # CoinGecko usa ids, no símbolos
BASE_CURRENCY = "BTC"     # Conceptual para tu modelo

TARGET_CURRENCIES = ["usd", "ars", "eur", "brl", "clp", "mxn", "pen"]

today = date.today().strftime("%Y_%m_%d")
OUTPUT_DIR = "../outputs/raw"
OUTPUT_PATH = f"{OUTPUT_DIR}/raw_crypto_{today}.csv"

# -----------------------------
# API Call
# -----------------------------
def fetch_crypto_prices():
    params = {
        "ids": CRYPTO,
        "vs_currencies": ",".join(TARGET_CURRENCIES)
    }
    response = requests.get(COINGECKO_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# -----------------------------
# Normalize
# -----------------------------
def normalize_crypto(raw):
    rows = []
    prices = raw.get(CRYPTO, {})
    extracted_at = datetime.now(timezone.utc)
    rate_date = date.today().isoformat()

    for currency, price in prices.items():
        rows.append({
            "base_currency": BASE_CURRENCY,
            "target_currency": currency.upper(),
            "rate": price,
            "rate_date": rate_date,
            "source": "coingecko",
            "extracted_at": extracted_at
        })

    return pd.DataFrame(rows)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    raw = fetch_crypto_prices()
    df = normalize_crypto(raw)

    df.to_csv(OUTPUT_PATH, index=False)

    print(df)
    print(f"Total crypto rates fetched: {len(df)}")
    print(f"Raw crypto data saved to: {OUTPUT_PATH}")
