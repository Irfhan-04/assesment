# Task 1: Product Scoping — Decision Record

**Product:** ChannelPulse — Internal Marketing Performance Dashboard
**Author:** Irfhan Ahamed
**Version:** V1

This document explains the decisions behind `product-brief.md` and `v1-scope.md`. Not what
was built — why it was built that way, what alternatives were considered, and what changes
with more time or information.

---

## The Decision That Shaped Everything: Primary User Is the Internal Analyst

The brief does not name a primary user. It describes a problem: one person manually
pulling data from three platforms and stitching it together. That person is the internal
analyst.

Building for the client first was the obvious alternative. A client-facing dashboard
looks like more product value — it is visible, it is the thing the business cares about.
But it is the wrong starting point for two reasons.

First, the friction described in the brief is internal. The analyst's 30–90 minutes per
request is the problem worth solving. If you build the client-facing view before validating
the underlying data, you are adding polish to something unvalidated. A client who sees a
number that contradicts their platform view loses trust in the tool — and in the agency.

Second, clients should see data the internal team already trusts. V1 builds that trust.
V2 exposes it.

Once the primary user decision is made, the tool form follows directly. The analyst needs
fast access to accurate numbers. She already uses Google Workspace. A URL she can open
without logging in, backed by a daily-refreshed BigQuery view, solves her problem with
zero new adoption cost.

---

## Tool Form: Looker Studio + BigQuery

Three alternatives were considered and rejected:

**Custom React dashboard:** Gives full control over logic and presentation. Requires
hosting, deployment, ongoing maintenance, and a new URL the team has to remember. Violates
the binding constraint — the team will not change their tools or add new workflows.

**SaaS analytics tool (Metabase, Grafana, Tableau):** Polished and capable. Requires a
new subscription, a new login, and onboarding. Violates the same constraint.

**Google Sheets via Connected Sheets:** Seriously considered. Zero adoption cost, already
in Google Workspace, familiar to the analyst. Rejected because Looker Studio handles the
date range toggle, visual layout, and sharing link pattern more cleanly for a dashboard
use case. Sheets is the right answer if the output is a tabular report. A channel
comparison dashboard is not a table.

Looker Studio wins because it is already in the team's orbit, requires no new subscription,
no deployment, and no training. The dashboard is a URL. That is the entire UX ask.

---

## V1 Scope Boundaries

**Three channels, not four or five.** The engineering pattern for adding a fourth channel
is identical to adding the third — a new connector, a new view column, a new dashboard
panel. There is no architectural reason to limit to three. The reason is to validate the
pattern with three before scaling it. Every channel added in V1 adds a new dependency that
could block the launch.

**Four metrics per channel.** Clicks/Sessions, Conversions, Spend, ROAS/CPC answer the
core question. Impressions and CTR describe reach, not performance. Frequency and CPM are
optimisation inputs, not status-check outputs. Adding them adds noise to a question that
has a clean four-metric answer.

**Single client.** The argument for multi-client from the start is: "if you build it for
one, design it for N." The counter-argument: adding `brand_id` and a row-level access
policy to the BigQuery schema is two hours of engineering in V2, not a full rearchitect.
Starting with one client is risk management. It lets V1 launch and get validated before
multiplying the failure surface.

---

## What I Would Revisit With More Time

**The Meta Ads connector.** Google Ads and GA4 both have native BigQuery exports — link
once in the platform admin, no code required. Meta Ads does not. The V1 assumption is a
manual CSV export or an existing Supermetrics subscription. Before finalising the V1 build
plan, I would confirm whether Supermetrics is already in the team's stack. If not, the
Meta Ads connector needs to be scoped explicitly — either a first-party Python connector
against the Meta Marketing API (same pattern as Task 2) or a third-party tool.

**Metric definition alignment per brand.** "Conversions" means different things across
platforms: Google Ads conversion actions, Meta campaign objective results, GA4 goal
completions. I assumed these are aligned per client before the pipeline is built. In
practice this requires a documented per-brand metric definitions table — exactly which
GA4 goal, which Google Ads conversion action, which Meta objective maps to "conversions"
for each client. Without this locked down, two analysts can look at the same dashboard
number and interpret it differently.

**The client-facing timeline.** I scoped client access as V2 without knowing how quickly
the business needs it. If client-facing data access is a Q2 priority, that constraint
should influence the V1 BigQuery schema design — specifically whether row-level security
is designed in from day one or retrofitted later. A four-week difference in V2 timeline
can change whether the V1 schema is a foundation or a rework.

---

## Key Trade-offs Made

**WRITE_APPEND over WRITE_TRUNCATE.** WRITE_APPEND with a `fetched_at` timestamp gives
every pipeline run a version key. All summary queries use `WHERE fetched_at = MAX(fetched_at)`
to operate on the latest snapshot. The trade-off is a slightly more complex query pattern
in exchange for time-series capability with no additional engineering. For any scheduled
pipeline, this is the correct default — WRITE_TRUNCATE loses history that cannot be
recovered.

**Daily refresh over near-real-time.** GA4 has a 24–48 hour processing delay for some
events. Google Ads conversion attribution can lag up to 72 hours. Meta's Ads Insights
data is not final until 48 hours post-delivery. Daily refresh is honest. Near-real-time
would require surfacing numbers that the source platforms themselves have not finalised.
The last-updated timestamp visible on every dashboard page is the communication layer
that makes this trade-off acceptable.

**Looker Studio's design constraints over full presentation control.** Looker Studio
imposes its own design language and limits what custom logic can live in the presentation
layer. A custom dashboard can display anything the data supports. The binding constraint
("the team will not change tools") made this easy — the question was never "custom vs.
Looker Studio." It was "Looker Studio or nothing deployable in V1."

---

## What Was Explicitly Ruled Out and Why

The full reasoning for every out-of-scope decision is in `v1-scope.md`. The three most
consequential exclusions:

**Recommendations.** A recommendation built on uncalibrated benchmarks is a confident
wrong answer. Wrong answers damage trust faster than no answer. V2, after 8+ weeks of
clean history, is when calibration is possible.

**Automated alerting.** Alerts before a baseline exists generate noise. The first false
alert in week one of a new tool is the fastest path to the tool being ignored. V2,
after 30 days of clean pipeline data, is when thresholds can be set with confidence.

**Campaign-level drill-down.** The brief names one question: "how is marketing performing
across channels." Campaign-level data answers a different question — why a specific channel
is performing the way it is. Adding it to V1 solves a problem the brief did not name while
increasing dashboard complexity for the problem it did name.