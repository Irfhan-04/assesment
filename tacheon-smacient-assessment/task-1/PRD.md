# Product Requirements Document
# ChannelPulse — Internal Marketing Performance Dashboard

---

| | |
|---|---|
| **Product Name** | ChannelPulse |
| **Document Type** | Product Requirements Document (PRD) |
| **Version** | 1.0 — Final |
| **Status** | Submitted for Engineering Review |
| **Author** | [Your Name], Data & AI Product Engineer |
| **Stakeholder Review** | Rohit Uttamchandani — Tacheon x Smacient |
| **Created** | Day 1 of Assessment |
| **Last Updated** | Day 4 of Assessment |

---

## Revision History

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| 0.1 | Day 1 | [Your Name] | Problem framing, primary user decision, tool form decision |
| 0.2 | Day 2 | [Your Name] | User personas, user journey maps, V1 scope decisions |
| 0.3 | Day 3 | [Your Name] | Functional requirements, architecture, data model, schema |
| 0.4 | Day 3 | [Your Name] | Decision log, RAID, technical debt register |
| 1.0 | Day 4 | [Your Name] | Final review, open questions, appendix complete |

---

## Table of Contents

**Part I — Context & Strategy**
1. Executive Summary
2. Problem Statement
3. Product Vision & Positioning
4. Goals & Success Metrics

**Part II — Users & Requirements**
5. Stakeholder Map
6. User Personas
7. User Journey Maps
8. User Stories & Acceptance Criteria
9. Functional Requirements
10. Non-Functional Requirements

**Part III — Product Design**
11. Information Architecture
12. Screen Descriptions
13. Data Requirements

**Part IV — Technical Architecture**
14. System Architecture
15. Data Architecture & Schema
16. Integration Specifications
17. Pipeline Specification

**Part V — Scope, Risk & Delivery**
18. V1 Scope Definition
19. Decision Log
20. RAID Log
21. Technical Debt Register
22. Implementation & Rollout Plan
23. Production Operations
24. Open Questions
25. Appendix

---

# Part I — Context & Strategy

---

## 1. Executive Summary

ChannelPulse is an always-on internal marketing performance dashboard that answers one recurring question — *"How is our marketing performing across channels right now, and where should we be focusing?"* — in under 60 seconds, without requiring any manual data work.

Today, answering this question means one analyst opens three browser tabs (GA4, Google Ads, Meta Ads Manager), pulls numbers, and stitches them into a spreadsheet. The output is inconsistent, person-dependent, and takes 30–90 minutes per request. If the analyst is unavailable, the question goes unanswered.

V1 of ChannelPulse eliminates this friction for the internal team. It is a read-only Looker Studio dashboard connected to a BigQuery view, refreshed daily, shared via link, requiring no login and no new tool adoption. The underlying data pipeline — the same architectural pattern demonstrated in Task 2 with the CoinGecko API — fetches, transforms, and loads marketing performance data on a schedule. The team never runs anything manually.

This PRD defines the complete product and technical requirements for V1. It documents what is being built, who it is for, exactly what is in and out of scope, every decision made and its rationale, and what was ruled out. The document is written to serve as both the spec for engineers and the decision record for stakeholders.

---

## 2. Problem Statement

### 2.1 The Current State

The team supports multiple client brands on marketing performance across three primary channels: Paid Search (Google Ads), Paid Social (Meta Ads Manager), and Organic Web (GA4). When anyone — internal team lead, junior analyst, or client contact — asks *"how is our marketing performing right now?"*, the following sequence happens:

```
Question asked
      ↓
Analyst opens GA4 → pulls organic sessions + conversions (10 min)
      ↓
Analyst opens Google Ads → pulls clicks + spend + ROAS (15 min)
      ↓
Analyst opens Meta Ads Manager → pulls clicks + spend + ROAS (15 min)
      ↓
Analyst reconciles date ranges and metric definitions (20 min)
      ↓
Analyst pastes into Notion/Sheets and formats (15 min)
      ↓
Answer delivered: 30–90 minutes after the question was asked
```

The total effort per request is 30–90 minutes. The team fields this question 2–3 times per week. That is 60–270 minutes of analyst time per week spent on data retrieval, not analysis.

### 2.2 Root Cause Analysis

The root cause is not that the team is inefficient. It is that there is no automated canonical data layer. No pipeline pulls data from these platforms on a schedule. No unified schema maps platform-specific metric names to consistent definitions. No shared view accumulates results so that the work of pulling one week's numbers applies to the next time the question is asked.

Every single time the question is asked, the full retrieval effort is repeated from scratch. The knowledge of how to pull the data lives in one person's head. The answer format is not standardized. The effort does not compound toward anything.

### 2.3 The Four Specific Failure Modes

**Inconsistency.** The answer looks different depending on who prepares it. Different analysts use different date ranges (calendar week vs. rolling 7 days), different attribution windows, and different metric selections. Two people answering the same question on the same day can produce numbers that differ by 10–15%.

**Person-dependency.** If the designated analyst is unavailable, the question waits. There is no fallback. No other team member knows the exact steps to pull and reconcile the data correctly.

**Trust erosion.** When the same question produces different answers at different times, stakeholders begin to distrust the numbers — even when the underlying data is correct. Inconsistency is perceived as inaccuracy.

**No accumulation of work.** Answering the question this week does not make answering it next week any faster. Every pull is a fresh start with no reuse.

### 2.4 The Binding Constraint

The team will not change the tools they use or the way they currently work. This is not negotiable. Any solution must fit around existing workflows. This rules out:

- Asking the team to adopt a new SaaS analytics platform
- Requiring analysts to run scripts or learn new interfaces
- Building anything that requires ongoing manual input from the people using it
- Creating a new data entry step that introduces a new failure point

The solution must be invisible as infrastructure and obvious as output.

### 2.5 Why Solve This Now

The question is being asked 2–3 times per week and growing as the team takes on more clients. At two clients, one analyst managing the manual process is a friction. At five clients, it is a bottleneck. At ten clients, it is a scaling failure. The cost of not solving this compounds as the team grows. The architecture to solve it is available today at effectively zero incremental cost (BigQuery + Looker Studio within the Google Workspace subscription the team already has).

---

## 3. Product Vision & Positioning

### 3.1 Vision Statement

Give every person on the team — regardless of their technical depth — the ability to answer the core marketing performance question in under 60 seconds, with data they trust, without opening a single source platform.

### 3.2 What This Product Is

A lightweight, always-on, automatically refreshed, read-only marketing performance dashboard that consolidates key metrics across three channels into a single view. Infrastructure the team never thinks about. An answer that is always there when someone looks.

### 3.3 What This Product Is Not

It is not a recommendation engine. It does not tell the team where to focus. It surfaces data and lets the humans make that call. Automated recommendations require calibrated benchmarks that take weeks to establish, and a wrong recommendation damages trust faster than no recommendation at all.

It is not a reporting tool for clients. Client access, branding, and presentation are V2 concerns. V1 builds internal trust first.

It is not a campaign management interface. It reads from platforms. It never writes to them.

It is not a replacement for any existing tool. GA4, Google Ads, and Meta Ads Manager remain the systems of record. ChannelPulse is a read layer on top of them.

### 3.4 Competitive Positioning

The team already has access to third-party connector tools (Supermetrics, Funnel.io, Fivetran) that solve a version of this problem. ChannelPulse is not a direct competitor — it is a simpler, cheaper, more controllable alternative for a team where the data volume does not justify the cost and complexity of a full connector subscription. The architecture is the team's own, maintainable by any engineer, and extendable without a vendor dependency.

---

## 4. Goals & Success Metrics

### 4.1 Business Goals (OKR Format)

**Objective 1: Eliminate manual data retrieval for weekly performance checks.**

Key Results:
- The designated analyst spends zero minutes on manual data stitching for standard performance questions within 4 weeks of launch.
- At least 2 team members use the dashboard to answer the performance question without being prompted, within 4 weeks of launch.
- The number of times the performance question goes unanswered due to analyst unavailability drops to zero.

**Objective 2: Establish a single canonical answer to the marketing performance question.**

Key Results:
- Two team members looking at the dashboard on the same day see identical numbers within 4 weeks of launch.
- Data accuracy within ±5% of platform-native numbers (accounting for API processing lag) verified by spot-check in week 2.
- Last-updated timestamp is visible on every dashboard page from day 1.

**Objective 3: Build the data infrastructure foundation for future intelligence features.**

Key Results:
- BigQuery dataset is queryable and accumulates a rolling 90-day history of daily snapshots within 30 days of launch.
- Pipeline runs successfully on schedule with ≥99% success rate over 30 consecutive days.
- A second channel can be added to the pipeline by any engineer in under 4 hours of work.

### 4.2 V1 Measurable Success Criteria

These are the binary pass/fail criteria for declaring V1 a success. They are observable, not aspirational.

