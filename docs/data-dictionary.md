# Data dictionary, event taxonomy and metric contract

## Extraction grain

One row per source event. Keep every event type for first-observed cohorts and visit construction. The query avoids an `UNNEST` cross join that would multiply events. Multiple matching session parameters are counted and rejected for session construction; extraction uses MAX only to produce a deterministic scalar.

| Field | Type | Treatment |
|---|---|---|
| event_date | YYYYMMDD string | Source property's reporting date; table suffix bounds extraction |
| event_timestamp | INT64 microseconds | UTC analysis clock; strictly ordered; all observation windows half-open |
| event_name | string | Original event name, including non-funnel events |
| user_pseudo_id | nullable string | Browser/device pseudonym, not a person or account |
| ga_session_id | nullable INT64 | Nested parameter, positive integer required |
| session_param_count | integer | Must equal one for session membership |
| device | nullable string | Device category; missing/placeholders → Unknown |
| acquisition_source / acquisition_medium | nullable strings | First-user traffic source, never presented as last-click session attribution |
| transaction_id | nullable string | Store-global order identity; earliest event wins |
| revenue_usd | nullable float | Ecommerce purchase revenue in USD; only canonical purchases enter deduped sum |
| revenue_local | nullable float | Local-currency ecommerce revenue; never summed across currencies |
| currency | nullable string | Event parameter; retained for audit |
| event_value | nullable float | Event parameter value; not used as a revenue substitute |

Unknown identity tokens: null, empty string, `<Other>`, `(not set)`. Missing user IDs are never merged into a shared synthetic user. Missing session IDs are never imputed. Missing transaction IDs are excluded from conversion and repeat-purchase numerators; this conservative decision may undercount true purchases.

## Event taxonomy

| Event | Business meaning | Analytical use |
|---|---|---|
| session_start | Instrumented visit start | Audit context; session identity comes from the parameter, not this event's presence |
| page_view | Page exposure | First-observed identity and session activity |
| view_item | Product-detail exposure | Funnel entry |
| add_to_cart | Cart addition | Funnel step 2 |
| begin_checkout | Checkout initiation | Funnel step 3 |
| purchase | Order completion signal | Step 4 only after valid transaction deduplication |
| Other events | Other recorded activity | Cohort/session identity; retained in count reconciliation |

## SQL model contracts

| Model | Grain / key | Key decision |
|---|---|---|
| events | Input event / event_id | Preserve rows; normalize identities; event_id is local row order, not a source identifier |
| sessions | user + session ID | Composite string key, no midnight splitting; first timestamp anchors dimensions |
| users | user pseudo ID | First and last observed event, never inferred signup |
| purchases | valid global transaction ID | Earliest timestamp wins; known revenue or identity conflicts audited |
| cohorts | user pseudo ID + Monday cohort date | Derived from first observed UTC event |

`sql/models.sql` implements all five models. Python implements sequential state traversal, follow-up eligibility and statistics. Identical non-purchase events are retained: the export does not provide a universal unique event ID and careless deduplication can erase legitimate behavior. Funnel counts are entity-level, so identical repeated stages cannot inflate them. Equal timestamps never prove stage order, including events batched with identical timestamps. Tie-breaking for duplicate purchases follows input row order; conflicting orders require review.

## Metric definitions

| Metric | Numerator | Denominator / window |
|---|---|---|
| Same-session step reach | Viewing sessions reaching all steps through that step in order | Sessions containing view_item in observed UTC window |
| Seven-day user conversion | Users completing ordered path before first view + 168 hours | Users whose first observed view has at least 168 hours of follow-up |
| Weekly return retention | Users with a different session starting in elapsed days 1–7, 8–14, 15–21 or 22–28 | All identified users in first-observed week; display only once the whole cohort has full follow-up |
| Repeat purchase | Eligible buyers with a later distinct canonical order before first purchase + 28 days | First-observed buyers with complete 28-day follow-up |
| Segment difference | Segment user conversion minus conversion of all other users | Disjoint user-level groups; 95% Newcombe interval |

All windows are UTC timestamps with inclusive start and exclusive end. Return week 1 is `[first + 1 day, first + 8 days)`, so complete week 4 requires 29 elapsed days. Repeat purchase is `(first purchase, first purchase + 28 days)` and requires 28 elapsed days. These intentionally different definitions are labeled rather than conflated.

## Acquisition grouping

`organic` → Organic search; `cpc`/`ppc`/`paidsearch` → Paid search; `email` → Email; `referral` → Referral; `(direct)` source with `(none)` or `(not set)` medium → Direct; absent/placeholder medium → Unknown; everything else → Other. This is a simplified custom grouping, **not** GA4's default channel group. Session dimensions come from first event; user funnel dimensions from first view. No retroactive attribution or multi-touch allocation.

## Uncertainty

95% Wilson score intervals for a user-level proportion; Newcombe hybrid-score intervals for a difference of independent proportions. The session funnel uses a percentile bootstrap sampling users with replacement, including all of each sampled user's eligible sessions, 500 repetitions with fixed seed. Small groups (fewer than 30 viewers in either comparison arm) remain visible but cannot set the device priority. Confidence intervals are conditional on this sample/model and do not capture obfuscation, identity error, seasonal variation or causal uncertainty. Exploratory comparisons are not adjusted for multiple testing.
