# Task 2: CoinGecko → BigQuery Pipeline

A production-aware Python pipeline that fetches cryptocurrency market data from the
CoinGecko public API, transforms it with derived analytical fields, and loads it to
Google BigQuery using batch load with explicit schema definition.

---

## API Choice and Rationale

**API used:** CoinGecko `/coins/markets`
`https://api.coingecko.com/api/v3/coins/markets`

**Why CoinGecko:**

Three candidates were considered. Open-Meteo (weather) returns a flat, pre-cleaned
array with no meaningful transformation work — the data arrives essentially load-ready,
which demonstrates nothing about the engineering pattern. NewsAPI requires an API key
(friction), returns semi-structured article text with limited numerical depth, and
produces weak SQL aggregation queries. CoinGecko requires no API key on the free tier,
returns richly nested JSON with ~30 fields per coin, and provides clear, non-trivial
opportunities for two distinct derived fields that add genuine analytical value. The
endpoint is stable, well-documented, and free to call at the rate this pipeline requires.

**Endpoint parameters:**

| Parameter | Value | Source |
|---|---|---|
| `vs_currency` | `usd` (default) | `COINGECKO_VS_CURRENCY` env var |
| `order` | `market_cap_desc` | Fixed — top coins by market cap first |
| `per_page` | `100` (default) | `COINGECKO_PER_PAGE` env var |
| `page` | `1` (default) | `COINGECKO_PAGE` env var |
| `sparkline` | `false` | Fixed — reduces response payload |
| `price_change_percentage` | `24h,7d` | Fixed — enables both change fields |

---

## Setup and Run Instructions

**Prerequisites:**

- Python 3.11+
- Google Cloud SDK (`gcloud`) installed and authenticated
- A GCP project with BigQuery API enabled (BigQuery Sandbox works; no billing required)
- A BigQuery dataset named `crypto_market_data` created in your project

**Step 1 — Create the BigQuery dataset (one-time setup):**

```bash
bq mk --dataset --location=US your-project-id:crypto_market_data
```

**Step 2 — Authenticate with GCP:**

```bash
gcloud auth application-default login
```

This uses your Google account credentials locally. No service account JSON file is
needed for development. For CI/production, use a service account (see Production
Thinking below).

**Step 3 — Clone the repo and set up the environment:**

```bash
git clone https://github.com/your-username/tacheon-smacient-assessment.git
cd tacheon-smacient-assessment/task-2

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 4 — Configure environment variables:**

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

GCP_PROJECT_ID=your-project-id
BQ_DATASET_ID=crypto_market_data
BQ_TABLE_ID=coin_markets

All other variables have sensible defaults. See `.env.example` for the full reference.

**Step 5 — Run the pipeline:**

```bash
python pipeline.py
```

**Expected output:**

2026-05-30 06:12:01 INFO Starting CoinGecko → BigQuery pipeline
2026-05-30 06:12:01 INFO Fetching coin markets: vs_currency=usd, per_page=100, page=1
2026-05-30 06:12:02 INFO Fetched 100 coins from CoinGecko
2026-05-30 06:12:02 INFO Transforming 100 rows
2026-05-30 06:12:02 INFO Transformation complete: 100 rows, 18 columns
2026-05-30 06:12:03 INFO Loading 100 rows to BigQuery: your-project-id.crypto_market_data.coin_markets (mode: WRITE_APPEND)
2026-05-30 06:12:05 INFO Successfully loaded 100 rows. Table now has 100 rows total.
2026-05-30 06:12:05 INFO Pipeline complete

The pipeline exits with code `0` on success and code `1` on any failure. Every error
is logged at `ERROR` level before exit — there are no silent failures.

**Step 6 — Verify the data in BigQuery:**

```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*), MIN(fetched_at), MAX(fetched_at)
   FROM `your-project-id.crypto_market_data.coin_markets`'
