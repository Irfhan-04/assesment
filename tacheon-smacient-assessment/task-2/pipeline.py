"""
CoinGecko → BigQuery Pipeline
------------------------------
Fetches top coins by market cap from CoinGecko, transforms the data,
adds derived analytical fields, and loads the result to BigQuery.

Usage:
    python pipeline.py

Configuration:
    All parameters are read from environment variables.
    Copy .env.example to .env and fill in your values before running.
"""

import logging
import sys
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, SchemaField, WriteDisposition

from config import load_config

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BigQuery schema — explicit typing prevents autodetect failures
# ---------------------------------------------------------------------------

BQ_SCHEMA = [
    SchemaField("coin_id", "STRING", mode="REQUIRED"),
    SchemaField("coin_name", "STRING", mode="REQUIRED"),
    SchemaField("symbol", "STRING", mode="REQUIRED"),
    SchemaField("market_cap_rank", "INTEGER", mode="NULLABLE"),
    SchemaField("current_price_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("market_cap_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("total_volume_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("high_24h_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("low_24h_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("price_change_pct_24h", "FLOAT64", mode="NULLABLE"),
    SchemaField("price_change_pct_7d", "FLOAT64", mode="NULLABLE"),
    SchemaField("circulating_supply", "FLOAT64", mode="NULLABLE"),
    SchemaField("total_supply", "FLOAT64", mode="NULLABLE"),
    SchemaField("ath_usd", "FLOAT64", mode="NULLABLE"),
    SchemaField("ath_change_pct", "FLOAT64", mode="NULLABLE"),
    SchemaField("volume_to_market_cap_ratio", "FLOAT64", mode="NULLABLE"),
    SchemaField("price_range_pct_24h", "FLOAT64", mode="NULLABLE"),
    SchemaField("fetched_at", "TIMESTAMP", mode="REQUIRED"),
]


# ---------------------------------------------------------------------------
# Step 1: Fetch
# ---------------------------------------------------------------------------

def fetch_coin_markets(config: dict) -> list[dict[str, Any]]:
    """
    Fetch coin market data from CoinGecko /coins/markets endpoint.

    Returns:
        List of raw coin dictionaries from the API response.

    Raises:
        requests.exceptions.HTTPError: On non-2xx API responses.
        requests.exceptions.Timeout: If the request exceeds the configured timeout.
        ValueError: If the API returns an empty or non-list response.
    """
    url = config["coingecko_base_url"] + config["coingecko_markets_endpoint"]
    params = {
        "vs_currency": config["vs_currency"],
        "order": "market_cap_desc",
        "per_page": config["per_page"],
        "page": config["page"],
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    }

    logger.info(
        "Fetching coin markets: vs_currency=%s, per_page=%s, page=%s",
        config["vs_currency"],
        config["per_page"],
        config["page"],
    )

    try:
        response = requests.get(
            url,
            params=params,
            timeout=config["request_timeout_seconds"],
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error(
            "CoinGecko API timed out after %s seconds",
            config["request_timeout_seconds"],
        )
        raise
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "CoinGecko API returned HTTP %s: %s",
            exc.response.status_code,
            exc.response.text[:500],
        )
        raise

    data = response.json()

    if not isinstance(data, list):
        raise ValueError(
            f"Expected list from CoinGecko API, got {type(data).__name__}. "
            f"Response: {str(data)[:300]}"
        )

    if not data:
        raise ValueError("CoinGecko API returned an empty list. No data to process.")

    logger.info("Fetched %d coins from CoinGecko", len(data))
    return data


# ---------------------------------------------------------------------------
# Step 2: Transform
# ---------------------------------------------------------------------------

def transform(raw_data: list[dict[str, Any]], fetched_at: datetime) -> pd.DataFrame:
    """
    Flatten the raw CoinGecko response, clean types, and add derived analytical fields.

    Derived fields:
        volume_to_market_cap_ratio: total_volume / market_cap.
            Liquidity signal — high ratio = actively traded relative to market size.

        price_range_pct_24h: (high_24h - low_24h) / low_24h * 100.
            Intraday volatility — how much the price swung as a % of the daily low.

    Returns:
        Cleaned, typed DataFrame with columns ordered to match BQ_SCHEMA.
    """
    logger.info("Transforming %d rows", len(raw_data))

    field_map = {
        "id": "coin_id",
        "name": "coin_name",
        "symbol": "symbol",
        "market_cap_rank": "market_cap_rank",
        "current_price": "current_price_usd",
        "market_cap": "market_cap_usd",
        "total_volume": "total_volume_usd",
        "high_24h": "high_24h_usd",
        "low_24h": "low_24h_usd",
        "price_change_percentage_24h": "price_change_pct_24h",
        "price_change_percentage_7d_in_currency": "price_change_pct_7d",
        "circulating_supply": "circulating_supply",
        "total_supply": "total_supply",
        "ath": "ath_usd",
        "ath_change_percentage": "ath_change_pct",
    }

    rows = []
    for coin in raw_data:
        row = {target: coin.get(source) for source, target in field_map.items()}
        rows.append(row)

    df = pd.DataFrame(rows)

    # Coerce floats — prevents schema mismatch on API nulls
    float_columns = [
        "current_price_usd", "market_cap_usd", "total_volume_usd",
        "high_24h_usd", "low_24h_usd", "price_change_pct_24h",
        "price_change_pct_7d", "circulating_supply", "total_supply",
        "ath_usd", "ath_change_pct",
    ]
    for col in float_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["market_cap_rank"] = pd.to_numeric(
        df["market_cap_rank"], errors="coerce"
    ).astype("Int64")

    # Derived field 1: Liquidity signal
    # Row-level apply ensures None (not NaN) when inputs are null or denominator is zero
    df["volume_to_market_cap_ratio"] = df.apply(
        lambda row: (
            round(row["total_volume_usd"] / row["market_cap_usd"], 6)
            if pd.notna(row["total_volume_usd"])
            and pd.notna(row["market_cap_usd"])
            and row["market_cap_usd"] > 0
            else None
        ),
        axis=1,
    )

    # Derived field 2: Intraday volatility signal
    df["price_range_pct_24h"] = df.apply(
        lambda row: (
            round(
                (row["high_24h_usd"] - row["low_24h_usd"])
                / row["low_24h_usd"]
                * 100,
                4,
            )
            if pd.notna(row["high_24h_usd"])
            and pd.notna(row["low_24h_usd"])
            and row["low_24h_usd"] > 0
            else None
        ),
        axis=1,
    )

    # Pipeline lineage timestamp
    df["fetched_at"] = fetched_at

    # Enforce column order to match BQ_SCHEMA — must be the last transform step
    column_order = [field.name for field in BQ_SCHEMA]
    df = df[column_order]

    logger.info(
        "Transformation complete: %d rows, %d columns", len(df), len(df.columns)
    )
    return df


# ---------------------------------------------------------------------------
# Step 3: Load to BigQuery
# ---------------------------------------------------------------------------

def load_to_bigquery(df: pd.DataFrame, config: dict) -> None:
    """
    Load the transformed DataFrame to BigQuery using batch load.

    Uses load_table_from_dataframe (not streaming inserts) because BigQuery Sandbox
    does not guarantee streaming support without a billing account.

    Write mode is controlled by BQ_WRITE_MODE env var (default: WRITE_APPEND).
    WRITE_APPEND makes every run a time-stamped snapshot; the table becomes a time series.

    Raises:
        Exception: Any BigQuery client error — logged before re-raising.
    """
    project_id = config["gcp_project_id"]
    dataset_id = config["bq_dataset_id"]
    table_id = config["bq_table_id"]
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    write_mode = (
        WriteDisposition.WRITE_APPEND
        if config["bq_write_mode"] == "WRITE_APPEND"
        else WriteDisposition.WRITE_TRUNCATE
    )

    job_config = LoadJobConfig(
        schema=BQ_SCHEMA,
        write_disposition=write_mode,
    )

    logger.info(
        "Loading %d rows to BigQuery: %s (mode: %s)",
        len(df),
        table_ref,
        config["bq_write_mode"],
    )

    client = bigquery.Client(project=project_id)

    try:
        load_job = client.load_table_from_dataframe(
            df, table_ref, job_config=job_config
        )
        load_job.result()  # Blocks until job completes
    except Exception as exc:
        logger.error("BigQuery load failed: %s", exc)
        raise

    destination_table = client.get_table(table_ref)
    logger.info(
        "Successfully loaded %d rows. Table now has %d rows total.",
        len(df),
        destination_table.num_rows,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Orchestrate the pipeline: config → fetch → transform → load.
    Exits with code 1 on any stage failure. Exits with code 0 on success.
    """
    logger.info("Starting CoinGecko → BigQuery pipeline")

    try:
        config = load_config()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc)

    try:
        raw_data = fetch_coin_markets(config)
    except (requests.exceptions.RequestException, ValueError) as exc:
        logger.error("Fetch failed: %s", exc)
        sys.exit(1)

    try:
        df = transform(raw_data, fetched_at)
    except Exception as exc:
        logger.error("Transform failed: %s", exc)
        sys.exit(1)

    try:
        load_to_bigquery(df, config)
    except Exception as exc:
        logger.error("BigQuery load failed: %s", exc)
        sys.exit(1)

    logger.info("Pipeline complete")


if __name__ == "__main__":
    main()