| Criterion | Measurement | Target |
|---|---|---|
| Answer speed | Time from opening dashboard to answering the performance question | ≤ 60 seconds |
| Data freshness | Age of data shown on dashboard at any point during business hours | ≤ 24 hours |
| Data accuracy | Deviation from platform-native numbers | ≤ ±5% |
| Adoption | Distinct team members using the dashboard without prompting | ≥ 2 within 4 weeks |
| Manual pull reduction | Analyst still performing manual stitching process | Zero instances within 2 weeks |
| Pipeline reliability | Successful scheduled runs over 30 days | ≥ 99% |

### 4.3 Anti-Goals

Stating what this product does not try to achieve is as important as stating what it does. These are explicit non-goals for V1:

- We are not trying to replace GA4, Google Ads, or Meta Ads Manager as the system of record.
- We are not trying to surface every metric those platforms provide.
- We are not trying to serve clients directly — that is a V2 concern.
- We are not trying to answer *why* performance is at a certain level — only *what* it is.
- We are not trying to achieve real-time data — daily refresh is the target.

---

# Part II — Users & Requirements

---

## 5. Stakeholder Map

| Stakeholder | Role | Decision Authority | Primary Interest |
|---|---|---|---|
| **Internal Analyst** | Primary user | Uses the tool daily; provides feedback | Eliminating manual data work |
| **Marketing Team Lead** | Secondary user, project sponsor | Approves V1 scope; champions adoption | Answering performance questions before client calls |
| **Data / Engineering Team** | Builders and maintainers | Owns architecture and pipeline decisions | Clean, maintainable infrastructure |
| **Client Brand Contacts** | Future users (V2) | N/A for V1 | Self-serve access to their brand's data |
| **Tacheon Leadership (Rohit)** | Evaluator of this PRD | Assessing product thinking and technical decision quality | Clear reasoning, deliberate scope, honest trade-offs |

---

## 6. User Personas

### 6.1 Primary Persona — The Internal Analyst

**Name:** Priya  
**Title:** Marketing Analyst  
**Technical Depth:** High comfort with GA4, Google Ads UI, Meta Ads Manager, Notion, and spreadsheets. Has used BigQuery before but does not write SQL regularly. Does not write code. Not aware of API integrations but understands data freshness, attribution windows, and metric definitions well.

**Goal:** Answer the performance question quickly and move on to actual analysis work — identifying trends, flagging anomalies, building client narratives. She does not want to spend time on retrieval.

**Current Pain:** 30–90 minutes per performance question request, 2–3 times per week. She has internalized this as "part of the job" rather than something that can be fixed. She will adopt a better tool if it shows her accurate numbers and doesn't require anything new to learn.

**Trust Triggers:** Numbers that match what she would find if she went to the source. A visible "data as of [timestamp]" label. No configuration required before viewing.

**Distrust Triggers:** Any number that differs unexpectedly from the platform. A dashboard that loads and shows "no data." A tool that requires her to do anything before seeing results.

**Success:** Priya stops performing the manual pull within 2 weeks of launch. She opens the dashboard URL instead. She tells the team lead she trusts the numbers.

---

### 6.2 Secondary Persona — The Team Lead

**Name:** Arjun  
**Title:** Marketing Team Lead  
**Technical Depth:** Comfortable with slide decks, Notion, and client presentations. Does not look at platform dashboards. Asks Priya for performance summaries before calls and reviews.

**Goal:** Have performance context before client conversations without creating a dependency on Priya's availability.

**Current Pain:** He asks Priya for numbers before every client call. If she is in a meeting, he goes into the call without context or delays it. He trusts her numbers completely — but the process requires her to be available.

**Trust Triggers:** Same numbers as Priya sees. A "last updated" timestamp that tells him the data is current. Labels in plain language (not platform jargon).

**Distrust Triggers:** Numbers that contradict what Priya reported last week without an obvious explanation. A dashboard that requires him to set up or configure anything.

**Success:** Arjun checks the dashboard before his Monday client calls without messaging Priya first. He has not changed his workflow — he is just opening a URL instead of sending a Slack message.

---

### 6.3 Future Persona — The Client Contact (V2 Only)

**Name:** Client Brand Marketing Manager  
**Note:** Explicitly excluded from V1. Including them would require row-level data isolation per brand, per-client access control, authentication, and a more polished UI with client-appropriate branding. V1 does none of this. This persona is documented here so that V2 planning does not need to re-litigate why they were excluded from V1.

---

## 7. User Journey Maps

### 7.1 Current State Journey (The Painful Path)

```
TRIGGER: Team lead asks "how did paid search perform last week?"
│
├── Priya opens GA4
│   ├── Sets date range (rolling 7 days)
│   ├── Navigates to Acquisition → Traffic Acquisition
│   ├── Filters to Organic Search
│   ├── Pulls: Sessions, Goal Completions
│   └── Copies numbers to Notion doc [10–15 min]
│
├── Priya opens Google Ads
│   ├── Sets date range (must match GA4 manually)
│   ├── Navigates to Campaigns → Overview
│   ├── Pulls: Clicks, Cost, Conversions, ROAS
│   └── Copies numbers to Notion doc [10–15 min]
│
├── Priya opens Meta Ads Manager
│   ├── Sets date range (must match manually — again)
│   ├── Selects account and date window
│   ├── Pulls: Clicks, Spend, Results, ROAS
│   └── Copies numbers to Notion doc [10–15 min]
│
├── Priya reconciles numbers
│   ├── Checks date ranges are aligned
│   ├── Checks metric definitions match expectations
│   └── Formats into a shareable view [15–20 min]
│
└── Priya sends to Arjun [30–90 min total]

FAILURE MODES:
  - Arjun asks while Priya is in a meeting → question waits
  - Different date range used → numbers don't match last week's report
  - Priya is out → question goes unanswered
  - Two people pull separately → different numbers, trust eroded
```

### 7.2 Target State Journey (ChannelPulse)

```
TRIGGER: Team lead wants to know how paid search performed last week
│
├── Arjun opens the ChannelPulse dashboard URL
│   └── No login required [0 min]
│
├── Dashboard loads — all three channels side by side
│   ├── Sees: Paid Search | Paid Social | Organic Web
│   ├── Rolling 7-day window loaded by default
│   ├── Metrics visible: Clicks/Sessions, Conversions, Spend, ROAS/CPC
│   └── "Data as of [yesterday 06:00 UTC]" timestamp visible [<5 seconds]
│
├── Arjun reads the numbers
│   └── Question answered [<60 seconds from opening the URL]
│
└── Arjun closes the tab and prepares for the call [0 additional minutes]

PRIYA'S PARALLEL EXPERIENCE:
  - Priya has not received a message from Arjun about performance
  - No manual pull required
  - Her time is spent on analysis, not retrieval
```

### 7.3 Key Moments of Value

**Moment 1 — First successful load:** The first time Arjun opens the dashboard and sees numbers that match what Priya would have pulled, without asking her. This is when V1 has proven its concept.

**Moment 2 — First unaided use:** The first time any team member opens the dashboard without being told to, because a question came up and they remembered the URL existed. This is when V1 has achieved genuine adoption.

**Moment 3 — First time the question gets answered without Priya:** The first time Arjun answers a performance question in a client call using dashboard data, without Priya being in the room. This is when V1 has eliminated the person-dependency.

---

## 8. User Stories & Acceptance Criteria

Priority notation: **[M]** = Must Have | **[S]** = Should Have | **[C]** = Could Have | **[W]** = Won't Have (V1)

---

**US-01 [M] — Weekly channel performance check**

As Priya (internal analyst), I want to open a single URL and immediately see last week's performance across Paid Search, Paid Social, and Organic Web, so that I can answer the performance question without opening any platform dashboards.

*Acceptance Criteria:*
- **Given** I have the dashboard URL, **when** I open it in a browser, **then** the dashboard loads within 5 seconds with no login prompt
- **Given** the dashboard has loaded, **when** I look at the default view, **then** I can see all three channels (Paid Search, Paid Social, Organic Web) on a single screen without scrolling
- **Given** I am on the default view, **when** I read the time window label, **then** it shows "Last 7 days" or equivalent rolling-window label
- **Given** the dashboard is showing data, **when** I look for a freshness indicator, **then** I can see a "Data as of [timestamp]" label accurate to the hour

---

**US-02 [M] — Pre-call performance check (no analyst required)**

As Arjun (team lead), I want to check current marketing performance before a client call without asking Priya, so that I can discuss channel performance with confidence regardless of Priya's availability.

*Acceptance Criteria:*
- **Given** I have the dashboard link, **when** I open it on any device with internet access, **then** I see current data without needing to be added to any access list
- **Given** I am looking at the dashboard, **when** I read the metric labels, **then** they are in plain language (e.g., "Website Sessions" not "GA4 Organic Entrances")
- **Given** I want to see last month's context, **when** I toggle to the 30-day view, **then** the same metrics are shown for the rolling 30-day window

---

**US-03 [M] — Channel comparison**

As Priya, I want to see all three channels' key metrics side by side on one screen, so that I can immediately identify which channel is performing best on any given metric this week.

