# Product Brief: ChannelPulse
## Internal Marketing Performance Dashboard

**Author:** Irfhan Ahamed
**Version:** V1  
**Prepared for:** Tacheon x Smacient — Data & AI Product Engineer Assessment

---

## Problem Statement

The team answers one question on a recurring basis: *"How is our marketing performing 
across channels right now, and where should we be focusing?"*

Today, answering that question means one analyst opens three browser tabs — GA4, Google 
Ads, and Meta Ads Manager — pulls numbers, reconciles date ranges, and stitches the result 
into a Notion doc or spreadsheet. The cycle takes 30 to 90 minutes per request and runs 
2–3 times per week. If the analyst is unavailable, the question goes unanswered.

The output looks different every time. Different analysts choose different date windows, 
different metrics, different formats. Two people answering the same question on the same 
day can produce numbers that differ by 10–15%. Over time, this inconsistency erodes trust 
in the numbers — even when the underlying data is accurate.

The root cause is not inefficiency. It is the absence of an automated, canonical data 
layer. No pipeline fetches data from these platforms on a schedule. No unified schema maps 
platform-specific metrics to consistent definitions. No shared view accumulates the work 
of previous pulls so that answering the question this week reduces the effort next week.

---

## Primary User

**The internal analyst — not the client.**

The problem is an internal workflow problem first. The friction lives inside the team: 
one person doing repetitive retrieval work that blocks everyone else. If the tool 
first eliminates that analyst's manual effort, it creates a trusted internal data layer. 
Client-facing views are built on top of that layer in V2 — after the internal team 
trusts what they're seeing.

Building for the client first would require multi-tenancy, access control, authentication, 
and client-appropriate presentation before a single internal number has been validated. 
That is the wrong order.

---

## Tool Form

**A read-only Looker Studio dashboard connected to a BigQuery view.**

The binding constraint is that the team will not change their existing tools or workflows. 
This rules out asking them to adopt a new SaaS analytics platform, learn a new interface, 
or run anything manually on a schedule.

Looker Studio is already available to any team using Google Workspace — no new subscription, 
no new login, no deployment. If Tacheon is already in the GCP ecosystem (which the 
assessment context suggests), this is zero incremental tool adoption. The dashboard is a 
URL. The analyst opens it. That is the full interaction.

The data layer — a BigQuery dataset with one view per channel, joined into a unified 
summary view — is invisible infrastructure. The team never touches it directly after setup.

---

## What a Successful Interaction Looks Like

A team lead has a client call at 10am Monday. At 9:55am they open the dashboard URL. 
Within 60 seconds they can see: which channel drove the most conversions last week, which 
channel had the highest cost-per-click, and whether any channel is trending significantly 
up or down from the prior period. They close the tab. They go into the call with context.

They did not message the analyst. They did not wait for a spreadsheet. They did not open 
a platform dashboard.

That is the interaction. Everything in V1 is designed to make that interaction reliable.

---

## What the Tool Needs to Work

The dashboard reads from a BigQuery dataset that aggregates data from three channels:

**Google Ads → BigQuery:** Native export available in Google Ads settings at no cost. 
Google pushes daily performance data to a specified BigQuery dataset automatically once 
linked.

**GA4 → BigQuery:** Native BigQuery linking available in GA4 Admin at no cost. GA4 
exports events daily once linked.

**Meta Ads Manager → BigQuery:** Meta does not have a native BigQuery export. Two options: 
a custom Python connector following the same pattern as the Task 2 pipeline, or a 
third-party connector (Supermetrics, Funnel.io) if the team already subscribes.

Once these three sources land in BigQuery, a unified summary view joins them on a common 
schema. Looker Studio reads from that view. The analyst opens a URL.

**Data refresh:** Daily at minimum (05:00 UTC, data available by 06:00 UTC). The 
last-updated timestamp is visible on every page of the dashboard — this is the primary 
trust mechanism. Analysts need to know how old the data is before they cite it.

**Access:** Read-only Looker Studio report shared via link. No login required for viewers. 
No edit permissions granted to anyone outside the engineering team.

---

## Success Criteria for V1

V1 has succeeded when the following are all true:

The designated analyst stops performing the manual 30–90 minute pull within 2 weeks of 
launch.

Two team members use the dashboard to answer the performance question without being 
prompted, within 4 weeks of launch.

Dashboard data is within ±5% of platform-native numbers, verified by spot-check in week 2. 
The tolerance accounts for API processing lag and attribution window differences across 
platforms.

The last-updated timestamp is visible and accurate on every page from day 1.

---

## What Is Deliberately Not In V1

**Recommendations ("where should we focus"):** Correct recommendations require calibrated 
benchmarks and historical context that take weeks to establish. A wrong recommendation 
damages trust faster than no recommendation. V1 surfaces the data. The humans make the call.

**Automated alerting:** Alerts require thresholds. Thresholds require a baseline. 
Alerting before the data is trusted produces noise, not signal. V2 feature.

**Multi-client views:** Multi-tenancy adds row-level security, per-client data isolation, 
and access management. V2 architecture decision. V1 validates the approach with one client.

**Client-facing access:** V1 builds internal trust first. Clients see data after the 
internal team has validated it for at least 4 weeks.

The full reasoning for every out-of-scope decision is in `v1-scope.md`.