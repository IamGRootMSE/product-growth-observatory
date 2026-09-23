# Safe, bounded extraction

The default pipeline is offline and fixture-only. Do not enable billing or use an existing billable project without authorization. No real query has run in this project yet.

1. Use an authenticated Google account and explicitly selected Cloud project with the BigQuery API enabled. Prefer the sandbox if suitable. Verify account quotas. Do not put credential files in this repository.
2. Inspect the actual historical table schema before extracting. In BigQuery's query editor, dry-run this read-only metadata query, then run it in the authorized project:

```sql
SELECT table_name, field_path, data_type
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE table_name = 'events_20201101'
ORDER BY field_path;
```

3. Open `sql/extract_bigquery.sql`. Its wildcard scan is bounded to 20201101–20210131 and selects only needed columns. Run the query validator/dry run and record estimated bytes **before** execution. `LIMIT` would not cap scan cost. For a tiny access check, narrow both suffix bounds to one day, but do not use such an extract to make 28-day retention claims.
4. Set maximum bytes billed to **1,000,000,000 per query** initially. If the dry run exceeds that cap, stop; consciously revise the cap or dates after reviewing the estimate. Do not silently retry with a larger cap. The extraction and independent audit each have their own cap.
5. Run both bounded SQL files only after authorizing their cost. Record job IDs, query hashes, byte estimates, actual billed bytes, extract timestamp, scope and schema. Export **all** result rows as CSV with headers; avoid console preview truncation. A partial export will fail independent source count reconciliation.
6. Keep exports in ignored `data/raw/`. Do not commit them. Run the local pipeline with matching UTC boundaries, then use the source reconciliation script before publishing. Property event dates and UTC may differ at boundaries; the audit uses property-date extraction scope and is compared to the full input before the UTC filter.

## Optional Python extraction helper

Install the separately pinned `requirements-extract.txt` in your virtual environment. Authenticate using your approved Google Cloud workflow (Application Default Credentials), without pasting secrets into code or chat.

```sh
python scripts/extract.py --project YOUR_AUTHORIZED_PROJECT
# Above is dry-run only. It reports bytes, not an invented dollar estimate.
# Optional: --price-per-tib YOUR_VERIFIED_CURRENT_RATE
# Only after reviewing estimates and accepting potential charges:
python scripts/extract.py --project YOUR_AUTHORIZED_PROJECT --execute --maximum-bytes-billed 1000000000
python scripts/reconcile_source.py data/raw/events.csv data/raw/source-audit.csv
python -m observatory.pipeline --input data/raw/events.csv --start 2020-11-01 --end-exclusive 2021-02-01
python scripts/build.py
```

The helper fetches all result pages, writes CSV, and records an ignored manifest. It does not enable billing, create datasets, or export to a storage bucket. API permissions and schema must still be verified in the actual project. Its authenticated execution has not been tested here.

Before replacing the fixture site, review source reconciliation, cohort eligibility, identity loss, transaction conflicts and generated hypotheses. Change the CI fixture snapshot check and Pages build deliberately to consume a reviewed real aggregate artifact; the current Pages workflow intentionally rebuilds the fixture for safe reproducibility.