*Acceptance Criteria:*
- **Given** I am on the main dashboard view, **when** I look at the channel comparison area, **then** I can see Paid Search, Paid Social, and Organic Web metrics in columns or panels that can be visually compared
- **Given** the data is loaded, **when** I look at each channel panel, **then** I can see at minimum: clicks or sessions, conversions, spend (where applicable), and ROAS or CPC (where applicable)
- **Given** organic web data is shown, **when** I look at the spend and ROAS fields, **then** they are displayed as "N/A" or hidden — organic does not have spend

---

**US-04 [M] — Data freshness transparency**

As any team member, I want to know exactly when the dashboard data was last updated, so that I can decide whether it is current enough for a client conversation.

*Acceptance Criteria:*
- **Given** the dashboard is open, **when** I look at any page, **then** a "Last updated: [datetime]" label is visible without scrolling
- **Given** the pipeline ran successfully last night, **when** I look at the timestamp, **then** it reflects last night's run — not today's page load time
- **Given** the pipeline has not run in more than 26 hours (schedule plus 2-hour buffer), **when** I look at the dashboard, **then** a visual warning or stale-data indicator is shown

---

**US-05 [M] — Pipeline reliability (engineering)**

As the data engineer, I want the pipeline to fail loudly with an observable signal rather than silently loading bad data, so that I know immediately when a run has failed.

*Acceptance Criteria:*
- **Given** the pipeline encounters an HTTP error on the API call, **when** the error occurs, **then** the pipeline logs ERROR with the HTTP status code and exits with code 1 — no data is written to BigQuery
- **Given** the pipeline encounters a BigQuery load failure, **when** the error occurs, **then** the pipeline logs ERROR with the exception message and exits with code 1 — no partial rows are written
- **Given** the pipeline runs successfully, **when** it completes, **then** it exits with code 0 and logs the row count loaded and the total table row count
- **Given** the scheduler (cron or Cloud Scheduler) monitors exit codes, **when** the pipeline exits with code 1, **then** the scheduler marks the run as failed and triggers whatever notification mechanism is configured

---

**US-06 [M] — Zero-config execution (engineering)**

As any engineer on the team, I want to run the pipeline by setting environment variables and executing one command, so that setting up a new environment takes under 30 minutes.

*Acceptance Criteria:*
- **Given** I have cloned the repository and have a Google account with BigQuery access, **when** I follow the README setup instructions, **then** I can run the pipeline successfully in under 30 minutes
- **Given** I want to change the target BigQuery table, **when** I update the `BQ_TABLE_ID` environment variable and re-run the pipeline, **then** data loads to the new table without any code changes
- **Given** I look at `pipeline.py`, **when** I search for hardcoded project IDs, table names, currency codes, or row limits, **then** I find none

---

**US-07 [S] — Period-over-period comparison**

As Priya, I want to see how this week's performance compares to last week for each channel, so that I can flag trends without manually calculating deltas.

*Acceptance Criteria:*
- **Given** I am on the 7-day view, **when** I look at any metric, **then** I can see the current period value and the delta vs. the prior 7-day period (e.g., "+12%" or "−3%")
- **Given** a metric is significantly up or down (>20% vs. prior period), **when** I look at that metric, **then** there is a visual indicator (colour or arrow) that draws attention to the change

---

**US-08 [C] — Metric definition access**

As Priya, I want to understand exactly how each metric is defined, so that I can explain the numbers confidently to clients.

*Acceptance Criteria:*
- **Given** I am looking at any metric, **when** I hover over or click an info icon next to the metric name, **then** I see a one-sentence definition (e.g., "Conversions: Goal completions as defined in GA4 for this brand")

---

**US-09 [W — V2] — Multi-client view**

As any team member, I want to switch between clients and see performance for each brand separately.

*(Explicitly out of scope for V1 — see Section 18.2 for reasoning.)*

---

## 9. Functional Requirements

Grouped by area. Priority: **[M]** Must Have | **[S]** Should Have | **[C]** Could Have | **[W]** Won't Have in V1.

### 9.1 Data Display

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-01 | Display metrics for three channels: Paid Search, Paid Social, Organic Web | M | These three cover the majority of client spend |
| FR-02 | Rolling 7-day window shown by default | M | Answers "right now" |
| FR-03 | Toggle to rolling 30-day window | M | Answers "this month" |
| FR-04 | Per-channel metrics: Clicks/Sessions, Conversions, Spend, ROAS or CPC | M | Four metrics answer the core question |
| FR-05 | Organic Web shows Sessions and Conversions; Spend and ROAS shown as N/A | M | Organic has no spend; showing zero is misleading |
| FR-06 | Last-updated timestamp visible on every page | M | Core trust mechanism |
| FR-07 | Period-over-period delta displayed for each metric | S | Requires two periods of pipeline history |
| FR-08 | Visual indicator (colour or arrow) for significant changes (>20% delta) | S | Draws attention to outliers |
| FR-09 | Metric definition accessible via tooltip or info icon | C | Reduces onboarding friction |
| FR-10 | Single brand/client view only | M | V1 constraint; multi-brand is V2 |

### 9.2 Access & Availability

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-11 | Dashboard accessible via shared Looker Studio link | M | No login required for link-based access |
| FR-12 | Dashboard loads in ≤ 5 seconds | M | Measured on standard business broadband |
| FR-13 | Dashboard is read-only; no user can modify data or filters persistently | M | Non-negotiable for data integrity |
| FR-14 | Data refreshes automatically on daily schedule — no manual trigger | M | Invisible infrastructure |
| FR-15 | Dashboard works on desktop and tablet browsers | M | Team uses laptops and iPads |
| FR-16 | Dashboard works on mobile browser | C | Nice-to-have for on-the-go access |

### 9.3 Trust & Data Quality

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-17 | Last-updated timestamp reflects pipeline run time, not page load time | M | Must read from `MAX(fetched_at)` in BigQuery |
| FR-18 | Metrics match source platform values within ±5% | M | Verified by spot-check; tolerance accounts for API lag |
| FR-19 | Null or missing metric values shown as "—" not "0" | M | Zero implies no activity; null implies missing data |
| FR-20 | Stale data indicator shown if data is >26 hours old | S | 24h schedule + 2h buffer |
| FR-21 | No metrics calculated differently than their platform-native definition | M | Consistency is the product |

### 9.4 Pipeline (Engineering)

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-22 | Pipeline fetches data from public API on a schedule | M | No manual trigger |
| FR-23 | All parameters read from environment variables | M | Zero hardcoded values |
| FR-24 | Full error handling: fetch, transform, and load each have try/except | M | No silent failures |
| FR-25 | Structured logging at every pipeline step | M | INFO on progress, ERROR on failure |
| FR-26 | Exit code 0 on success, non-zero on any failure | M | Enables scheduler failure detection |
| FR-27 | At least one derived analytical field computed during transform | M | Demonstrates data enrichment |
| FR-28 | BigQuery load uses explicit schema (not autodetect) | M | Prevents type mismatch failures |
| FR-29 | BigQuery write mode defaults to WRITE_APPEND | M | Enables time-series queries |
| FR-30 | At least one SQL aggregation query delivered in `summary.sql` | M | Proves data is queryable |

---

## 10. Non-Functional Requirements

### 10.1 Performance

| NFR | Requirement | Measurement |
|---|---|---|
| NFR-01 | Dashboard load time ≤ 5 seconds | Measured via browser network tab on standard broadband |
| NFR-02 | Pipeline full run (fetch → transform → BQ load) ≤ 120 seconds for 100 rows | Measured from script start to exit |
| NFR-03 | BigQuery summary queries execute in ≤ 10 seconds | Measured in BigQuery console on unpartitioned table |

### 10.2 Reliability

| NFR | Requirement |
|---|---|
| NFR-04 | Pipeline scheduled run success rate ≥ 99% over any 30-day window |
| NFR-05 | No silent failures — every failure produces a non-zero exit code and an ERROR log entry |
| NFR-06 | No partial BigQuery loads — pipeline either loads all rows or no rows for a given run |
| NFR-07 | Dashboard data staleness ≤ 24 hours under normal operation |

### 10.3 Maintainability

| NFR | Requirement |
|---|---|
| NFR-08 | A new engineer can run the pipeline following README in ≤ 30 minutes |
| NFR-09 | Adding a new channel to the pipeline requires changes in ≤ 3 files |
| NFR-10 | All pipeline functions have docstrings with purpose, parameters, return type, and exceptions |
| NFR-11 | Configuration changes require no code edits — env vars only |

### 10.4 Security

| NFR | Requirement |
|---|---|
| NFR-12 | No credentials, project IDs, or real values in any committed file |
| NFR-13 | `.env` is in `.gitignore`; `.env.example` contains template keys only |
| NFR-14 | Service account follows least privilege: BigQuery Data Editor + BigQuery Job User only |
| NFR-15 | Dashboard is read-only; no authenticated write surface is exposed |

### 10.5 Observability

| NFR | Requirement |
|---|---|
| NFR-16 | Log format: `YYYY-MM-DD HH:MM:SS LEVEL message` on stdout |
| NFR-17 | In production: Cloud Monitoring alert fires on any ERROR-level log entry from the pipeline |
| NFR-18 | In production: staleness alert fires if `MAX(fetched_at)` is older than `CURRENT_TIMESTAMP() - INTERVAL 26 HOUR` |