```

Run the pipeline a second time to confirm `WRITE_APPEND` behaviour — the row count
doubles and two distinct `fetched_at` timestamps appear.

---

## BigQuery Approach

**Batch load, not streaming inserts:**

BigQuery Sandbox does not reliably support streaming inserts (`insert_rows_json`)
without a billing account attached. More importantly, batch load via
`load_table_from_dataframe` is the correct pattern for a pipeline that runs on a
schedule — streaming inserts are for real-time event streams, not scheduled pulls.
Every load in this pipeline uses `client.load_table_from_dataframe()` exclusively.

**Explicit schema, not autodetect:**

The `BQ_SCHEMA` list in `pipeline.py` declares every column with its type and mode.
`autodetect=True` is never used. Autodetect fails on nullable floats (may infer
INTEGER for a column that occasionally returns null), produces inconsistent results
across library versions, and is unauditable. An explicit schema is self-documenting,
version-controlled, and deterministic across runs.

**WRITE_APPEND with `fetched_at` timestamp:**

The default write mode is `WRITE_APPEND`. Every pipeline run appends a
time-stamped snapshot — the table is a time series, not a current-state store.
This design decision costs almost nothing (one extra timestamp column, one
`MAX(fetched_at)` filter in every query) and unlocks everything: you can query
the latest snapshot, trend any metric over pipeline runs, or detect data drift
between runs. `WRITE_TRUNCATE` would be simpler but irreversibly loses history.
The write mode is configurable via `BQ_WRITE_MODE` env var if needed.

**Two derived fields:**

| Field | Formula | Analytical Purpose |
|---|---|---|
| `volume_to_market_cap_ratio` | `total_volume / market_cap` | Liquidity signal. High ratio = actively traded relative to total size. Filters coins with large market caps but thin real-world participation. |
| `price_range_pct_24h` | `(high_24h − low_24h) / low_24h × 100` | Intraday volatility. Measures price swing size as a percentage of the daily low. Useful for risk profiling independent of price direction. |

Both fields return `NULL` (not an error) when any input is null or when a denominator
is zero. Null-safety is enforced at the row level in `transform()`, not left to
BigQuery to handle downstream.

**BigQuery Sandbox limitations:**

| Limitation | Impact | How This Pipeline Handles It |
|---|---|---|
| No DML (UPDATE, DELETE, MERGE) | Cannot update rows in place | WRITE_APPEND + `fetched_at`; query latest with `WHERE fetched_at = (SELECT MAX(fetched_at) FROM ...)` |
| Tables expire after 60 days | Data loss without billing | Documented; in production, use a billed GCP account with no table expiration |
| No scheduled queries without billing | Cannot automate via BigQuery UI | Cloud Scheduler (production) or GitHub Actions (Sandbox) — see Production Thinking |
| Streaming insert reliability | May fail silently | Not used; batch load exclusively |
| No table partitioning in Sandbox | Higher query cost at scale | Partitioning by `DATE(fetched_at)` is the production recommendation — see Production Thinking |

**Pipeline verification (actual run):**

The pipeline was run against `starry-sylph-409904.crypto_market_data.coin_markets`.
The following was confirmed in the BigQuery console:

| Total Rows | First Run (UTC) | Latest Run (UTC) | Distinct Runs |
|:----------:|-----------------|------------------|:-------------:|
| 200 | 2026-05-30 07:01:30 | 2026-05-30 07:09:30 | 1 |

---

## SQL Summary Query and Output

Three analytical queries are defined in `summary.sql`. Each targets the most recent
pipeline snapshot using the `MAX(fetched_at)` pattern, which is idiomatic for
WRITE_APPEND time-series tables.

**Canonical query pattern for latest-snapshot reads:**

```sql
WHERE fetched_at = (
  SELECT MAX(fetched_at)
  FROM `your-project-id.crypto_market_data.coin_markets`
)
```

---

### Query 1 — Top 10 Coins by Liquidity

Uses the `volume_to_market_cap_ratio` derived field. High ratio means the coin is
actively traded relative to its total market size — a signal of genuine market
participation rather than price inflation.

```sql
SELECT
  coin_name,
  symbol,
  market_cap_rank,
  ROUND(current_price_usd, 4)                AS price_usd,
  ROUND(volume_to_market_cap_ratio * 100, 2) AS volume_to_mcap_pct,
  ROUND(price_change_pct_24h, 2)             AS price_change_24h_pct
