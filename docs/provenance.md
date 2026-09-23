# Provenance and access receipt

**Status: synthetic fixture only. No real GA4 rows were acquired or analyzed.** This is an independent portfolio project; it is not affiliated with Google and does not claim shipped experiments or commercial impact.

Official intended source: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`.

Verified on **2026-09-23** against [Google's dataset page](https://developers.google.com/analytics/bigquery/web-ecommerce-demo-dataset): coverage is **2020-11-01 through 2021-01-31**. Access requires a Google Cloud project with the BigQuery API enabled. A sandbox can support exploration without billing; query execution still requires an authenticated account and project. Google documents obfuscation, placeholders such as `<Other>`, missing values, and limited internal consistency. This sample differs from the Analytics demo account and should not be reconciled to it.

The [BigQuery sandbox documentation](https://cloud.google.com/bigquery/docs/sandbox) was checked for access requirements. Free quotas are account-dependent and can be exhausted; this project never assumes free remaining capacity. No cloud project was configured, no credentials were supplied, and no BigQuery connector or CLI was available in this session. No cloud job, byte estimate or charge was incurred. A real dry-run estimate therefore remains **unavailable**, not zero.

The [GA4 export schema](https://support.google.com/analytics/answer/7029846) documents repeated event parameters, microsecond UTC timestamps, device, first-user traffic source, and ecommerce fields. The extraction intentionally avoids newer session-attribution fields that may not exist in this historical sample. Live table metadata has **not** been verified; run the schema probe in the extraction guide before execution.

## Fixture lineage

`observatory/fixture.py` generates fabricated users with fixed random seed 20260923 and a default 1,200 users. It emulates the flattened extraction schema, includes cross-session completion, repeat visits, duplicates and missing identifiers, and is not calibrated to the real sample. Its patterns are deliberately constructed to exercise the pipeline. User IDs and transaction IDs are fabricated and never included in the public aggregate snapshot.

The exact input hash is stored in `site/data.json`, alongside the source label, window and quality ledger. The hash is a reproducibility fingerprint, not evidence of authenticity. The published snapshot includes aggregates only. Raw exports, extraction manifests with project/job identifiers, credentials, caches and local databases are ignored by Git.

## Limits on claims

Fixture rates establish that calculations run, not that a product problem exists. Even a future run on the public sample cannot establish modern business performance, causal effects, acquisition attribution at session level, lifetime customer tenure, or revenue opportunity. Query history/usage metadata was unavailable; it is not treated as zero usage.
