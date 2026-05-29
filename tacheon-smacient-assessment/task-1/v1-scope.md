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

**Metric source:** Paid metrics (spend, ROAS, CPC, conversions from paid) come from 
their native platform — Google Ads for Paid Search, Meta for Paid Social. Organic 
sessions and conversions come from GA4. Using GA4 as the source for paid conversions 
would introduce attribution model conflicts that make the numbers structurally incomparable. 
Platform-native sourcing keeps each channel's numbers internally consistent.

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
**Reason:** Each platform reports conversions using a fundamentally different attribution 
model. Meta uses 7-day click + 1-day view-through attribution; Google Ads uses last-click 
with a 30-day lookback; GA4 uses data-driven attribution across a 90-day window. A 20–40% 
gap between platform-reported conversions is structurally normal — it is not a data quality 
problem, it is a definitional one. Making a "focus on channel X" recommendation from 
numbers that are not comparable without a normalized attribution model would produce 
misleading guidance. V1 surfaces what each platform reports. Interpreting those numbers 
correctly requires the analyst's domain knowledge. Recommendations are a V2 feature, 
after an attribution strategy has been agreed and a baseline established.

### Automated alerting and anomaly detection
**Reason:** Alerts require thresholds. Thresholds require a validated baseline. A baseline 
requires at least 4 weeks of clean, trusted pipeline history. Alerting before the data 
is trusted generates noise — notifications for changes that are normal variance or pipeline 
lag, not real anomalies. Every false alert erodes confidence in the system. V2 feature.

### Multi-client or multi-brand support
**Reason:** Multi-tenancy requires row-level security policies in BigQuery, per-client 
dataset isolation or view-level access control, and an identity layer that maps dashboard 
users to their permitted data. This multiplies data modeling complexity by 3–5x before 
the single-client version has been validated. V2 architectural decision.

### Campaign-level drill-down
**Reason:** Channel-level data answers the core question. Campaign-level is an 
optimisation tool — it is what an analyst reaches for when they already know which 
channel to investigate and want to understand why. Adding it to V1 increases dashboard 
complexity without serving the status-check use case. It also requires a more complex 
data model that is out of scope for V1.

### Historical data beyond 30 days
**Reason:** Backfilling historical data from three platforms requires careful handling of 
rate limits, API pagination, date-range query patterns per platform, and reconciliation 
of schema changes over time. This is a separate engineering project. V1 builds the 
forward-going daily pipeline first. Once stable for 30 days, a historical backfill can 
be scoped with real knowledge of each source's edge cases.

### Client-facing access
**Reason:** Clients should see data that the internal team has already validated. V1 
builds that internal trust first. Client-facing views require additional QA for data 
accuracy, per-brand access control, and a more polished UI. Exposing clients to 
unvalidated data is a trust liability, not a product feature.

### Real-time or near-real-time data
**Reason:** GA4 has a 24–48 hour processing delay for some events. Google Ads conversion 
attribution can be delayed up to 72 hours. Meta's Ads Insights API does not finalize 
delivery numbers until 48 hours after the ad ran — data pulled before that window closes 
will change. Claiming "real-time" from these sources would require misrepresenting 
freshness. Daily refresh at 05:00 UTC, with data available by 06:00 UTC, is both 
achievable and honest. The last-updated timestamp makes this explicit.

### Cross-platform attribution normalization
**Reason:** Resolving the structural attribution differences between platforms (Meta's 
view-through model vs. Google's last-click vs. GA4's data-driven model) requires a 
dedicated attribution project: a unified identity graph, agreed conversion definitions, 
and a normalization layer that none of these platforms provide natively. This is a 
significant data science project, not a dashboard feature. V1 shows platform-native 
numbers clearly. Normalization is a V2+ initiative.

### LinkedIn Ads, TikTok Ads, email channel
**Reason:** Three channels prove the architecture. The engineering pattern for adding a 
fourth or fifth channel is identical — a new connector, a new column in the unified view, 
a new panel in the dashboard. Start with three, validate the pattern, then scale it.

### Predictive forecasting
**Reason:** Forecasting requires a minimum of 8–12 weeks of stable historical data and 
an explicit modeling decision. The baseline data does not exist yet. V2 or later.

### Automated reporting or push delivery (email, Slack)
**Reason:** Push delivery adds infrastructure before pull access has been validated. 
V2 feature.

---

## V2 Candidates (In Priority Order)

1. Period-over-period deltas and trend indicators (requires 2 weeks of history)
2. Automated staleness alert if pipeline has not run in 26+ hours
3. Campaign-level drill-down for Paid Search and Paid Social
4. Multi-brand support with row-level security
5. Historical backfill (90-day rolling window)
6. Client-facing read-only views per brand
7. Threshold-based alerting (spend spike, conversion drop)
8. Attribution normalization layer (requires dedicated data science project)
9. "Where to focus" recommendations using normalized, calibrated benchmarks