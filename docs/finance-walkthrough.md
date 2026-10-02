# Revenue, margin and forecast walkthrough

Independent portfolio extension, October 2, 2026. **Entirely synthetic commerce data.** This is not the GA4 fixture, real Google-store data, Fullscript analysis, employer work or a realized financial outcome.

## Five-minute demo

```sh
python -m pip install -r requirements-dev.txt
python -m observatory.finance
python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 --directory dist
```

Open `/finance/index.html`, or open `outputs/finance/index.html` directly. `outputs/finance/results.json` contains the executed numbers, data hash, monthly aggregates, cohort eligibility, bridge allocations, forecast selection and all rolling predictions. No cloud account or credentials are needed.

## Data and metric contract

Seed 20261002 generates 13,672 orders over January 2024–December 2025. Each order contains one item from standard or premium, one customer identifier, one date, net revenue cents, and variable cost cents. Customers enter monthly and may return; repeat behavior and purchase values are invented. After month 18, premium mix declines, price decreases and unit cost rises by construction. This intentionally challenges forecasts with a regime change.

Revenue excludes tax and deducts discounts. Contribution margin = net revenue − product cost − fulfillment cost. This is not accounting net income: acquisition spending and fixed overhead are excluded. Integer cents prevent source rounding drift; DuckDB totals independently reconcile to Python source totals.

Metric tree: **buyers × orders/buyer × net revenue/order = revenue**. Contribution margin additionally subtracts order-level variable costs. The last two complete months receive exact volume/mix/price/cost bridges. Average unit price combines list-price and discount changes; it is not a pure list-price effect.

The Shapley bridge averages each factor's contribution across all 24 orderings for margin (six for revenue). This handles interactions symmetrically and sums to the observed change. It is an accounting decomposition, **not causal attribution**. Product entry/exit is explicitly rejected because absent-product prices require an agreed counterfactual, not an arbitrary zero.

Repeat purchase = any distinct later purchase day in [first purchase + 1 day, first purchase + 90 days). All members of a first-observed calendar-month cohort need follow-up: month-end + 90 days must be at or before the exclusive cutoff. Same-day orders are not repeats. Immature cohorts show null, not zero. First-observed purchase is only acquisition in this simulated closed history; real exports often lack prior history.

## Forecast protocol and actual fixture result

Compare last-month, trailing-three-month driver means, and seasonal-naive forecasts. Use months 13–18 for validation-only selection by revenue WAPE; freeze the method; report expanding-history one-month forecasts for months 19–24. Actuals from earlier holdout months may enter later forecasts as they become available, but the method is never reselected on the holdout.

The selected method is **last month**, with **7.57% holdout revenue WAPE** on this artificial series. More elaborate drivers do not automatically win. The report also shows contribution-margin MAE, every baseline and the individual predictions. The next-month forecast uses the selected method. Scenario economics use the separately labeled three-month driver baseline: demand ±10%, AOV ±5%, fixed unit variable cost. These are business scenarios, not statistical prediction intervals.

Only six holdout origins, one artificial regime change and two years are available. No result demonstrates real business forecasting accuracy. A real implementation should add mature source history, refund reconciliation, stockouts, promotion calendars, customer identity checks, rolling evaluation across multiple regimes, forecast bias and interval calibration. Historical data must be available as of each forecast origin; current final-order totals would not solve reporting-delay leakage.

## Interview questions and decisions

1. **Why not just show revenue growth?** Higher revenue can coexist with weak contribution margin; connect price, mix and fulfillment costs to the decision.
2. **Why Shapley rather than a fixed waterfall order?** A fixed order allocates interactions arbitrarily. Averaging orderings is symmetric, but still a descriptive allocation.
3. **Why exclude late cohorts?** Immature users have less time to repeat. A denominator that silently removes only late members changes the cohort composition.
4. **Why report a simple forecast winner?** Evaluate complexity against frozen baselines, and keep the losing model visible. A synthetic error rate is an engineering demonstration, not a business performance claim.
5. **What would Finance need to approve?** Margin definition, refund lag, discount treatment, acquisition-cost scope, forecast horizon, scenario ranges and acceptable error by decision.
6. **What action follows?** Audit sources, identify which driver warrants investigation, then propose a falsifiable pricing or retention experiment. A descriptive bridge cannot establish that changing a driver will reproduce its allocated contribution.

## Evidence

Tests include a hand-solvable bridge (volume +$65, price +$30, cost −$15), independent cent reconciliation, exact 89/90-day repeat boundaries, immature cohorts, duplicate/invalid orders, missing months and a leakage test that mutates the final holdout outcome without changing selection or its forecast. Browser review checks mobile/desktop layout, source links and reported headline values.

[Forecasting: Principles and Practice — time-series cross-validation](https://otexts.com/fpp3/tscv.html) explains rolling-origin evaluation. Implementation intentionally separates selection and final evaluation as an additional portfolio discipline.

**Defensible resume wording:** Extended an independent SQL/Python analytics portfolio with reconciled synthetic order economics, exact revenue/margin driver bridges, maturity-aware repeat-purchase cohorts, and rolling-origin forecast comparisons with held-out evaluation and documented failure cases.
