# Interview guide

## Two-minute opening

“This independent project models an ecommerce event stream into sessions, users, canonical purchases and first-observed cohorts. I distinguish same-session friction from seven-day user conversion, handle right-censoring, and connect descriptive evidence to a testable product hypothesis. This published run is a clearly marked synthetic fixture because no authorized BigQuery project was available. I included bounded extraction SQL and independent source reconciliation so the same pipeline can be run on Google's official sample.”

## Questions and defensible answers

**Did you analyze real Google users?** No. I verified official source documentation and implemented the extraction path; numerical results are from a deterministic fixture. This demonstrates analytical engineering and judgment, not a business finding. I would not recommend shipping based on these rates.

**Why not just count each event type?** Raw event counts mix repeated actions, entities and out-of-order behavior. The denominator is a viewing session or mature first-view user. A state machine ensures each successive step occurs later than the last accepted step.

**How did you construct sessions?** Positive GA session ID plus a nonmissing user pseudonym. Session IDs alone are not globally unique. I keep cross-midnight sessions together and avoid silent timeout-based imputation. Session parameters appearing multiple times are quarantined.

**What about duplicate purchase events?** Valid order ID is the global transaction key. Earliest receipt wins. Missing order IDs are separately counted and excluded from conversion; known identity/revenue conflicts are audited. This is conservative and could undercount genuine purchases.

**Does a user mean a person?** No. It is a device/browser pseudonym. Cookie loss, consent, cross-device use and obfuscation can fragment identities. There is no account stitching in this sample pipeline.

**Are cohorts new customers?** No. They are first observed inside the extract. A customer may have purchased before the observation window. Return visits use session starts derived from the first event per session, not any repeated event.

**How do you avoid unfair cohort comparison?** Every observed cohort member must have the full elapsed follow-up interval before a cell is shown. Missing maturity is displayed as unavailable, never zero retention. Comparisons still face seasonality and different acquisition mixes.

**Why not use binomial intervals for sessions?** Repeat sessions from one user are correlated. I resample users as clusters for the session conversion interval. User-level metrics have one outcome per pseudonym and use Wilson intervals. A larger real sample would merit sensitivity checks and more bootstrap repetitions.

**Can mobile underperformance be causal?** No. Product mix, intent, channel and device switching can explain it. I would inspect within-channel differences, instrumentation and performance, then randomize a defined intervention. Multiple exploratory comparisons are not confirmatory hypothesis tests.

**Why does the experiment primary metric differ from the funnel?** Intent-to-treat purchase within seven days of assignment should not depend on whether intermediate event logging changed. Eligibility and exposure occur before the treatment; conditioning on post-treatment add-to-cart would bias the estimate.

**What is the MDE?** An assumed absolute 3 percentage-point increase, from 15% to 18%, with two-sided 5% alpha and 80% power. The calculator shows how assumptions change sample size and duration. The baseline and 500 users/day are planning inputs, not fixture-derived traffic projections.

**When do you stop?** After the fixed planned sample and a minimum of two full enrollment weeks, followed by seven days for outcomes. No efficacy peeking. A safety interruption requires a documented restart/redesign rather than casually interpreting a truncated test.

**What would you improve next?** Run authorized real extraction and reconciliation; inspect actual schema and ID quality; add schema contracts for historical variants; assess equal-timestamp losses and censoring sensitivity; investigate refund/net revenue handling; estimate real experiment baseline and guardrail sample requirements. These are future work, not completed claims.

## Demonstration path

Open the funnel and explain the denominator; switch to user scope; show an immature retention cell; compare a device with its disjoint complement; change MDE in the calculator; finish with the purchase reconciliation and source disclosure.