---

# Part III — Product Design

---

## 11. Information Architecture

The dashboard has a flat, single-page information architecture. There is no navigation, no drill-down, no multi-page flow. The entire product is one view that answers one question.

```
ChannelPulse Dashboard
│
├── Header
│   ├── Product name / logo wordmark
│   ├── Brand / client name
│   ├── Time window selector [7 days | 30 days]
│   └── Last updated: [timestamp]
│
├── Channel Performance Panel (3 columns)
│   ├── Paid Search (Google Ads)
│   │   ├── Clicks
│   │   ├── Conversions
│   │   ├── Spend
│   │   └── ROAS
│   ├── Paid Social (Meta Ads)
│   │   ├── Clicks
│   │   ├── Conversions
│   │   ├── Spend
│   │   └── ROAS
│   └── Organic Web (GA4)
│       ├── Sessions
│       ├── Conversions
│       ├── Spend [N/A]
│       └── CPC [N/A]
│
└── Footer
    └── Data source labels + last pipeline run timestamp
```

The structure is deliberately minimal. Complexity is what makes dashboards unused. The core question — "how is marketing performing across channels right now?" — is answerable from the single channel performance panel without interacting with anything.

---

## 12. Screen Descriptions

No Figma wireframes are delivered in this PRD. The following are wireframe narratives — text descriptions of what each visual element should communicate and how it should behave. A designer or engineer should be able to produce a faithful implementation from these descriptions.

### 12.1 Main Dashboard View

The full-width layout divides into three equal columns, one per channel. Each column has a channel label at the top (e.g., "Paid Search — Google Ads") followed by a stack of metric cards. Each metric card shows: the metric name in a small grey label, the metric value in a large bold number, and — if US-07 is implemented — a directional indicator showing the delta vs. the prior period (e.g., "↑ 12% vs last period" in green, "↓ 8%" in red).

The header spans the full width. On the left: the dashboard name and brand name. On the right: the time window toggle (two tabs labelled "7 days" and "30 days") and the last-updated timestamp in a muted style that does not compete with the metric values.

The colour palette should use neutral grays for structure with a single accent colour for positive/negative indicators. The visual hierarchy priority is: metric value > metric name > period delta > structural chrome.

### 12.2 Time Window Toggle

Two states: "7 days" (default) and "30 days". Switching between them reloads all metric cards with data from the corresponding window. This is handled natively by Looker Studio's date range control connected to the BigQuery view's `date` field. No custom code required.

### 12.3 Channel Metric Cards

Each metric card follows a consistent template:

```
┌─────────────────────┐
│  Clicks             │  ← metric name (small, muted)
│  12,430             │  ← metric value (large, bold)
│  ↑ 8% vs prior      │  ← delta (small, coloured) [US-07]
└─────────────────────┘
```

For organic web, spend and ROAS cards are replaced with a greyed-out "N/A" card with a small label: "Not applicable for organic." This makes it explicit that the absence of spend data is intentional, not missing.

### 12.4 Stale Data Indicator

If the `MAX(fetched_at)` timestamp in the BigQuery view is more than 26 hours old, a yellow banner appears at the top of the dashboard:

```
⚠ Data may be stale — last updated [timestamp]. Pipeline check required.
```

This is implemented via a Looker Studio data source condition. In V1 it is a Should Have; if Looker Studio's conditional formatting cannot surface this cleanly, it is deferred to V2.

---

## 13. Data Requirements

### 13.1 Data Sources (Production Vision)

| Source | Data | Ingestion Method | Refresh Cadence |
|---|---|---|---|
| Google Ads | Clicks, Conversions, Spend, ROAS, CPC | Native BigQuery export (free, in Google Ads settings) | Daily |
| Meta Ads Manager | Clicks, Conversions, Spend, ROAS | Meta Marketing API → Python connector or Supermetrics | Daily |
| GA4 | Sessions, Goal Completions | Native BigQuery linking (free, in GA4 Admin) | Daily |

### 13.2 Metric Definitions

Metric definitions must be locked to consistent definitions before the pipeline is built. Inconsistent definitions are the source of the "two people get different numbers" problem the product is trying to solve.

| Metric | Channel | Definition | Notes |
|---|---|---|---|
| Clicks | Paid Search | Total link clicks from Google Ads campaigns | Uses Google Ads `clicks` field |
| Clicks | Paid Social | Total link clicks from Meta Ad campaigns | Uses Meta `link_clicks` action type specifically (not all clicks) |
| Sessions | Organic | GA4 sessions attributed to Organic Search medium | Filtered on `session_medium = 'organic'` |
| Conversions | Paid Search | Conversions as defined in Google Ads conversion tracking | Must match what the client has configured |
| Conversions | Paid Social | Results as defined in Meta Ads campaign objective | Must be documented per brand |
| Conversions | Organic | Goal completions as defined in GA4 | Must match what the client has configured |
| Spend | Paid Search | Google Ads cost (currency as configured per account) | Shown in USD or account currency |
| Spend | Paid Social | Meta Ads spend (amount_spent field) | Shown in USD or account currency |
| ROAS | Paid | Revenue / Spend | Revenue source must be defined per brand |
| CPC | Paid | Spend / Clicks | Fallback metric when ROAS is not configured |

### 13.3 Freshness Requirements

| Source | Platform Processing Lag | Pipeline Cadence | Data Available By |
|---|---|---|---|
| Google Ads | 3-hour lag typical; up to 24h for conversion attribution | Daily at 05:00 UTC | 06:00 UTC same day |
| Meta Ads | 1–3 hour lag typical | Daily at 05:00 UTC | 06:00 UTC same day |
| GA4 | 24–48 hour lag for some event data | Daily at 05:00 UTC | 06:00 UTC same day |

All sources have non-trivial processing lags. The dashboard must display "data as of [yesterday's date]" by default, not "real-time." Displaying real-time implies fresher data than these sources can provide. The last-updated timestamp is the honest communication of what "current" means here.

---

# Part IV — Technical Architecture

---

## 14. System Architecture

### 14.1 Full Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                              │
│                                                                        │
│  [Google Ads API]      [Meta Marketing API]      [GA4 BigQuery Link] │
│  clicks, spend,         clicks, spend,             sessions,          │
│  conversions, ROAS      conversions, ROAS           goal completions   │
│                                                                        │
│  [CoinGecko API] ← Task 2 proof-of-concept for the ingestion pattern │
│  coin markets, prices, volume, market cap                             │
└────────────┬─────────────────┬──────────────────────┬────────────────┘
             │                 │                       │
             ▼                 ▼                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER — Python                           │
│                                                                        │
│  pipeline.py                                                           │
│  ├── load_config()        reads env vars, fails fast if missing       │
│  ├── fetch_data()         GET request, error handling, timeout        │
│  ├── transform()          flatten, clean types, derived fields        │
│  └── load_to_bigquery()   batch load, explicit schema, WRITE_APPEND  │
│                                                                        │
│  config.py                all configurable values in one place        │
│  .env / .env.example      environment variable interface              │
│                                                                        │
│  Scheduling: Cloud Scheduler (production) / GitHub Actions (sandbox) │
│  Auth: Application Default Credentials (local) / SA JSON (CI/prod)   │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER — BigQuery                           │
│                                                                        │
│  Dataset: crypto_market_data (Task 2 — CoinGecko proof of concept)  │
│  Table:   coin_markets                                                │
│  Columns: 15 raw fields + 2 derived + fetched_at timestamp           │
│  Pattern: WRITE_APPEND → time-series snapshots queryable by date     │
│                                                                        │
│  Dataset: marketing_performance (Task 1 — production vision)         │
│  Tables:  paid_search_daily, paid_social_daily, organic_daily        │
│  View:    channel_summary_7d, channel_summary_30d                    │
│  Pattern: WRITE_APPEND → rolling window views query latest N days    │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                PRESENTATION LAYER — Looker Studio                     │
│                                                                        │
│  Connected: BigQuery native connector (free, zero config)            │
│  Data source: channel_summary_7d and channel_summary_30d views       │
│  Access: shared link, no login required                               │
│  Refresh: follows BigQuery connector cache (daily by default)        │
│  Read-only: no write surface exposed                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### 14.2 Data Flow Sequence

```
Step 1:  Cloud Scheduler fires at 05:00 UTC daily
Step 2:  Cloud Run Job starts pipeline.py container
Step 3:  pipeline.py calls load_config() → validates all env vars present
Step 4:  fetch_data() sends GET request to API (CoinGecko for Task 2;
         Google Ads / Meta / GA4 for production)
Step 5:  API returns JSON response
Step 6:  transform() flattens to DataFrame, coerces types, adds derived
         fields, appends fetched_at timestamp
Step 7:  load_to_bigquery() calls load_table_from_dataframe() with
         explicit schema and WRITE_APPEND disposition
Step 8:  BigQuery executes batch load job; pipeline blocks on job.result()
Step 9:  Pipeline logs row count + total table rows; exits with code 0
Step 10: Looker Studio reads from BigQuery view on next user page load
Step 11: Analyst opens dashboard URL; sees refreshed data
```

### 14.3 Technology Selection Decisions

