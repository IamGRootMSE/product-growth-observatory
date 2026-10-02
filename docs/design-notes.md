# Measurement design notes

## Source and scope

All published numerical results use a deterministic synthetic fixture. Official Google sample documentation was checked and a bounded extraction path implemented, but no real Google data was queried. Fixture rates are engineering examples, not evidence for a product launch. Real extraction, schema validation and source reconciliation remain future work.

## Ordered funnels and identities

Raw event counts mix repeated actions, entities and out-of-order behavior. The denominator is a viewing session or a mature first-view user. A state machine requires each accepted stage to occur strictly later than the previous one.

Sessions use a positive GA session ID together with a nonmissing user pseudonym; a session ID alone is not globally unique. Cross-midnight sessions remain together, repeated session parameters are quarantined and no timeout-based identity imputation occurs. A pseudonym is not a person: cookie loss, consent, devices and obfuscation can fragment identities. No account stitching is attempted.

## Purchase reconciliation

Valid order ID is the global transaction key; earliest receipt wins. Missing order IDs are counted separately and excluded from conversion. Identity and revenue conflicts are audited. This conservative policy can undercount genuine purchases. Refund and net-revenue handling need further source-specific validation.

## Cohort maturity

Cohorts are first observed within the extract, not necessarily new customers. Prior purchases may be outside the window. Return visits use session starts, not arbitrary repeated events. Every cohort member must have complete elapsed follow-up before a cell is reported. Immaturity is unavailable, never zero. Seasonality and acquisition-mix differences remain limitations.

## Uncertainty and interpretation

Repeated sessions within a user are correlated, so session intervals resample user clusters. User-level metrics use Wilson intervals. A larger real sample would warrant more bootstrap repetitions and sensitivity analysis. Device differences are descriptive: product mix, intent, acquisition channel and switching can confound them. Multiple exploratory comparisons are not confirmatory tests.

## Experiment planning

The proposed primary metric is intention-to-treat purchase within seven days of assignment, independent of intermediate event logging. Conditioning on post-treatment add-to-cart would bias the estimate. The calculator assumes an absolute MDE of three percentage points (15% to 18%), two-sided 5% alpha and 80% power. The baseline and 500 users/day are hypothetical planning inputs, not fixture traffic projections.

The stopping rule uses a fixed planned sample, at least two enrollment weeks and seven additional outcome days. No efficacy peeking is supported. Safety interruptions require a documented redesign rather than an ordinary interpretation of a truncated test. Real baseline and guardrail variance estimates, historical schema contracts, equal-timestamp loss and censoring sensitivity remain validation needs.
