# October 2, 2026 validation

Executed on RONIN with Python 3.12.14 in a new isolated environment installed from `requirements-dev.txt`. `pip check` found no broken requirements.

- `python -m unittest discover -s tests -v`: **20 passed**, including five finance tests and all existing funnel/source-reconciliation tests.
- `python -m observatory.finance`: 13,672 synthetic orders; last-month method selected on validation; six-month holdout revenue WAPE 0.07565865692594961; latest margin change $1,393, with exact driver reconciliation.
- `python -m observatory.pipeline --fixture` and `python scripts/write_summary.py`: reproduced committed event aggregates and original narrative without a substantive snapshot diff. Real BigQuery extraction remains unexecuted.
- `python scripts/check_finance_report.py`: passed at 1440px and 390px; confirmed all monthly dollar values, headline statistics, 24 bars, mature/immature labeling, evidence links, no document overflow and no browser exceptions. Generated screenshots were visually reviewed.
- `python scripts/build.py` and `python scripts/browser_test.py`: passed all six existing routes at desktop/mobile, intersected filters, empty states, keyboard behavior, calculator arithmetic and invalid inputs, artifact HTTP checks and 200% zoom equivalent.

The new finance fixture is separate from the existing GA4-style event fixture. Neither contains real business observations. Tests demonstrate correctness on known examples, not commercial forecast accuracy. Local validation is distinct from GitHub Actions status; review the PR checks for the published commit.