FROM `your-project-id.crypto_market_data.coin_markets`
WHERE
  fetched_at = (SELECT MAX(fetched_at) FROM `your-project-id.crypto_market_data.coin_markets`)
  AND volume_to_market_cap_ratio IS NOT NULL
ORDER BY volume_to_market_cap_ratio DESC
LIMIT 10;
```

**Result:**

# Crypto Market Data — Volume to Market Cap

| Coin Name | Symbol | Market Cap Rank | Price (USD) | Volume / MCap % | Price Change 24h % |
|-----------|--------|:--------------:|------------:|:--------------:|:-----------------:|
| Injective | INJ | 87 | $6.75 | 48.75% | +9.39% |
| Artificial Superintelligence Alliance | FET | 97 | $0.2447 | 35.14% | -0.32% |
| Stellar | XLM | 17 | $0.2564 | 31.10% | +24.11% |
| Tether | USDT | 3 | $0.9988 | 30.04% | +0.04% |
| NEAR Protocol | NEAR | 33 | $2.38 | 27.53% | -5.29% |
| USD1 | USD1 | 24 | $0.9984 | 24.30% | +0.05% |
| Worldcoin | WLD | 71 | $0.2956 | 20.08% | -2.12% |
| Sui | SUI | 31 | $0.9003 | 16.14% | -2.51% |
| USDC | USDC | 6 | $0.9997 | 15.97% | +0.02% |
| Filecoin | FIL | 83 | $0.9739 | 15.86% | +1.09% |

---

### Query 2 — Top 10 Coins by Intraday Volatility

Uses the `price_range_pct_24h` derived field. High value means the coin moved a large
percentage between its daily high and low — useful for identifying momentum assets and
assessing risk independent of price direction.

```sql
SELECT
  coin_name,
  symbol,
  market_cap_rank,
  ROUND(current_price_usd, 4)    AS price_usd,
  ROUND(price_range_pct_24h, 2)  AS intraday_volatility_pct,
  ROUND(price_change_pct_24h, 2) AS price_change_24h_pct,
  ROUND(high_24h_usd, 4)         AS high_24h,
  ROUND(low_24h_usd, 4)          AS low_24h
FROM `your-project-id.crypto_market_data.coin_markets`
WHERE
  fetched_at = (SELECT MAX(fetched_at) FROM `your-project-id.crypto_market_data.coin_markets`)
  AND price_range_pct_24h IS NOT NULL
