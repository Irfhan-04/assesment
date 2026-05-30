# CLAUDE.md — tacheon-smacient-assessment

This is a 4-day technical assessment for the Data & AI Product Engineer role at Tacheon x Smacient.
Two tasks: Task 1 is product scoping (Markdown documents, no code). Task 2 is a Python data pipeline
(CoinGecko API → transform → BigQuery). Assessment evaluators read commit history, code decisions,
and written walkthroughs. Everything Claude Code produces here is evaluation evidence.

---

## Bash Commands

```bash
# Setup (run once from task-2/)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the pipeline
python task-2/pipeline.py

# Authenticate with BigQuery (local dev, run once)
gcloud auth application-default login

# Verify BigQuery table loaded (replace with your project/dataset)
bq query --use_legacy_sql=false \
  'SELECT COUNT(*), MAX(fetched_at) FROM `PROJECT.crypto_market_data.coin_markets`'

# Run a summary query
bq query --use_legacy_sql=false < task-2/summary.sql
```

---

## Repository Structure

```
tacheon-smacient-assessment/
├── CLAUDE.md                    ← this file
├── README.md                    ← root overview, links to both tasks
├── task-1/                      ← product scoping (Markdown only, no code)
│   ├── README.md
│   ├── product-brief.md
│   ├── v1-scope.md
│   └── walkthrough.md
└── task-2/                      ← pipeline (Python + BigQuery)
    ├── pipeline.py
    ├── config.py
    ├── summary.sql
    ├── requirements.txt
    ├── .env.example
    └── README.md
```

---

## Task 2 — Code Conventions

**Parameterisation is non-negotiable.**
Every value that could vary between environments lives in an environment variable, read via `config.py`.
`pipeline.py` contains zero hardcoded project IDs, dataset names, table names, endpoints, row limits,
currency codes, timeouts, or write modes. If you are about to type a string literal that is a
configuration value, stop and add an env var instead.

**Explicit BigQuery schema. Never autodetect.**
The `BQ_SCHEMA` list in `pipeline.py` defines every column with its type and mode.
Do not pass `autodetect=True` to `LoadJobConfig`. Autodetect breaks on nullable floats and is
unreliable across schema versions.

**Batch load only. No streaming inserts.**
Use `client.load_table_from_dataframe()` exclusively. BigQuery Sandbox does not reliably support
streaming inserts without billing. Do not use `client.insert_rows_json()` or `to_gbq()`.

**Write mode is `WRITE_APPEND` by default.**
Every pipeline run appends a time-stamped snapshot. Do not switch to `WRITE_TRUNCATE` unless
the `BQ_WRITE_MODE` env var explicitly sets it. The `fetched_at` column is how snapshots are versioned.

**Type coercion in transform is explicit.**
Apply `pd.to_numeric(col, errors='coerce')` to every numeric column before computing derived fields.
Never assume the API returns a float — it may return `None`, an int, or a string.

**Derived fields return `None` on bad input.**
`volume_to_market_cap_ratio` and `price_range_pct_24h` must return `None` if any input is null
or if a denominator is zero. Use row-level `apply()` with explicit null guards — do not let
division-by-zero exceptions propagate.

**Column order must match `BQ_SCHEMA` before load.**
Reorder the DataFrame columns to `[field.name for field in BQ_SCHEMA]` as the final transform step.
Positional mismatches cause silent type errors at load time.

**Functions have docstrings.**
Every function (`fetch_coin_markets`, `transform`, `load_to_bigquery`, `load_config`, `main`)
has a docstring stating its purpose, key parameters, return type, and what it raises.

---

## Logging Conventions

Use Python's `logging` module. Never use `print()`.

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
```

Log at these points:
- `INFO` on pipeline start with parameter summary
- `INFO` on fetch completion with row count
- `INFO` on transform completion with row and column counts
- `INFO` on BQ load start with table reference and row count
- `INFO` on BQ load completion with total table row count
- `ERROR` on any exception with the full exception message (truncate API response body to 500 chars)

---

## Error Handling

Each of the three pipeline stages (fetch, transform, load) has its own try/except in `main()`.
A failure in any stage logs `ERROR`, prints the exception, and calls `sys.exit(1)`.
The pipeline never partially loads data — if transform or load fails, nothing is written.

```python
# Pattern for every stage in main()
try:
    result = stage_function(config)