Every technology selection in this product was made against two criteria: does it solve the problem cleanly, and does it require the team to adopt something new? If the answer to the second question is yes, the default decision is to not use it.

| Layer | Technology | Alternative Considered | Why This Was Chosen |
|---|---|---|---|
| Ingestion | Python | dbt, Fivetran, Supermetrics | Python gives full control, no vendor dependency, can be maintained by any engineer |
| Storage | BigQuery | Postgres, Redshift, Snowflake | Team already uses GCP; BigQuery has native Looker Studio connector; free sandbox for development |
| Presentation | Looker Studio | Metabase, Grafana, Tableau, custom React | Zero new tool adoption; free; native BigQuery connector; shareable link with no login |
| Scheduling | Cloud Scheduler + Cloud Run | Airflow, Prefect, cron | Fully managed, no infrastructure to maintain; native GCP auth; cost negligible at this scale |
| Auth (local) | ADC (gcloud auth application-default login) | Service account JSON file | No file to manage; uses the engineer's existing Google account; appropriate for development |
| Auth (production) | Service account JSON + IAM | Workload Identity Federation | Service account is simpler to implement for V1; WIF is the production upgrade path |

---

## 15. Data Architecture & Schema

### 15.1 Task 2 — BigQuery Table: `crypto_market_data.coin_markets`

**Write mode:** WRITE_APPEND — every pipeline run appends a snapshot with `fetched_at` as the version key.  
**Production additions (not in Sandbox V1):** Partition by `DATE(fetched_at)`, cluster by `coin_id`.

| Column | Type | Mode | Source | Analytical Purpose |
|---|---|---|---|---|
| `coin_id` | STRING | REQUIRED | API `id` | Unique identifier; used for JOIN and GROUP BY |
| `coin_name` | STRING | REQUIRED | API `name` | Human-readable label |
| `symbol` | STRING | REQUIRED | API `symbol` | Ticker; used in display and filtering |
| `market_cap_rank` | INTEGER | NULLABLE | API `market_cap_rank` | Rank by total market cap; null for unranked |
| `current_price_usd` | FLOAT64 | NULLABLE | API `current_price` | Spot price at fetch time |
| `market_cap_usd` | FLOAT64 | NULLABLE | API `market_cap` | Total market capitalisation |
| `total_volume_usd` | FLOAT64 | NULLABLE | API `total_volume` | 24h trading volume |
| `high_24h_usd` | FLOAT64 | NULLABLE | API `high_24h` | 24h highest price |
| `low_24h_usd` | FLOAT64 | NULLABLE | API `low_24h` | 24h lowest price |
| `price_change_pct_24h` | FLOAT64 | NULLABLE | API `price_change_percentage_24h` | 24h price movement |
| `price_change_pct_7d` | FLOAT64 | NULLABLE | API `price_change_percentage_7d_in_currency` | 7-day price movement |
| `circulating_supply` | FLOAT64 | NULLABLE | API `circulating_supply` | Coins in active circulation |
| `total_supply` | FLOAT64 | NULLABLE | API `total_supply` | Total coins ever; null = uncapped |
| `ath_usd` | FLOAT64 | NULLABLE | API `ath` | All-time high price |
| `ath_change_pct` | FLOAT64 | NULLABLE | API `ath_change_percentage` | % below all-time high |
| **`volume_to_market_cap_ratio`** | FLOAT64 | NULLABLE | **Derived** | `total_volume / market_cap` — liquidity signal; high ratio = actively traded relative to size |
| **`price_range_pct_24h`** | FLOAT64 | NULLABLE | **Derived** | `(high_24h - low_24h) / low_24h × 100` — intraday volatility; useful for risk profiling |
| `fetched_at` | TIMESTAMP | REQUIRED | **Pipeline** | UTC fetch time; version key for time-series queries |

**Schema design rationale:** All numeric fields are NULLABLE, not REQUIRED, because CoinGecko occasionally returns null for newly listed or delisted coins. Declaring them REQUIRED causes a load failure on any row with a null value, which would silently drop valid coins. The derived fields return NULL rather than erroring when any input is null or when the denominator is zero — this is enforced in the transform function, not left to BigQuery.

### 15.2 Production Vision — Marketing Performance Schema

This schema is not built in this assessment. It documents the intended production data model so that any engineer reading this PRD can implement it without a redesign.

**Raw tables (one per channel, daily granularity):**

```sql
-- paid_search_daily
CREATE TABLE marketing_performance.paid_search_daily (
  date              DATE        NOT NULL,
  brand_id          STRING      NOT NULL,
  campaign_id       STRING,
  clicks            INT64,
  conversions       INT64,
  spend_usd         FLOAT64,
  roas              FLOAT64,
  cpc_usd           FLOAT64,
  impressions       INT64,
  pipeline_run_id   STRING      NOT NULL,
  fetched_at        TIMESTAMP   NOT NULL
)
PARTITION BY date
CLUSTER BY brand_id;

-- paid_social_daily — identical structure, different source
-- organic_daily — identical structure; spend_usd and roas always NULL
```

**Unified summary view (what Looker Studio reads):**

```sql
CREATE VIEW marketing_performance.channel_summary_7d AS
SELECT
  'paid_search'                    AS channel,
  date,
  brand_id,
  SUM(clicks)                      AS clicks_or_sessions,
  SUM(conversions)                 AS conversions,
  SUM(spend_usd)                   AS spend_usd,
  SAFE_DIVIDE(
    SUM(revenue_usd), SUM(spend_usd)
  )                                AS roas,
  SAFE_DIVIDE(
    SUM(spend_usd), SUM(clicks)
  )                                AS cpc_usd,
  MAX(fetched_at)                  AS data_as_of
FROM marketing_performance.paid_search_daily
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY channel, date, brand_id

UNION ALL

SELECT 'paid_social' AS channel, ... -- same pattern
UNION ALL
SELECT 'organic_web' AS channel, spend_usd AS NULL, roas AS NULL, ...;
```

### 15.3 BigQuery Query Patterns

**Pattern 1 — Latest snapshot query (used in all three summary.sql queries):**
```sql
WHERE fetched_at = (SELECT MAX(fetched_at) FROM `project.dataset.table`)
```
This is the canonical way to query the most recent pipeline run on a WRITE_APPEND table.

**Pattern 2 — Time-series trend:**
```sql
SELECT DATE(fetched_at) AS run_date, AVG(metric) AS daily_avg
FROM `project.dataset.table`
GROUP BY run_date
ORDER BY run_date;
```
This becomes available automatically because of the WRITE_APPEND + `fetched_at` design.

**Pattern 3 — Staleness check (for monitoring):**
```sql
SELECT
  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(fetched_at), HOUR) AS hours_since_last_run
FROM `project.dataset.table`
HAVING hours_since_last_run > 26;
```
Returns a row only when data is stale. Used in Cloud Monitoring alerting policy.

---

## 16. Integration Specifications

### 16.1 CoinGecko API (Task 2 — Proof of Concept)

**Endpoint:** `GET https://api.coingecko.com/api/v3/coins/markets`  
**Auth:** None (free tier)  
**Rate limit:** 10–30 requests/minute — not a concern for a once-per-hour scheduled run

**Parameterised request:**
```
vs_currency     = {COINGECKO_VS_CURRENCY}   default: usd
order           = market_cap_desc            fixed
per_page        = {COINGECKO_PER_PAGE}       default: 100
page            = {COINGECKO_PAGE}           default: 1
sparkline       = false                      fixed; reduces response payload
price_change_percentage = 24h,7d            fixed; enables 24h and 7d change fields
```

**Error handling matrix:**

| Condition | HTTP Code | Pipeline Behaviour |
|---|---|---|
| Successful response | 200 + list | Log INFO row count, continue |
| Rate limit exceeded | 429 | Log ERROR with status; exit code 1; no BQ write |
| Server error | 500, 503 | Log ERROR with status and response body (≤500 chars); exit code 1 |
| Client error | 4xx | Log ERROR with status; exit code 1 |
| Network timeout | Socket timeout | Log ERROR with timeout duration; exit code 1 |
| Empty list response | 200 + `[]` | Log ERROR "empty response"; raise ValueError; exit code 1 |
| Non-list response | 200 + `{}` | Log ERROR "unexpected shape"; raise ValueError; exit code 1 |

### 16.2 Google Ads → BigQuery Export (Production)

Google Ads has a native BigQuery export at no additional cost. It is enabled in the Google Ads account under Tools → BigQuery transfers. Once enabled, Google exports daily performance data to a specified BigQuery dataset on a schedule. No custom API integration is required. The pipeline reads from this dataset rather than from the Google Ads API directly.

### 16.3 Meta Ads → BigQuery (Production)

Meta does not have a native BigQuery export. Two options exist:

**Option A — Meta Marketing API (custom connector):** The same pipeline pattern demonstrated in Task 2 can be extended to fetch from the Meta Marketing API using an access token. The transform and load pattern is identical. This adds one new pipeline function and one new env var.

**Option B — Third-party connector:** If the team already uses Supermetrics or Funnel.io, those connectors can write Meta Ads data to BigQuery directly with no custom code. The PRD is agnostic on this choice — the data model works either way.