ORDER BY price_range_pct_24h DESC
LIMIT 10;
```

**Result:**

# Crypto Market Data — Intraday Swing

| Coin Name | Symbol | Market Cap Rank | Price (USD) | Intraday Swing % | Net Change 24h % | High 24h | Low 24h |
|-----------|--------|:--------------:|------------:|:---------------:|:----------------:|---------:|--------:|
| Stellar | XLM | 17 | $0.2564 | 46.28% | +24.11% | $0.2954 | $0.2019 |
| Algorand | ALGO | 63 | $0.1272 | 23.87% | +8.90% | $0.1378 | $0.1112 |
| Hedera | HBAR | 27 | $0.0964 | 23.13% | +4.37% | $0.1091 | $0.0886 |
| Injective | INJ | 87 | $6.75 | 18.01% | +9.39% | $7.01 | $5.94 |
| Monero | XMR | 18 | $393.12 | 16.57% | +8.68% | $418.17 | $358.73 |
| NEAR Protocol | NEAR | 33 | $2.38 | 14.47% | -5.29% | $2.61 | $2.28 |
| Artificial Superintelligence Alliance | FET | 97 | $0.2447 | 13.68% | -0.32% | $0.2621 | $0.2305 |
| MemeCore | M | 30 | $2.86 | 12.28% | -6.60% | $3.20 | $2.85 |
| VeChain | VET | 100 | $0.0062 | 9.83% | +4.34% | $0.0063 | $0.0057 |
| Zcash | ZEC | 16 | $518.33 | 9.82% | -4.07% | $554.95 | $505.31 |

---

### Query 3 — Market Structure by Rank Tier

Aggregates all coins into four rank brackets and shows how total market cap, trading
volume, average price change, and average liquidity are distributed across the market.
Demonstrates GROUP BY aggregation on the derived field at scale.

```sql
SELECT
  CASE
    WHEN market_cap_rank BETWEEN 1  AND 10  THEN '01-10 (Mega Cap)'
    WHEN market_cap_rank BETWEEN 11 AND 25  THEN '11-25 (Large Cap)'
    WHEN market_cap_rank BETWEEN 26 AND 50  THEN '26-50 (Mid Cap)'
    WHEN market_cap_rank BETWEEN 51 AND 100 THEN '51-100 (Small Cap)'
    ELSE 'Unranked'
  END                                              AS rank_tier,
  COUNT(*)                                         AS coin_count,
  ROUND(SUM(market_cap_usd) / 1e9, 2)             AS total_market_cap_bn_usd,
  ROUND(SUM(total_volume_usd) / 1e9, 2)           AS total_volume_bn_usd,
  ROUND(AVG(price_change_pct_24h), 2)             AS avg_price_change_24h_pct,
  ROUND(AVG(volume_to_market_cap_ratio) * 100, 2) AS avg_volume_to_mcap_pct
FROM `your-project-id.crypto_market_data.coin_markets`
WHERE
  fetched_at = (SELECT MAX(fetched_at) FROM `your-project-id.crypto_market_data.coin_markets`)
  AND market_cap_rank IS NOT NULL
GROUP BY rank_tier
ORDER BY rank_tier;
```

**Result:**

# Crypto Market Data — Market Cap by Rank Tier

| Rank Tier | Coin Count | Total Market Cap (B USD) | Total Volume (B USD) | Avg Price Change 24h % | Avg Volume / MCap % |
|-----------|:----------:|------------------------:|--------------------:|:---------------------:|:-------------------:|
| 01–10 (Mega Cap) | 10 | $2,266.43B | $123.06B | +0.60% | 7.02% |
| 11–25 (Large Cap) | 15 | $116.31B | $7.69B | +2.14% | 6.58% |
| 26–50 (Mid Cap) | 25 | $68.57B | $4.33B | -0.57% | 6.13% |
| 51–100 (Small Cap) | 50 | $47.47B | $2.26B | +0.63% | 5.34% |

---

## Production Thinking

### Scheduling

**Sandbox / development (no billing required):**

A GitHub Actions scheduled workflow triggers the pipeline daily on a cron schedule.
Secrets are stored as GitHub repository secrets. This is version-controlled,
team-shareable, and costs nothing.

```yaml
# .github/workflows/pipeline.yml
name: CoinGecko Pipeline

on:
  schedule:
    - cron: '0 5 * * *'   # Daily at 05:00 UTC
  workflow_dispatch:        # Manual trigger for testing

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r task-2/requirements.txt
      - run: python task-2/pipeline.py
        env:
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          BQ_DATASET_ID:  ${{ secrets.BQ_DATASET_ID }}
          BQ_TABLE_ID:    ${{ secrets.BQ_TABLE_ID }}
          GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GOOGLE_APPLICATION_CREDENTIALS }}