except (SpecificError, AnotherError) as exc:
    logger.error("Stage name failed: %s", exc)
    sys.exit(1)
```

---

## BigQuery — Sandbox Constraints

The BigQuery Sandbox (free tier, no billing) has these hard limits:
- No DML (UPDATE, DELETE, MERGE) — query with `WHERE fetched_at = MAX(fetched_at)` instead
- No scheduled queries — document Cloud Scheduler as the production path
- Tables expire after 60 days — document this in README; do not set expiration programmatically
- No streaming inserts reliably — use batch load (already enforced above)

Never add `time_partitioning` or `range_partitioning` to `LoadJobConfig` in Sandbox code —
document partitioning as a production recommendation in README instead.

---

## CoinGecko API

Endpoint: `GET https://api.coingecko.com/api/v3/coins/markets`
No API key required on free tier. Rate limit: ~10–30 req/min — not a concern for a scheduled run.

Params (all from config): `vs_currency`, `order=market_cap_desc`, `per_page`, `page`,
`sparkline=false`, `price_change_percentage=24h,7d`

Response is a JSON array. Validate with `isinstance(data, list) and len(data) > 0` before transforming.

---

## Commit Conventions

Format: `<type>(<scope>): <imperative lowercase description>`
Types: `init`, `task-1`, `task-2`, `fix`, `docs`, `refactor`

Commit at every logical checkpoint — not every file save, but every meaningful unit of progress.
Minimum 14 commits spread across 4 days. A single final commit defeats the purpose of the assessment.

```
init: scaffold repo structure for both assessment tasks
task-1: add product brief draft with primary user and tool form decisions
task-2: add pipeline.py with fetch, transform, and bigquery load
task-2: verified pipeline runs end-to-end, data loaded to bigquery
fix: remove hardcoded project id from pipeline.py
```

---

## What Never to Do

- Hardcode any value in `pipeline.py` or `config.py` that belongs in `.env`
- Use `autodetect=True` on `LoadJobConfig`
- Use `client.insert_rows_json()` or streaming insert patterns
- Use `print()` instead of `logging`
- Let a derived field raise a `ZeroDivisionError` or `TypeError` at runtime
- Let the pipeline exit with code 0 after a failed stage
- Commit the real `.env` file (it must be in `.gitignore`)
- Write real GCP project IDs, credentials, or keys in `.env.example`
- Write code in `task-1/` — that folder contains only Markdown documents
- Add a single large commit at the end of the project

---

## Task 1 — Writing Conventions

`task-1/` contains four Markdown files: `product-brief.md`, `v1-scope.md`, `README.md`, `walkthrough.md`.
These are prose documents, not code. When editing them:

- Write in direct technical English — no hedging, no filler phrases
- Every exclusion in `v1-scope.md` must include an explicit "Reason:" line
- `walkthrough.md` reads as a first-person narrative of decisions made, not a feature list
- Do not add code blocks, diagrams, or tables unless they make a specific point clearer

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GCP_PROJECT_ID` | Yes | — | GCP project ID (from BigQuery console) |
| `BQ_DATASET_ID` | Yes | — | BigQuery dataset name |
| `BQ_TABLE_ID` | Yes | — | BigQuery table name |
| `COINGECKO_VS_CURRENCY` | No | `usd` | Quote currency |
| `COINGECKO_PER_PAGE` | No | `100` | Rows per API page (max 250) |
| `COINGECKO_PAGE` | No | `1` | API page number |
| `REQUEST_TIMEOUT_SECONDS` | No | `30` | HTTP request timeout |
| `BQ_WRITE_MODE` | No | `WRITE_APPEND` | `WRITE_APPEND` or `WRITE_TRUNCATE` |
| `GOOGLE_APPLICATION_CREDENTIALS` | No* | — | Path to service account JSON (*not needed with ADC) |

For local development, use `gcloud auth application-default login` — no JSON key file needed.
For CI/GitHub Actions, store the service account JSON as a repository secret.