### 16.4 GA4 → BigQuery Export (Production)

GA4 has a native BigQuery linking, also free, enabled in GA4 Admin → BigQuery linking. Once linked, GA4 exports events daily to BigQuery's `analytics_{property_id}` dataset. The pipeline creates a view on top of this export rather than moving raw data.

---

## 17. Pipeline Specification

### 17.1 Module Architecture

```
pipeline.py
│
├── load_config()
│   ├── Reads all env vars via python-dotenv
│   ├── Validates required vars are present (fail fast on missing)
│   └── Returns typed config dict — no env var access outside this function
│
├── fetch_coin_markets(config)
│   ├── Constructs URL from config base_url + endpoint
│   ├── Builds params dict from config values
│   ├── Sends GET with timeout from config
│   ├── Calls response.raise_for_status()
│   ├── Validates response is non-empty list
│   └── Returns raw list[dict]
│
├── transform(raw_data, fetched_at)
│   ├── Maps API field names to schema column names
│   ├── Creates DataFrame from mapped rows
│   ├── Coerces all numeric columns with pd.to_numeric(errors='coerce')
│   ├── Computes volume_to_market_cap_ratio (null-safe)
│   ├── Computes price_range_pct_24h (null-safe, div-by-zero safe)
│   ├── Appends fetched_at column
│   ├── Reorders columns to match BQ_SCHEMA
│   └── Returns typed DataFrame
│
├── load_to_bigquery(df, config)
│   ├── Constructs table reference from config
│   ├── Builds LoadJobConfig with BQ_SCHEMA and write disposition from config
│   ├── Calls client.load_table_from_dataframe()
│   ├── Blocks on load_job.result()
│   ├── Fetches updated row count for INFO log
│   └── Returns None; raises on failure
│
└── main()
    ├── Logs pipeline start
    ├── Calls load_config() — exits 1 on ValueError
    ├── Sets fetched_at = datetime.now(timezone.utc)
    ├── Calls fetch_coin_markets() — exits 1 on RequestException or ValueError
    ├── Calls transform() — exits 1 on Exception
    ├── Calls load_to_bigquery() — exits 1 on Exception
    └── Logs pipeline complete; exits 0
```

### 17.2 Derived Field Specifications

**Field: `volume_to_market_cap_ratio`**

Formula: `total_volume_usd / market_cap_usd`  
Type: FLOAT64, NULLABLE  
Precision: 6 decimal places  
Null conditions: returns NULL if `total_volume_usd` is NULL, `market_cap_usd` is NULL, or `market_cap_usd == 0`  
Analytical meaning: Measures trading activity relative to total market size. A ratio of 0.10 means 10% of the total market cap traded hands in 24 hours. High ratios indicate liquid, actively traded assets. Low ratios indicate illiquid or thinly traded markets. Useful for filtering out coins that have large market caps on paper but low real-world tradability.

**Field: `price_range_pct_24h`**

Formula: `(high_24h_usd - low_24h_usd) / low_24h_usd × 100`  
Type: FLOAT64, NULLABLE  
Precision: 4 decimal places  
Null conditions: returns NULL if `high_24h_usd` is NULL, `low_24h_usd` is NULL, or `low_24h_usd == 0`  
Analytical meaning: Measures the size of the 24-hour price swing as a percentage of the daily low. A value of 5.0 means the price moved 5% between its lowest and highest point in the last 24 hours. High values indicate volatile assets with large intraday price movements. Useful for volatility ranking and risk-adjusted performance analysis.

---

# Part V — Scope, Risk & Delivery

---

## 18. V1 Scope Definition

### 18.1 In Scope

**Channels:**  
Paid Search (Google Ads), Paid Social (Meta Ads), Organic Web (GA4). These three channels cover the majority of marketing spend and measurable traffic for a typical agency client. The architectural pattern for adding a fourth channel (LinkedIn, TikTok, email) is identical — a new connector, not a new architecture.

**Time windows:**  
Rolling 7-day and rolling 30-day. These answer "right now" and "this month" — the two windows the team reaches for first. Week-over-week and month-over-month comparisons are derived from these same windows without additional complexity.

**Metrics:**  
Clicks (or Sessions for organic), Conversions, Spend, ROAS (or CPC where ROAS is unconfigured). Four metrics per channel. These answer the core question. Additional metrics (impressions, CTR, CPM, frequency) add noise to a channel-level performance view.

**Scope:**  
Single client/brand. V1 validates the architecture and builds team trust with one client. Multi-tenancy is a V2 architectural decision.

**Infrastructure:**  
CoinGecko → BigQuery pipeline (Task 2) as a working proof of the ingestion pattern. This demonstrates the pipeline architecture that would underpin the marketing performance data layer in production.

### 18.2 Out of Scope — With Explicit Reasoning

| Feature | Reasoning for Exclusion |
|---|---|
| "Where to focus" AI recommendations | Correct recommendations require calibrated benchmarks, historical context, and business rules specific to each client. Calibration takes weeks. A wrong recommendation damages trust faster than no recommendation. This is a V2 feature, after 4+ weeks of V1 data validates the underlying numbers. |
| Automated alerting (spend spike, conversion drop) | Alerts require thresholds. Thresholds require a baseline. A baseline requires at least 4 weeks of clean history. Alerting before the data is trusted produces noise, not signal. V2 feature. |
| Multi-client / multi-brand views | Multi-tenancy requires row-level security policies, per-client data isolation, and an access management layer. Adding this to V1 multiplies the engineering scope by 3–5x with no marginal benefit until the single-client version is validated. V2 architecture decision. |
| Campaign-level drill-down | Channel-level data answers the stated question. Campaign-level is an analyst tool for optimisation work, not a status-check tool for answering "how is marketing performing." Adding it in V1 increases dashboard complexity and may distract from the channel-level signal. |
| Historical data beyond 30 days | Backfilling 90+ days of data from three APIs with rate limits, processing lags, and inconsistent historical schemas is a separate project. V1 builds the forward-going pipeline first. Historical backfill is V1.1, after the daily pipeline is stable. |
| Client-facing access | Clients should only see data the internal team already trusts. V1 builds that internal trust. Client-facing views require additional QA, per-brand access control, and a more polished UI. V2 concern. |
| Real-time or near-real-time data | GA4 has a 24–48 hour processing delay for some events. Google Ads conversion attribution can be delayed by 72 hours. Meta has 1–3 hour typical lag. "Real-time" cannot be delivered honestly from these sources. Daily refresh is both achievable and honest. |
| LinkedIn Ads, TikTok Ads, Email channel | Each additional channel follows the same engineering pattern as the existing three. Starting with three validates the architecture before scaling it. Each additional channel can be added in under 4 hours of work once V1 is stable. |
| Predictive forecasting | Forecasting requires a minimum of 8–12 weeks of stable historical data and a modelling decision (linear, seasonal, ML-based). V2 or later. |
| Mobile-native app | Looker Studio renders acceptably on mobile browsers. A native app is scope creep for a tool that primarily serves office-based analysts. |

---

## 19. Decision Log

This section documents every significant decision made during scoping, including the alternatives considered and the reason each alternative was rejected. This is the most important section of the PRD for understanding how the product was shaped.

---

**Decision 1: Primary user is the internal analyst, not the client.**

Options considered:
- Option A: Build for the internal analyst first (chosen)
- Option B: Build for the client first
- Option C: Build for both simultaneously

Reasoning: The problem statement describes an internal workflow problem — one analyst manually pulling data. The friction lives inside the team, not at the client interface. Building for the client first would require multi-tenancy, access control, authentication, and client-appropriate presentation before any of the underlying data infrastructure is validated. Option C doubles the scope. Option A (chosen) lets V1 solve the stated problem cleanly and builds the foundation that makes client access possible in V2.

---

**Decision 2: Tool form is Looker Studio + BigQuery, not a custom dashboard.**

Options considered:
- Option A: Looker Studio connected to BigQuery (chosen)
- Option B: Custom React dashboard reading from BigQuery via API
- Option C: Third-party analytics SaaS (Metabase, Grafana, Tableau)
- Option D: Google Sheets connected to BigQuery via Connected Sheets

Reasoning: The binding constraint is that the team will not change their tools. Looker Studio is already available to any team using Google Workspace — it requires no new subscription, no new login, and no new deployment. Option B requires frontend engineering, hosting, and maintenance that are out of scope for this product. Option C requires a new subscription and a new tool for the team to learn. Option D (Connected Sheets) was seriously considered — it has near-zero setup cost — but Looker Studio handles the date range toggle, visual layout, and sharing more cleanly for a dashboard use case.

---

**Decision 3: WRITE_APPEND with `fetched_at` timestamp over WRITE_TRUNCATE.**

Options considered:
- Option A: WRITE_APPEND (chosen)
- Option B: WRITE_TRUNCATE (replace table on each run)