```

**Production (full GCP account):**

Cloud Scheduler triggers a Cloud Run Job at `0 5 * * *` (05:00 UTC daily). The Cloud
Run Job runs the pipeline in a Docker container. Cloud Run handles the execution
environment and scaling. Cloud Scheduler integrates natively with GCP IAM — no
credentials to manage separately. This is the target architecture once the pipeline
moves off Sandbox.

---

### Failure Detection

**Layer 1 — Exit code monitoring:**
The pipeline exits with code `0` on success and code `1` on any failure in any stage
(fetch, transform, or load). Cloud Scheduler and GitHub Actions both monitor exit codes
natively. A non-zero exit marks the run as failed and triggers whatever notification
mechanism is configured (Cloud Monitoring alert or GitHub Actions email notification).

**Layer 2 — Log-based alerting (production):**
All pipeline logs are emitted to stdout in a consistent format (`YYYY-MM-DD HH:MM:SS
LEVEL message`). In Cloud Logging, a log-based metric counting `ERROR`-level entries
from the pipeline job feeds a Cloud Monitoring alerting policy. Any `ERROR` in a 1-hour
window triggers a notification. This catches failures even when exit code monitoring
is not reliable (e.g., a scheduler that ignores exit codes).

**Layer 3 — Staleness detection:**
Exit code monitoring only catches failed runs. It does not catch the case where the
scheduler itself fails to trigger. The following query detects that scenario:

```sql
SELECT
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(fetched_at), HOUR) AS hours_since_last_run
FROM `your-project-id.crypto_market_data.coin_markets`
HAVING hours_since_last_run > 26;
```

A Cloud Monitoring alerting policy runs this query on a schedule. If a row is returned
(the table has not been updated in more than 26 hours — the 24-hour schedule plus a
2-hour buffer), an alert fires. This provides end-to-end coverage: the pipeline can fail
to run entirely and still be detected within 2 hours.

---

### Scaling to 10x Volume

At 10x volume — 1,000 coins per run, or 10 endpoints instead of one — four changes
are required.

**Async fetching:** Replace `requests.get()` with `asyncio` + `httpx.AsyncClient`.
A 10-page sequential fetch taking 10+ seconds becomes 2–3 seconds with concurrent
HTTP calls. The transform and load layers are unchanged.

**Chunked BigQuery loads:** Split the DataFrame into 500-row chunks and load
sequentially. This prevents memory pressure on large payloads and allows per-chunk
retry logic without re-fetching all data from the API.

**Table partitioning and clustering:** Add `PARTITION BY DATE(fetched_at)` and
`CLUSTER BY coin_id` to the BigQuery table. Partitioning eliminates full table scans
on all time-range queries — BigQuery reads only the relevant date partition. At
1,000 rows per day across 90 days, unpartitioned queries scan 90,000 rows; partitioned
queries scan 1,000. Clustering reduces intra-partition scan cost further by grouping
coin rows together on disk. These require a billed GCP account (not available in
Sandbox) and are declared in `LoadJobConfig.time_partitioning` and
`LoadJobConfig.clustering_fields`.

**Pipeline metadata table:** Add a `pipeline_runs` BigQuery table that records each
run's UUID, start time, end time, row count, and status (success/failure). This enables
SLA monitoring and drift detection without parsing log files — query the metadata table
to see success rates, average row counts, and time-between-runs directly in SQL.

**Containerised execution:** Package the pipeline in a Docker container deployed to
Cloud Run. The container is reproducible across engineers, portable from local to GCP,
and scales to multiple concurrent workers if parallel endpoint fetching is needed.
A `Dockerfile` and `docker-compose.yml` are the only additions required to the
current codebase.

---

## File Reference

| File | Purpose |
|---|---|
| `pipeline.py` | Main pipeline: fetch → transform → BigQuery load |
| `config.py` | Centralised configuration loaded from environment variables |
| `requirements.txt` | Pinned dependencies for reproducible installs |
| `.env.example` | Template for required environment variables (no real values) |
| `summary.sql` | Three analytical SQL queries with captured output above |
| `walkthrough.md` | Engineering decisions, trade-offs, and what would change with more time |