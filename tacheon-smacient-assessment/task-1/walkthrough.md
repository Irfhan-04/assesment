# Task 1: Walkthrough

**Author:** Irfhan Ahamed  
**Assessment:** Data & AI Product Engineer — Tacheon x Smacient  

---

## Where I Started

The brief asks for a tool that answers two questions: "how is our marketing performing across channels right now?" and "where should we be focusing?" I initially read these as two separate design problems. They are not. The second question is downstream of the first — you can only answer "where to focus" if you trust the answer to "how are we doing." So I scoped toward the first question and deferred the second.

That meant the product I was designing was not a recommendation engine. It was a reliable data surface. That distinction shaped every decision that followed.

## The Decision That Shaped Everything

The single most important call I made was naming the primary user: the internal analyst, not the client.

The problem as described is entirely internal. One person is spending 30–90 minutes manually pulling and reconciling data from three platforms every time the performance question comes up. That person is the analyst. The client does not have that friction — they just wait for the answer. The analyst generates it.

If I had scoped V1 for the client, I would have needed to solve multi-brand access control, authentication, and client-appropriate presentation before validating that the underlying data is even trustworthy. That adds two to three weeks of scope before the first user gets any value. V1 solves the internal problem. Once the internal team trusts the numbers, giving a client access is a shared link, not a rebuild.

## How I Determined V1 Scope

I started from the hard constraint — the team will not change their existing tools — and worked outward.

That constraint immediately pointed toward the Google ecosystem. The firm is BigQuery-heavy by context. If the team uses Google Workspace, Looker Studio is already available at no cost. No new login. No new subscription. No onboarding. The tool form chose itself before I finished reading the brief.

From there, I picked channels by coverage and engineering cost. Paid Search, Paid Social, and Organic Web account for the majority of measurable spend and traffic for any agency client running standard campaigns. Each additional channel follows the same pipeline pattern — a new connector, not a new architecture. Starting with three means V1 ships and gets validated. Starting with six means V1 ships late or not at all.

For metrics, I held a strict filter: does this metric answer the question "how is marketing performing right now?" Impressions and CTR failed that filter. They describe attention, not outcomes. If an analyst needs impressions data for a specific client conversation, they can open the platform. The dashboard's job is to answer the operational question, not to replicate every view available in every platform.

## What I Almost Included But Didn't

Two decisions gave me genuine pause before I cut them.

**Period-over-period comparison.** Showing last week versus the prior week felt like an obvious inclusion — it requires no new data sources, just two rolling windows. I moved it from Must Have to Should Have for one specific reason: on launch day, the pipeline has only run once. There is no prior period. Displaying a delta against a missing baseline either errors or shows zero, which is actively misleading. I do not want the dashboard to show a wrong number on day one to avoid admitting a feature is not ready. The visual layout supports adding period-over-period as soon as the second week of clean data is confirmed.

**Attribution model mismatch.** During research, I found that Google Ads and Meta Ads use different default attribution windows — Google defaults to data-driven attribution, Meta defaults to 7-day click plus 1-day view. If the pipeline ingests conversions from both without normalizing the attribution window, the "Conversions" column across those two channels is not a direct comparison. It is comparing apples and attribution-adjusted oranges.

I decided not to solve this in V1, but I did not ignore it. The correct V1 approach is to use platform-native metric definitions — this is faster to build and easier to audit — and to document the limitation explicitly. The analyst using this dashboard needs to know that cross-channel conversion comparisons carry a caveat until the attribution windows are standardized per brand. A note in the README and a tooltip in the dashboard carry that information without requiring weeks of additional spec work before anything ships.

A related issue that I flagged separately: Meta finalizes some conversion metrics up to 48 hours after the event. A pipeline running at 06:00 UTC daily loads yesterday's Meta data before some conversions have finished processing. This means yesterday's Paid Social conversion count shown in the dashboard may be understated. The last-updated timestamp tells the user how old the data is, but it does not tell them that the numbers from two days ago are more reliable than yesterday's numbers. That is a data communication problem, not a pipeline design problem — but it warrants a visible note in the dashboard.

## What Would Change in V2

Multi-brand support is the natural next feature, but it requires a different BigQuery schema: a `brand_id` key on every table, row-level security policies, and per-brand Looker Studio reports rather than a single shared dashboard. The V1 architecture supports this as an extension — it is a new column and a new access layer, not a schema redesign.

Automated recommendations — "where should we focus?" — require a baseline. The pipeline needs to run cleanly for four to eight weeks before any threshold or benchmark is meaningful. I explicitly scoped this out of V1 because a wrong recommendation damages trust faster than no recommendation. The data layer comes first.

Alerting follows the same logic. You need to know what "normal" looks like before you can alert on anomalies. Four weeks of clean history establishes that. Alerting before that point generates noise.

## What I'd Want to Validate Before Building Anything

Three things need to be confirmed before a single line of pipeline code is written for the production marketing version of this tool:

**Metric definitions per brand.** What counts as a conversion in GA4 for this client? What counts as a "result" in Meta for this campaign objective? These are not universal — they are configured differently per account and per campaign goal. Schema is expensive to change. Metric definitions need to be locked before schema is finalized.

**GA4 and Google Ads BigQuery linking status.** Both have free native exports to BigQuery. If they are not yet linked, that is a 1–2 day setup task that must happen before any pipeline work begins. It is not a blocker, but it is a dependency that can silently delay V1 if it is discovered late.

**Attribution window alignment decision.** The team needs to make a call: show platform-native attribution for speed, or standardize to a single window for cross-channel comparability. V1 uses platform-native. V2 should revisit this with actual data in hand, because the right answer depends on how clients actually use the comparison — something that requires using V1 for a month to understand.