Reasoning: WRITE_TRUNCATE is simpler — the table always holds the current snapshot. WRITE_APPEND turns every pipeline run into a time-stamped version. For almost no additional complexity (one timestamp column, one `MAX(fetched_at)` in every query), WRITE_APPEND unlocks time-series analysis: you can trend any metric over pipeline runs, detect data drift between runs, and backfill specific dates by filtering on `fetched_at`. The cost in query complexity is trivial. The cost in not having history is irreversible. WRITE_APPEND is the correct default for any ingestion pipeline that runs on a schedule.

---

**Decision 4: Explicit BigQuery schema definition over autodetect.**

Options considered:
- Option A: Explicit `BQ_SCHEMA` list in code (chosen)
- Option B: `autodetect=True` on LoadJobConfig

Reasoning: Autodetect fails on nullable floats (it may infer INTEGER for a column that is usually an integer but occasionally returns a float), fails inconsistently across library versions, and provides no documentation of the schema in code. An explicit schema is self-documenting, version-controlled, and produces consistent load behaviour across environments. The cost is writing the schema once. The benefit is never debugging a schema mismatch in production.

---

**Decision 5: Batch load over streaming inserts for BigQuery.**

Options considered:
- Option A: `load_table_from_dataframe` batch load (chosen)
- Option B: `insert_rows_json` streaming inserts
- Option C: `pandas_gbq.to_gbq` wrapper

Reasoning: BigQuery Sandbox does not reliably support streaming inserts without a billing account. Streaming inserts also do not respect the schema as strictly as batch loads. The `pandas_gbq` wrapper is a higher-level abstraction that obscures what is happening and has had breaking changes across versions. Batch load via `load_table_from_dataframe` is explicit, reliable in Sandbox, and the correct pattern for a pipeline that runs on a schedule rather than in real-time.

---

**Decision 6: CoinGecko as the Task 2 API over Open-Meteo or NewsAPI.**

Options considered:
- Option A: CoinGecko `/coins/markets` (chosen)
- Option B: Open-Meteo weather API
- Option C: NewsAPI headlines

Reasoning: Open-Meteo returns flat, pre-cleaned arrays. There is no meaningful transformation work to demonstrate — the data arrives ready to load. NewsAPI requires an API key (additional setup friction) and returns semi-structured text fields with limited numerical analytical depth. CoinGecko requires no API key, returns richly nested JSON with ~30 fields per coin, has natural opportunities for two distinct derived fields (liquidity ratio and volatility), and produces three genuinely different SQL aggregation queries. The data is interesting. The transformation work is real.

---

**Decision 7: GitHub Actions as the Sandbox-compatible scheduler, Cloud Scheduler + Cloud Run as the production path.**

Options considered:
- Option A: GitHub Actions scheduled workflow (Sandbox) + Cloud Scheduler + Cloud Run (production) — chosen
- Option B: Local cron job
- Option C: Apache Airflow

Reasoning: Local cron is not reproducible or team-shareable — it lives on one machine and dies with it. Airflow is significantly over-engineered for a single-table pipeline running once per day. GitHub Actions is free, version-controlled, secrets-managed via repository secrets, and produces a natural CI/CD pattern. It is not production-grade at scale (it cannot be triggered on failure, has limited observability) but it is entirely appropriate for Sandbox development and demonstrates the right architectural intent. Cloud Scheduler + Cloud Run is the production upgrade with no code changes.

---

## 20. RAID Log

### 20.1 Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | CoinGecko free tier rate limit hit during development | Medium | Low | Rate limit is 10–30 req/min; single scheduled run is 1 request. No risk at this usage level. If hit during heavy testing, add exponential backoff. |
| R-02 | BigQuery Sandbox streaming insert fails silently | High | High | Already mitigated: batch load via `load_table_from_dataframe` only. Streaming inserts never used. |
| R-03 | BigQuery autodetect schema mismatch on nullable floats | High | Medium | Already mitigated: explicit `BQ_SCHEMA` used everywhere. Autodetect never enabled. |
| R-04 | Dashboard numbers do not match source platform values | Medium | High | Metric definitions are locked before pipeline build (Section 13.2). Spot-check against platforms is required before launch. |
| R-05 | GA4 or Google Ads BigQuery export not enabled in production | Medium | High | Documented as a dependency (D-02, D-03). Pipeline pattern works regardless; the connector setup is a pre-launch checklist item. |
| R-06 | BigQuery Sandbox table expiration after 60 days | Certain | Low (for assessment) | Documented in README. Production recommendation is full GCP account with no table expiration. |
| R-07 | Team does not adopt dashboard despite availability | Medium | High | Mitigation is the rollout plan (Section 22): analyst walkthrough in week 1, team lead demo in week 2, usage tracked. |
| R-08 | Single commit at end of assessment period | Low (self-managed) | High (evaluator signal) | Enforced by commit strategy: commit at every meaningful checkpoint across all 4 days. |

### 20.2 Assumptions

| ID | Assumption | If Wrong, Impact |
|---|---|---|
| A-01 | Team uses Google Workspace (Gmail, Drive, GCP access) | If not: replace Looker Studio with Metabase self-hosted; BigQuery layer unchanged |
| A-02 | Team has or can get a billed GCP account for production | If not: pipeline runs locally or via GitHub Actions indefinitely; Sandbox limitations documented |
| A-03 | GA4 and Google Ads accounts can link to BigQuery | If not: Meta Marketing API + Google Ads API connectors replace native exports; adds ~1 week of engineering |
| A-04 | Metric definitions are consistent across clients | If not: schema needs a `metric_definition_version` field and per-brand configuration; scope increases significantly |
| A-05 | The analyst (Priya) will validate dashboard numbers against platforms in week 1 | If not: data accuracy cannot be confirmed; launch should not proceed without this check |
| A-06 | One brand/client is sufficient for V1 validation | If not: multi-tenancy becomes a V1 requirement; adds 3–5x engineering scope |

### 20.3 Issues

| ID | Issue | Status | Owner |
|---|---|---|---|
| I-01 | BigQuery Sandbox does not support table partitioning without billing | Known | Documented in README; production recommendation noted |
| I-02 | Meta Ads does not have a native BigQuery export | Known | Option A (Meta Marketing API connector) or Option B (Supermetrics) documented in Section 16.3 |
| I-03 | `price_change_percentage_7d_in_currency` field name is unusually long and may cause column name conflicts | Known | Remapped to `price_change_pct_7d` during transform |

### 20.4 Dependencies

| ID | Dependency | Type | Risk Level |
|---|---|---|---|
| D-01 | CoinGecko API availability and schema stability | External API | Low — mature, stable endpoint |
| D-02 | Google Ads account → BigQuery export enabled | Internal setup | Medium — requires account admin access |
| D-03 | GA4 property → BigQuery linking enabled | Internal setup | Low — free, widely documented |
| D-04 | Meta Ads API access token | External auth | Medium — requires Meta app review for production scopes |
| D-05 | GCP project with BigQuery enabled | Infrastructure | Low — already set up via Sandbox |
| D-06 | `google-cloud-bigquery` library v3.25.0 | Python package | Low — pinned in requirements.txt |

---

## 21. Technical Debt Register

V1 ships with known shortcuts. These are documented here rather than hidden, so that the team can plan to address them on the right timeline.

| ID | Debt Item | Category | Severity | Planned Paydown |
|---|---|---|---|---|
| TD-01 | No retry logic on API failures | Reliability | Medium | Add exponential backoff with `tenacity` library in V1.1 |
| TD-02 | No `pipeline_runs` metadata table | Observability | Medium | Add in V1.1; enables SLA monitoring without log parsing |
| TD-03 | Table not partitioned by date | Performance | Low (at current volume) | Add `PARTITION BY DATE(fetched_at)` in production (requires billed account) |
| TD-04 | Table not clustered | Performance | Low (at current volume) | Add `CLUSTER BY coin_id` alongside partitioning in production |
| TD-05 | No data quality checks post-load | Data Quality | Medium | Add row count assertion and schema validation in V1.1 |
| TD-06 | Single-threaded fetch (one API call per run) | Scalability | Low (at current volume) | Refactor to async with `httpx` when per_page × pages exceeds 500 rows |
| TD-07 | No container / Dockerfile | Portability | Low (local dev sufficient) | Add Dockerfile for Cloud Run deployment in V2 |
| TD-08 | Service account credentials managed manually | Security | Medium | Migrate to Workload Identity Federation in V2 |

---

## 22. Implementation & Rollout Plan

### 22.1 Pre-Launch Checklist

Before any team member is shown the dashboard, every item on this checklist must be confirmed:

```
Infrastructure
□ BigQuery dataset and table exist and are queryable
□ Pipeline has run successfully at least twice on schedule
□ Summary SQL queries return expected results
□ Looker Studio dashboard loads from a shared link without login

Data Quality
□ Analyst (Priya) has spot-checked dashboard numbers against 
  each source platform for one week of data
□ Numbers are within ±5% of platform-native values
□ Last-updated timestamp reflects actual pipeline run time (not page load)
□ Null values display as "—" not "0"

Access
□ Shared dashboard link tested from a Google account that has never
  accessed the Looker Studio report (simulates cold-start user)
□ Dashboard link works on both laptop and mobile browser

Documentation
□ README covers setup, run, and BigQuery approach
□ .env.example has all required variables
□ summary.sql has been run and output captured
```

