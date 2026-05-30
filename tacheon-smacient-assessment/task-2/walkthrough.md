# Task 2: Walkthrough

## Why CoinGecko

I evaluated three API candidates: CoinGecko, Open-Meteo, and NewsAPI.

Open-Meteo was the first to go. The weather API returns flat, pre-cleaned arrays with 
no transformation work to demonstrate — the data arrives essentially ready to load. 
That would make the transform step trivial, which defeats the point of demonstrating 
pipeline engineering.

NewsAPI was the second cut. It requires an API key (additional setup friction for an 
assessment reviewer) and returns semi-structured article metadata with limited 
numerical fields. There is no natural opportunity for derived fields that add real 
analytical value.

CoinGecko requires no API key on the free tier, returns richly nested JSON with 
~30 fields per coin, and has natural input fields for two genuinely different derived 
metrics — one measuring liquidity, one measuring volatility. The free tier provides 
100 coins per page at rates nowhere near the limit for a single scheduled run. The 
SQL summary queries are also genuinely interesting: top coins by liquidity is a 
different analytical question from top coins by intraday volatility, which is 
different from how capital distributes across market tiers. Three distinct questions 
from one dataset.

## How I Structured the Pipeline

I split the pipeline into four functions with a single orchestrator (`main`). Each 
function does one thing and fails independently. If the API is down, `fetch_coin_markets` 
raises — `transform` never runs. If transform fails, nothing is written to BigQuery.

The orchestrator handles exit codes; the stage functions handle logic. This separation 
matters in practice: when something fails in production, you can identify exactly which 
stage failed from the ERROR log without reading the code.

`load_config` runs at startup and raises `ValueError` immediately on any missing 
required variable. I prefer failing at startup over failing mid-run — a startup failure 
is clean and obvious; a mid-run failure after a successful API call is confusing to debug.

All parameters flow through the `config` dict returned by `load_config`. Nothing in 
`pipeline.py` calls `os.getenv` directly. If you want to trace where a value came from, 
you look in one place.

## The Derived Fields and Why They Matter

**volume_to_market_cap_ratio** = `total_volume / market_cap`

This is a liquidity signal. A ratio of 0.05 means 5% of the total market cap traded 
hands in the last 24 hours. High ratios indicate actively traded, liquid assets — coins 
where you can enter and exit a position without significant price impact. Low ratios 
indicate thinly traded assets with large market caps on paper but limited real-world 
tradability.

Volume alone is correlated with market cap — Bitcoin will always have more raw volume 
than an obscure small-cap. The ratio normalises for size, which is the analytically 
meaningful signal.

**price_range_pct_24h** = `(high_24h - low_24h) / low_24h × 100`

This is an intraday volatility signal. A value of 8.0 means the price moved 8% between 
its daily low and daily high. A coin with a small net 24h price change might still have 
had a large intraday swing — the net change hides that information. This field surfaces it.

Both fields use row-level `apply()` with explicit null guards rather than vectorised 
division. Vectorised division silently produces `NaN` when the denominator is zero or 
null. I want explicit `None` values in those cases, which map cleanly to BigQuery `NULL`.
`NaN` in a DataFrame column causes type errors at BigQuery load time.

## BigQuery Design Decisions

**WRITE_APPEND over WRITE_TRUNCATE.** WRITE_TRUNCATE is simpler — the table always holds 
the current state. WRITE_APPEND turns every run into a time-stamped snapshot. For almost 
no added complexity (one timestamp column, one `MAX(fetched_at)` filter in queries), I 
get time-series behaviour: I can trend any metric over pipeline runs, detect data drift 
between snapshots, and query any historical state by filtering on `fetched_at`. For a 
scheduled pipeline, time-series storage is the correct default. Choosing WRITE_TRUNCATE 
would be an irreversible decision that eliminates this capability.

**Explicit schema over autodetect.** Autodetect is unreliable on nullable floats — it 
may infer INTEGER for a column that is usually an integer but occasionally returns a float 
or null. It also fails inconsistently across library versions and provides no 
documentation of the schema in code. An explicit `BQ_SCHEMA` list at module level is 
self-documenting, version-controlled, and produces consistent load behaviour across 
environments.

**Batch load over streaming inserts.** BigQuery Sandbox does not reliably support 
streaming inserts without a billing account. Beyond the Sandbox constraint, batch load 
via `load_table_from_dataframe` is also the correct pattern for a pipeline that runs on 
a schedule — streaming inserts are designed for real-time event streams, not hourly or 
daily batch jobs.

**Why `crypto_market_data` as the dataset name.** Task 2 is a proof of concept for the 
ingestion pattern, not the actual marketing performance pipeline. The dataset name reflects 
what it actually contains. The `marketing_performance` dataset described in Task 1 would 
be set up separately in production with the GA4, Google Ads, and Meta sources.

## What I'd Do Differently With More Time

The biggest missing piece is retry logic. Currently, any transient network failure exits 
with code 1 and nothing is retried. A 503 from CoinGecko that self-resolves in 10 seconds 
causes a failed run. Adding `tenacity` with `@retry(stop=stop_after_attempt(3), 
wait=wait_exponential(multiplier=1, min=2, max=30))` on `fetch_coin_markets` would handle 
this cleanly with minimal code.

The second gap is a `pipeline_runs` metadata table. Currently, observability depends on 
log parsing. A BigQuery table that records run ID, start time, end time, row count, and 
status would let me monitor SLA compliance with a SQL query — "how many runs failed in 
the last 7 days?" — without touching Cloud Logging.

Third, I would add a post-load data quality assertion: verify that the row count loaded 
matches what was fetched, and that both derived fields have non-null values for at least 
90% of rows. If either check fails, the pipeline should log a WARNING and write to the 
metadata table — but not necessarily exit with code 1, since partial data is better than 
no data in most cases.

## What Would Change at Production Scale

**10x data volume (1,000 coins per run, 10 API pages):**

The fetch layer needs to go async. CoinGecko's free tier allows 250 per page, so 1,000 
coins requires 4 paginated requests. Sequential requests take 4× as long as concurrent 
ones. Replacing `requests` with `asyncio` + `httpx.AsyncClient` for concurrent pagination 
would cut fetch time by 70–80%.

The BigQuery load should be chunked — 500-row chunks with per-chunk error handling — 
rather than a single DataFrame call. This prevents memory pressure on large payloads and 
allows per-chunk retry without re-fetching all data.

The table should be partitioned by `DATE(fetched_at)` and clustered by `coin_id`. 
Partitioning eliminates full table scans on time-range queries. At 100 rows per run, 
this is not a cost concern. At 10,000 rows per run across 365 days, it is.

**Production deployment:**

The local script would move to a Docker container deployed to Cloud Run, triggered by 
Cloud Scheduler. Cloud Run handles the execution environment, Cloud Scheduler handles 
the trigger, and GCP IAM handles authentication via a service account. No servers to 
maintain. Monthly cost at this scale is negligible.

The GitHub Actions scheduled workflow I documented as the Sandbox-compatible alternative 
demonstrates the same architectural intent without requiring a billing account — it's an 
honest proxy for the Cloud Run + Cloud Scheduler pattern.