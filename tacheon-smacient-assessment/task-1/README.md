# Task 1: Product Scoping — README

**Product:** ChannelPulse — Internal Marketing Performance Dashboard  
**Author:** Irfhan Ahamed  
**Assessment:** Data & AI Product Engineer — Tacheon x Smacient  

---

## What I Decided and Why

**Primary user: the internal analyst, not the client.**

The problem as described is an internal workflow problem. One person on the team is spending 30–90 minutes manually stitching data from three platforms every time the performance question comes up. That friction lives inside the team, not at the client interface. Scoping V1 for the client would have required solving authentication, multi-brand data isolation, and client-appropriate presentation before validating that the underlying data layer is trustworthy. That is a V2 problem set. V1 eliminates the internal manual work. Once the internal team trusts the numbers, client access becomes a sharing permission, not an architecture rebuild.

**Tool form: Looker Studio dashboard connected to a BigQuery view.**

The binding constraint — the team will not change their existing tools — immediately pointed toward the Google ecosystem. If the team uses Google Workspace (which a BigQuery-heavy firm almost certainly does), Looker Studio is already available at no additional cost. No new login, no new subscription, no onboarding. The dashboard is a URL. This constraint ruled out every SaaS analytics platform and every custom-built dashboard option simultaneously.

**Three channels in V1: Paid Search, Paid Social, Organic Web.**

These three account for the majority of measurable marketing spend and traffic for agency clients running standard campaigns. Each additional channel (LinkedIn, TikTok, email) follows the identical engineering pattern — a new connector, not a new architecture. Starting with three means V1 ships and gets validated before the scope grows.

**Four metrics per channel: Clicks or Sessions, Conversions, Spend, ROAS or CPC.**

These four answer the core question. Impressions, CTR, CPM, and frequency were explicitly excluded — they describe reach and attention, not outcomes, and they add noise to a channel-level status check. If an analyst needs impressions data, they can open the platform directly. The dashboard should not try to be the platform.

**Rolling 7-day and 30-day windows only.**

These answer "right now" and "this month." Calendar-week and calendar-month views are better for formatted reporting (nicer-looking numbers that align with invoice periods) but rolling windows are better for operational decisions. V1 is an operational tool.

**Platform-native metric definitions, not normalized cross-channel metrics.**

Google Ads and Meta Ads use different default attribution models. Google defaults to data-driven attribution; Meta defaults to a 7-day click plus 1-day view window. If the pipeline ingests conversions from both platforms without standardizing the attribution window, the "Conversions" column across channels is not a direct apples-to-apples comparison. V1 uses platform-native definitions — this is faster to build and easier to audit ("does this match what I see in Google Ads?"), but it requires the analyst to understand that cross-channel conversion comparisons carry an implicit caveat. This is documented as an open question rather than a V1 design decision.

---

## What I Would Revisit With More Time

**Attribution window standardisation.** The V1 dashboard shows platform-native conversions, which means Paid Search and Paid Social conversions are not directly comparable without a caveat. A V1.1 decision is whether to document the difference prominently in the dashboard UI, or to standardize both channels to a single attribution window (typically last-click) before the pipeline loads the data. The right answer depends on the clients' reporting requirements — it cannot be made without that context.

**Meta conversion finalization lag.** Meta finalizes some conversion metrics up to 48 hours after the event. A pipeline running daily at 06:00 UTC will load yesterday's Meta data before some conversions are finalized. This means yesterday's Paid Social conversion count may increase by today's run. A more robust approach is to load Meta data with a 48-hour offset — displaying data from two days ago as "final" rather than yesterday as "preliminary." The last-updated timestamp partially addresses the trust problem, but not the accuracy problem.

**Period-over-period comparison.** I listed this as Should Have rather than Must Have because it requires two complete periods of clean pipeline history before it displays a meaningful delta. On day one, there is no prior period. Displaying a delta against an empty baseline would either error silently or show a misleading zero. I would include this in V1.1 after the first full week of pipeline data is confirmed clean.

**Stale data indicator.** If the pipeline has not run in more than 26 hours, the dashboard should surface a visible warning. This is technically trivial (a conditional formatting rule against `MAX(fetched_at)`), but it requires defining what "stale" looks like in practice — which requires the pipeline to run for at least a week before the threshold is meaningful.

---

## Key Trade-offs I Made

**Simplicity over completeness.** V1 shows three channels and four metrics. There are dozens of metrics available across these three platforms. I chose the four that answer the stated question. The remaining metrics can be added without architectural change — they are additive columns, not redesigns.

**Internal trust over client access.** V1 is not client-facing. This delays a feature that could generate visible value for clients in order to build the data quality foundation that makes that feature credible when it ships. Wrong numbers sent to a client early cause more damage than a delayed self-service feature.

**Daily refresh over real-time.** GA4, Google Ads, and Meta all have processing lags of 24–72 hours for certain metrics. "Real-time" is not achievable from these sources without significant engineering complexity and the risk of showing preliminary numbers as final. Daily refresh is both achievable and honest. The last-updated timestamp is the transparency mechanism.

---

## What I Explicitly Ruled Out

Every V1 exclusion is in `v1-scope.md` with explicit reasoning. The organizing principle: anything that requires the data to be trusted before it can be implemented — recommendations, automated alerting, client access — was excluded in favour of building the data layer and validating it internally first. You cannot recommend on data that has not been verified. You cannot alert on thresholds that have not been calibrated.