### 22.2 Rollout Phases

**Phase 1 — Internal Validation (Week 1)**  
Priya reviews the dashboard alongside her manual process for one full week. She documents any discrepancies she finds (numbers that don't match, labels she doesn't understand, metrics that are missing). No other team member is introduced to the dashboard until Priya signs off on data accuracy.

**Phase 2 — Team Adoption (Weeks 2–3)**  
Arjun and any other regular recipients of performance summaries are shown the dashboard. A 15-minute walkthrough covers where to find it, what each metric means, and what "last updated" means. The goal is for at least two people to use it independently within 2 weeks.

**Phase 3 — Baseline Collection (Weeks 4–8)**  
The pipeline continues running on schedule. The team uses the dashboard as the primary answer to the performance question. At the end of week 8, there is 30+ days of clean data in BigQuery — enough to validate period-over-period comparisons and begin planning V2 features.

### 22.3 Adoption Success Signals

- Week 1: Priya confirms data accuracy; signs off to proceed
- Week 2: Arjun opens the dashboard independently before at least one client call
- Week 3: Any team member answers the performance question using the dashboard without being told to
- Week 4: No one has performed the manual 30–90 minute pull since launch

---

## 23. Production Operations

### 23.1 Scheduling

**Sandbox / Development:**  
GitHub Actions scheduled workflow with `schedule: cron('0 5 * * *')`. Runs daily at 05:00 UTC. Secrets (GCP project ID, service account JSON) stored as GitHub repository secrets. Run history and logs visible in the Actions tab.

**Production (full GCP):**  
Cloud Scheduler triggers a Cloud Run Job at `0 5 * * *` (daily 05:00 UTC). The Cloud Run Job runs the pipeline container built from the project Dockerfile. Cloud Run manages execution environment, scaling, and retries. Cloud Scheduler handles the trigger and integrates natively with GCP IAM for authentication. No servers to maintain.

### 23.2 Failure Detection (Three Layers)

**Layer 1 — Exit code monitoring:** The scheduler (Cloud Scheduler or GitHub Actions) monitors the process exit code. Exit code 1 → run marked as failed → notification dispatched via configured channel (email or Slack via Cloud Monitoring).

**Layer 2 — Log-based alerting:** In Cloud Logging, a log-based metric counts ERROR-level entries from the pipeline. A Cloud Monitoring alerting policy fires when this metric exceeds 0 in a 1-hour window. This catches failures even if the exit code is not captured correctly.

**Layer 3 — Staleness detection:** A BigQuery-based monitoring query checks whether `MAX(fetched_at)` is older than 26 hours. A Cloud Monitoring alerting policy triggers on this condition. This catches the case where the scheduler itself fails to trigger — a failure mode that exit code and log monitoring cannot detect.

```sql
-- Staleness check query (run by monitoring)
SELECT
  TIMESTAMP_DIFF(
    CURRENT_TIMESTAMP(), MAX(fetched_at), HOUR
  ) AS hours_since_last_run
FROM `project.dataset.table`
HAVING hours_since_last_run > 26;
```

### 23.3 Scale Plan — 10x Data Volume

At 10x volume (1,000 coins per run, or 10 API endpoints instead of one):

**Async fetching:** Replace `requests.get()` with `asyncio` + `httpx.AsyncClient` for concurrent calls across multiple pages or endpoints. A 10-page fetch that takes 10 seconds synchronously takes 2–3 seconds concurrently.

**Chunked BigQuery loads:** Split the DataFrame into 500-row chunks and load sequentially. Prevents memory pressure on large payloads and enables per-chunk retry logic without re-fetching all data.

**Table partitioning and clustering:** Partition by `DATE(fetched_at)` and cluster by `coin_id`. Partitioning eliminates full table scans on all time-range queries (BigQuery reads only the relevant date partition). Clustering reduces cost further by grouping related rows physically on disk.

**Pipeline metadata table:** A `pipeline_runs` table records every run's start time, end time, row count, status, and a UUID run identifier. This enables SLA reporting and drift detection without parsing logs.

**Containerised execution:** Package the pipeline in a Docker container deployed to Cloud Run. This makes the execution environment reproducible across engineers, portable between local and GCP, and horizontally scalable if parallel endpoint fetching is needed.

---

## 24. Open Questions

These questions would be resolved before a production build begins. They are documented here so that V2 planning does not need to re-discover them.

| Question | Impact if Unresolved | Who Resolves |
|---|---|---|
| Does the team use Google Workspace? | Changes presentation layer choice (Looker Studio vs Metabase) | Engineering lead confirms GCP access |
| Are GA4 and Google Ads already BigQuery-linked? | Adds 1–2 days of setup if not | Data team confirms or enables linking |
| How does the team define "conversion" per brand? | Metric definition diverges per client; schema needs `metric_definition_version` | Analyst Priya defines per brand before pipeline build |
| Is there a preference for ROAS over CPC as the primary efficiency metric? | Affects which metric gets primary visual weight on the dashboard | Team lead (Arjun) decides |
| Who owns the GCP project and billing for production? | Determines who enables the scheduled Cloud Run job | Engineering lead and finance confirm |
| Will the team use Supermetrics (if already subscribed) for Meta Ads, or build a custom connector? | Custom connector adds ~3 days of engineering; Supermetrics is plug-and-play | Engineering lead checks existing subscriptions |
| What is the acceptable latency for the dashboard from question-to-answer? | "Under 60 seconds" is the current target; if the team wants faster, caching strategy changes | Team lead confirms from actual usage |

---

## 25. Appendix

### 25.1 Glossary

| Term | Definition |
|---|---|
| ROAS | Return on Ad Spend: Revenue ÷ Ad Spend. A ROAS of 4.0 means $4 of revenue per $1 spent. |
| CPC | Cost Per Click: Ad Spend ÷ Clicks. Used when ROAS is not configured. |
| Conversion | A user action defined as a goal in the tracking platform (purchase, lead form, sign-up). Definition varies per brand and must be documented. |
| fetched_at | The UTC timestamp written to every BigQuery row by the pipeline, recording when that row's data was retrieved. It is the version key for WRITE_APPEND tables. |
| WRITE_APPEND | BigQuery write disposition that adds new rows to an existing table without deleting existing rows. Enables time-series behaviour. |
| WRITE_TRUNCATE | BigQuery write disposition that replaces all existing rows with new data. Simpler but loses history. |
| ADC | Application Default Credentials. Google's mechanism for authenticating GCP SDK calls using the engineer's logged-in Google account. No service account JSON file required. |
| BigQuery Sandbox | Google's free BigQuery tier requiring no billing account. Has limitations: no DML, 60-day table expiration, limited streaming inserts. |
| Looker Studio | Google's free data visualisation tool with a native BigQuery connector. Formerly known as Google Data Studio. Shareable via link; no login required for viewers. |
| RAID | Risks, Assumptions, Issues, Dependencies. A standard project management framework for tracking uncertainty and constraints. |
| MoSCoW | Must Have, Should Have, Could Have, Won't Have. A prioritisation framework for product requirements. |
| Derived field | A column computed from one or more API response fields during the transform step. Not returned directly by the API; adds analytical value beyond raw data. |

### 25.2 Reference Documentation

- CoinGecko API: `https://www.coingecko.com/api/documentation`
- BigQuery Sandbox: `https://cloud.google.com/bigquery/docs/sandbox`
- BigQuery Python client: `https://cloud.google.com/python/docs/reference/bigquery/latest`
- GA4 → BigQuery Export: `https://support.google.com/analytics/answer/9358801`
- Google Ads → BigQuery Export: `https://support.google.com/google-ads/answer/12835217`
- Looker Studio BigQuery Connector: `https://support.google.com/looker-studio/answer/6295012`
- Twelve-Factor App Config: `https://12factor.net/config`
- GitHub Actions Scheduled Workflows: `https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule`

### 25.3 File Manifest

Files delivered as part of this submission:

```
task-1/
├── README.md          Decision record: what was made, why, what would change with more time
├── product-brief.md   Concise product brief: tool, user, form, success definition
├── v1-scope.md        Scope document: in/out with reasoning for every exclusion
└── walkthrough.md     Written narrative: thinking process, trade-offs, what was ruled out

task-2/
├── README.md          API rationale, setup instructions, BigQuery approach, SQL output, production thinking
├── pipeline.py        Production-ready pipeline: fetch → transform → BigQuery load
├── config.py          Centralised configuration: all parameters from env vars
├── requirements.txt   Pinned dependencies
├── .env.example       Environment variable template (no real values)
├── summary.sql        Three analytical queries with captured output
└── walkthrough.md     Engineering narrative: decisions, trade-offs, what would change
```

---

*This PRD was produced as Task 1 of the Data & AI Product Engineer assessment for Tacheon x Smacient. It represents the complete product thinking and technical decision record behind ChannelPulse V1. Every scope decision has a reason. Every exclusion has a reason. Every architecture choice has a reason and an alternative that was rejected. Questions on any section can be discussed in a follow-up call.*

*Document version 1.0 — Final.*
