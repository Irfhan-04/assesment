"""
Centralised configuration for the CoinGecko → BigQuery pipeline.

All values that vary between environments live here and are injected via
environment variables. pipeline.py imports load_config() and uses the
returned dict — it never calls os.getenv() directly.

See .env.example for the full list of supported environment variables.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def load_config() -> dict:
    """
    Load and validate all pipeline configuration from environment variables.

    Raises ValueError on the first missing required variable, listing all
    missing variables at once rather than failing one at a time.

    Returns:
        dict: Fully populated configuration dictionary. All keys are strings;
              numeric values are cast to int before return.
    """
    required = [
        "gcp_project_id",
        "bq_dataset_id",
        "bq_table_id",
    ]

    config: dict = {}
    missing: list[str] = []

    for key in required:
        value = os.getenv(key)
        if not value:
            missing.append(key)
        else:
            config[key] = value

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill in your values."
        )

    # CoinGecko API — base URL and endpoint are fixed; params are configurable
    config["coingecko_base_url"] = "https://api.coingecko.com/api/v3"
    config["coingecko_markets_endpoint"] = "/coins/markets"
    config["vs_currency"] = os.getenv("COINGECKO_VS_CURRENCY", "usd")
    config["per_page"] = int(os.getenv("COINGECKO_PER_PAGE", "100"))
    config["page"] = int(os.getenv("COINGECKO_PAGE", "1"))
    config["request_timeout_seconds"] = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    # BigQuery write disposition — WRITE_APPEND preserves time-series history;
    # WRITE_TRUNCATE replaces the table on each run.
    config["bq_write_mode"] = os.getenv("BQ_WRITE_MODE", "WRITE_APPEND")

    return config