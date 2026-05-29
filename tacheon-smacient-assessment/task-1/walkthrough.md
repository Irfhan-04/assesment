# Task 1: Walkthrough

This narrative covers the thinking process behind the scope decisions for ChannelPulse V1.
It reads in the order decisions were made, not in the order the documents are structured.

---

## Where I Started

The brief gives one question the tool must answer: *"How is our marketing performing across
channels right now, and where should we be focusing?"*

The first thing I did was split that question in two. "Right now" is a data retrieval
problem — reliable pipeline, consistent schema, accurate numbers available without manual
work. "Where should we be focusing" is a recommendation problem — it requires normalised
benchmarks, historical context, and business rules calibrated per client.

V1 can only credibly solve one of those. A recommendation engine built before the
underlying data is trusted is not a recommendation engine — it is a liability. If the
numbers are wrong, the recommendation is confidently wrong. That is worse than no
recommendation.

So V1 solves "right now." Everything in the scope follows from that choice.

---

## The Primary User Decision

The brief does not name a user. The problem it describes — one analyst spending 30–90
minutes pulling and stitching data per request — names the user indirectly. The person
doing that manual work is the primary user.

I considered building for the client first. The argument is superficially compelling:
client visibility is what the business cares about, client-facing features are what
gets noticed, starting there creates immediate external value. I rejected it for two
reasons.

The brief describes an internal problem, not a client experience problem. The friction
is inside the team before it ever reaches a client interface. Solving it requires fixing
the internal data layer. You cannot build client-facing trust on an internal data layer
that has not been validated.

And: clients should see data the internal team already trusts. The sequence matters.
V1 builds internal trust. V2 surfaces it externally.

Once I committed to the internal analyst as the primary user, the tool form became
obvious. She already uses Google Workspace. She needs a URL she can open without
logging in. She needs numbers that match what she would find manually. Looker Studio
connected to BigQuery satisfies all three of those with zero new adoption cost.

---

## How I Worked Out V1 Scope

I started with the minimum that makes the core question answerable and worked outward.

The core question is a comparison: "which channel is performing best right now." You
cannot answer a comparison question with a single channel. Three channels — Paid Search,
Paid Social, Organic Web — is the minimum that makes the comparison meaningful and covers
where most clients concentrate budget and measurable traffic.

Four metrics per channel came from the same logic. The question has four natural
dimensions for a paid channel: how much traffic (clicks), how much outcome (conversions),
how much cost (spend), and how efficient (ROAS or CPC). Dropping any one leaves a gap.
Adding impressions, CTR, or frequency adds noise — those metrics explain the four, they
do not replace them.

Single client for V1 was the decision I expected to defend most. The counterargument is
"design for N from the start." My answer: adding `brand_id` to the BigQuery schema and
a row-level access policy is two hours of engineering. It is not a rearchitect. Starting
with one client is not a technical limitation — it is a scope decision that lets V1
launch, get validated, and earn the right to V2 complexity.

---

## What I Almost Included

**Automated alerting.** This was the hardest exclusion. The brief explicitly names "where
should we be focusing" — and an alert on a spend spike or a conversion drop is a direct
answer to that. I excluded it because alerts require thresholds, thresholds require a
baseline, and a baseline requires trusting the data first. A false alert in week one —
fired because the data itself is inconsistent, not because performance changed — is the
fastest way to kill adoption of a new tool. The team will start ignoring the alerts, and
once alerts are ignored, the alerting system has negative value.

**Campaign-level drill-down.** The brief names one question at the channel level. Campaign-
level answers a different question — which specific campaign within a channel to investigate.
That is an analyst optimisation tool, not a status-check tool. Including it adds dashboard
complexity for a use case the brief did not name. I wanted to include it. I cut it.

**Week-over-week delta indicators.** These are genuinely useful and not hard to build —
two more columns in the BigQuery view. I deferred them to V2 because they require two
consecutive weeks of pipeline history before the numbers mean anything. In the first week
of V1, a delta indicator would show N/A or compare against incomplete data. V2, after two
full weeks of history, is the right time.

---

## What V2 Looks Like

V2 has three priorities in order:

The Meta Ads connector needs a real solution. Google Ads and GA4 both have native BigQuery
exports that require no custom code. Meta does not. V1 uses a manual CSV export as an
interim. V2 either builds a first-party Python connector against the Meta Marketing API
(same pattern as Task 2) or confirms a third-party connector is already in the team's
subscription.

Multi-brand support. Once V1 is validated with one client, adding `brand_id` to the
schema, a row-level access policy in BigQuery, and a brand selector in Looker Studio
is under a day of engineering. The architecture already supports it. V2 just turns it on.

Period-over-period deltas and trend indicators. After 30+ days of history, these become
meaningful. Week-over-week and month-over-month comparisons turn the dashboard from
"what is the number" to "is the number moving in the right direction."

---

## What I Would Validate Before Writing a Line of Pipeline Code

Three questions need answers before any engineering starts:

What is a "conversion" for each brand in each channel? This definition must be locked
before the schema is designed. Google Ads conversion actions, Meta campaign objective
results, and GA4 goal completions are all called "conversions" in their respective
platforms. They are not the same thing. The schema needs a `conversion_definition` field
or a documented mapping — not assumptions.

Is GA4 already linked to BigQuery? If yes, the organic data pipeline is a BigQuery view
on an existing export, not an API integration. If no, linking is free and takes ten
minutes in GA4 Admin — but it needs to happen before the pipeline architecture is
finalised.

Does the team already pay for Supermetrics or a similar connector? If yes, the Meta Ads
problem is already solved. If no, the Meta Ads connector is a V1 build dependency that
needs explicit scoping before the sprint starts.

These three answers change the build plan more than any architecture decision in this
scope document.