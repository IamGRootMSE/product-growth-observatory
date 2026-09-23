# Analysis walkthrough

## Reproduce the fixture run

Use Python 3.12. Create a virtual environment, install `requirements.txt`, run `python -m observatory.pipeline --fixture`, run `python -m unittest discover -s tests -v`, and build with `python scripts/build.py`. No account or paid service is required. Fixture generation and analysis complete in seconds on a typical laptop. See the root README for complete commands.

## Follow the evidence

1. `fixture.py` creates deterministic flattened event records conforming to the extraction schema. The real alternative is `sql/extract_bigquery.sql`, which safely extracts repeated parameters without multiplying event rows.
2. `pipeline.model()` loads records into DuckDB, with typed columns. `sql/models.sql` builds events, sessions, users, purchases and cohorts. Inspect models interactively by importing `model()` and `records()` in Python.
3. `funnel_records()` removes noncanonical purchase events, groups by composite session identity or pseudonymous user, and applies a strict sequential state machine. An early checkout cannot advance a later cart event. A tied timestamp cannot demonstrate order. Cross-session continuation is allowed only in the user funnel.
4. `retention()` uses first-observed identities rather than acquisition dates or `first_visit`. A full observed cohort must mature before a weekly cell appears. Repeat purchase anchors at first observed purchase and deduplicates global order IDs.
5. `stats.py` supplies Wilson intervals, Newcombe difference intervals, a user-cluster bootstrap and the experiment sample-size approximation. Statistical intervals do not convert observational differences into causal effects.
6. `analyze()` precomputes every device/channel/scope filter combination and reconciles event-name counts. Purchase events bridge exactly to canonical, duplicate and missing-ID categories. For real extraction, `reconcile_source.py` separately checks the exported CSV against the BigQuery source audit.
7. `site/data.json` contains only aggregate measures and provenance. Every observed figure in the site comes from this file; the experiment calculator alone computes new planning scenarios from labeled inputs. The site never requests raw event data or credentials.

## Analytical choices to challenge

Why strict ordered steps? The business question is journey completion, not independent event prevalence. This may undercount real purchases when tracking misses a step. Compare canonical purchases with funnel completions rather than pretending they should match.

Why no session-ID imputation? A 30-minute timeout would create a different visit definition, especially around gaps and cross-midnight activity. Missing identifiers are an explicit quality issue. Identified events with missing sessions can still contribute to the user funnel, but not return visits.

Why both funnels? The session view finds immediate friction. The user view recognizes later completion, deduplicates repeat visitors and requires full follow-up. Their different rates cannot be interpreted as incremental lift from returning.

Why no lifetime-value claim? The history is short, seasonal, obfuscated and excludes pre-window activity. USD revenue is a deduplication audit, not a claim of net revenue, profitability, or realized impact. Refunds are not modeled into a net revenue metric.

Why rank investigations rather than predicted revenue? The data cannot identify the causal effect or implementation cost of a fix. Priority 1 uses absolute step loss, priority 2 investigates device heterogeneity, and priority 3 investigates repeat behavior. Each includes a falsifier. The real-data run must re-evaluate this ordering.
