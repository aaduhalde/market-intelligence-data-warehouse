import pandas as pd
import os
import glob

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_DIR = os.path.join(BASE_DIR, "..", "outputs", "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "..", "outputs", "reports", "economy")

os.makedirs(REPORTS_DIR, exist_ok=True)

# -----------------------------
# Utils
# -----------------------------
def get_latest_file(pattern):
    files = glob.glob(os.path.join(RAW_DIR, pattern))
    if not files:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")
    latest_file = max(files)
    print(f"Using file: {latest_file}")
    return latest_file


def append_if_not_exists(df_new, output_file, date_column="run_date"):
    if os.path.exists(output_file):
        df_old = pd.read_csv(output_file)

        if df_new[date_column].iloc[0] in df_old[date_column].astype(str).values:
            print(f"[SKIP] {os.path.basename(output_file)} already has data for {df_new[date_column].iloc[0]}")
            return

        df_final = pd.concat([df_old, df_new], ignore_index=True)
        print(f"[UPDATE] Appended daily data to {os.path.basename(output_file)}")
    else:
        df_final = df_new
        print(f"[CREATE] Created {os.path.basename(output_file)}")

    df_final.to_csv(output_file, index=False)


def extract_date_from_filename(filepath, prefix):
    filename = os.path.basename(filepath)
    # raw_xxx_YYYY_MM_DD.csv
    return filename.replace(prefix, "").replace(".csv", "")


# -----------------------------
# Load RAW datasets
# -----------------------------
def load_forex():
    path = get_latest_file("raw_forex_*.csv")
    df = pd.read_csv(path)
    run_date = extract_date_from_filename(path, "raw_forex_")
    return df, run_date


def load_crypto():
    path = get_latest_file("raw_crypto_*.csv")
    df = pd.read_csv(path)
    run_date = extract_date_from_filename(path, "raw_crypto_")
    return df, run_date


def load_inflation():
    path = get_latest_file("raw_inflation_*.csv")
    df = pd.read_csv(path)
    run_date = extract_date_from_filename(path, "raw_inflation_")
    return df, run_date


# -----------------------------
# Processing
# -----------------------------
def process_forex(df):
    """
    Normalización mínima Forex
    """
    df = df.copy()
    df["rate"] = df["rate"].astype(float)
    df["rate_date"] = pd.to_datetime(df["rate_date"])

    return df[[
        "base_currency",
        "target_currency",
        "rate",
        "rate_date",
        "source",
        "extracted_at"
    ]]


def process_crypto(df):
    """
    Normaliza BTC prices desde:
    base_currency,target_currency,rate,rate_date,source,extracted_at

    Output:
    crypto_symbol | currency | price | price_usd | rate_date | source | extracted_at
    """
    df = df.copy()

    required = {"base_currency", "target_currency", "rate", "rate_date"}
    if not required.issubset(df.columns):
        raise ValueError(f"Crypto RAW schema inválido: {df.columns.tolist()}")

    df["crypto_symbol"] = df["base_currency"]          # BTC
    df["currency"] = df["target_currency"]
    df["price"] = df["rate"].astype(float)
    df["rate_date"] = pd.to_datetime(df["rate_date"])

    # Buscar BTC/USD
    btc_usd = df.loc[df["currency"] == "USD", "price"]
    if btc_usd.empty:
        raise ValueError("No se encontró cotización BTC/USD en raw_crypto")

    btc_usd_price = float(btc_usd.iloc[0])

    # Normalizar todo a USD
    df["price_usd"] = df.apply(
        lambda r: r["price"] if r["currency"] == "USD"
        else r["price"] / btc_usd_price,
        axis=1
    )

    return df[[
        "crypto_symbol",
        "currency",
        "price",
        "price_usd",
        "rate_date",
        "source",
        "extracted_at"
    ]]


def process_inflation(df):
    """
    Inflación anual por país
    """
    df = df.copy()
    df["inflation_rate"] = df["inflation_rate"].astype(float)
    df["year"] = df["year"].astype(int)

    return df[[
        "country_code",
        "country_name",
        "inflation_rate",
        "year",
        "source",
        "extracted_at"
    ]]


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":

    print("\nLoading RAW datasets...")

    forex_df, forex_date = load_forex()
    crypto_df, crypto_date = load_crypto()
    inflation_df, inflation_date = load_inflation()

    # Se asume misma fecha de corrida
    run_date = forex_date

    print(f"Run date detected: {run_date}")

    print("\nProcessing datasets...")

    forex_processed = process_forex(forex_df)
    crypto_processed = process_crypto(crypto_df)
    inflation_processed = process_inflation(inflation_df)

    # Tracking temporal
    forex_processed["run_date"] = run_date
    crypto_processed["run_date"] = run_date
    inflation_processed["run_date"] = run_date

    print("\nSaving reports...")

    append_if_not_exists(
        forex_processed,
        os.path.join(REPORTS_DIR, "forex_daily.csv")
    )

    append_if_not_exists(
        crypto_processed,
        os.path.join(REPORTS_DIR, "crypto_daily.csv")
    )

    append_if_not_exists(
        inflation_processed,
        os.path.join(REPORTS_DIR, "inflation_daily.csv")
    )

    print("\nEconomy processing pipeline completed successfully.")
