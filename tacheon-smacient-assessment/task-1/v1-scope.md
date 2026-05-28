# V1 Scope Document: ChannelPulse

**Version:** V1  
**Status:** Confirmed for engineering

This document defines the boundaries of ChannelPulse V1. Every item in the out-of-scope 
section has an explicit reason. Scope decisions without reasons are just wishes.

---

## In Scope

### Channels
Three channels: **Paid Search (Google Ads)**, **Paid Social (Meta Ads)**, **Organic Web (GA4)**.

These three cover the majority of where the team's clients spend marketing budget and 
generate measurable traffic. Adding a fourth channel follows the same engineering pattern — 
a new connector, not a new architecture. Proving the pattern with three channels before 
scaling it is the correct sequencing.

### Time Windows
**Rolling 7-day** (default) and **rolling 30-day** (toggle).

These are the two windows analysts reach for first. Rolling 7-day answers "how are we 
doing right now." Rolling 30-day answers "how is this month tracking." Week-over-week and 
month-over-month comparisons are derived from these same windows without additional 
complexity. Calendar-week and custom date ranges are out of scope for V1.

### Metrics Per Channel
**Clicks or Sessions, Conversions, Spend, ROAS or CPC.**

Four metrics per channel answer the core question — volume, outcome, cost, and efficiency. 
Impressions and reach are excluded: they describe how much the team showed up, not how 
marketing is performing.

For Organic Web: Sessions and Conversions are shown. Spend and ROAS display as N/A — 
organic has no spend, and showing zero is misleading.

### Scope
**Single client/brand.**

V1 serves one client. Multi-tenancy is a V2 architectural decision. Starting with one 
client lets the team validate data accuracy and establish trust before multiplying scope.

### Access
**Read-only Looker Studio dashboard, shared via link, no login required.**

The dashboard URL is the entire UX. No account setup, no permissions management, no 
onboarding for the people using it.

### Last-Updated Timestamp
**Visible on every page of the dashboard.**

Trust in the data depends on knowing how fresh it is. The timestamp reflects when the 
pipeline last ran, read directly from `MAX(fetched_at)` in the BigQuery view — not when 
the page was loaded.

---

## Out of Scope

### "Where should we focus" recommendations
**Reason:** Answering this correctly requires normalized benchmarks — what is a good ROAS 
for this client's industry, budget, and growth stage? These benchmarks take weeks to 
calibrate and are specific to each brand. An incorrect recommendation based on 
uncalibrated data is worse than no recommendation. V1 surfaces the data. The analyst 
interprets it. Recommendations are a V2 feature after 8+ weeks of clean data establishes 
the baseline they require.

### Automated alerting and anomaly detection
**Reason:** Alerts require thresholds. Thresholds require a validated baseline. A baseline 
requires at least 4 weeks of clean, trusted pipeline history. Alerting before the data is 
trusted generates noise — the team receives notifications for changes that turn out to be 
normal variance or pipeline lag, not real anomalies. Every false alert erodes confidence 
in the system. V2 feature, after V1 has been used and trusted for a full month.

### Multi-client or multi-brand support
**Reason:** Multi-tenancy requires row-level security policies in BigQuery, per-client 
dataset isolation or view-level access control, and an identity layer that maps dashboard 
users to their permitted data. This multiplies data modeling complexity by 3–5x and adds 
operational burden before the single-client version has been validated. V2 architectural 
decision.

### Campaign-level drill-down
**Reason:** Channel-level data answers the core question. Campaign-level is an 
optimisation tool — it is what an analyst reaches for when they already know which channel 
to investigate and want to understand why. Adding it to V1 increases dashboard complexity 
without serving the primary use case (status check, not investigation). It also requires 
a more complex data model that is out of scope for V1.

### Historical data beyond 30 days
**Reason:** Backfilling historical data from three platforms requires careful handling of 
rate limits, API pagination, date-range query patterns per platform, and reconciliation of 
schema changes over time. This is a separate engineering project. V1 builds the 
forward-going daily pipeline first. Once the pipeline has been running stably for 30 days, 
a historical backfill can be scoped with real knowledge of what edge cases exist in each 
source's data.

### Client-facing access
**Reason:** Clients should see data that the internal team has already validated and trusts. 
V1 builds that internal trust first. Client-facing views require additional QA for data 
accuracy, per-brand access control, and a more polished UI that reflects the agency's 
presentation standards. Exposing clients to unvalidated data is a trust liability, not a 
product feature.

### Real-time or near-real-time data
**Reason:** GA4 has a 24–48 hour processing delay for some events. Google Ads conversion 
attribution can be delayed up to 72 hours. Meta's Ads Insights data is not considered 
final until 48 hours after delivery. Claiming "real-time" from these sources would require 
misrepresenting data freshness. Daily refresh at 05:00 UTC is both achievable and honest. 
The last-updated timestamp makes the freshness explicit.

### LinkedIn Ads, TikTok Ads, email channel
**Reason:** Three channels prove the architecture. The engineering pattern for adding a 
fourth or fifth channel is identical — a new connector feeding the same schema, a new 
column in the unified view, a new panel in the dashboard. Start with three, validate the 
pattern, then scale it. Adding channels before V1 is stable is scope creep disguised as 
ambition.

### Predictive forecasting
**Reason:** Forecasting requires a minimum of 8–12 weeks of stable historical data and an 
explicit modeling decision. The baseline data does not exist yet. V2 or later.

### Automated reporting or push delivery (email, Slack)
**Reason:** Push delivery adds infrastructure before pull access has been validated. If 
the team is not yet habitually using the dashboard, adding push delivery creates a 
notification layer on top of an untrusted data source. V2 feature.

---

## V2 Candidates (In Priority Order)

1. Period-over-period deltas and trend indicators (requires 2 weeks of history)
2. Automated staleness alert if pipeline has not run in 26+ hours
3. Campaign-level drill-down for Paid Search and Paid Social
4. Multi-brand support with row-level security
5. Historical backfill (90-day rolling window)
6. Client-facing read-only views per brand
7. Threshold-based alerting (spend spike, conversion drop)
8. "Where to focus" recommendations using calibrated benchmarks