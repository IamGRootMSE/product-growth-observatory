# Product decision memo

**Independent project · synthetic fixture · no real Google data analyzed**

**Decision:** prioritize instrumentation validation and discovery before committing to a product change. The current run proves an analytical workflow; it does not prove a business problem.

**Question:** where do users abandon an ecommerce journey, which first-observed cohorts return, and what should the product team investigate next?

**Evidence in this fixture:** the ordered same-session funnel converts 323/1,708 product-view sessions (18.9%; user-cluster 95% interval 17.1%–20.6%). The seven-day user funnel converts 270/1,118 mature viewers (24.2%; Wilson interval 21.7%–26.7%). Different units and follow-up explain why these are not interchangeable. Repeat purchase is 38/277 eligible first-observed buyers (13.7%) within 28 days.

**Investigation priorities:**

1. 900 of 1,708 entrants do not reach add_to_cart in order within the same session. Validate missing events, then investigate cost visibility and clarity at the product-to-cart transition.
2. mobile: 122/542 mature viewers purchase within the ordered seven-day funnel. Inspect device differences within acquisition groups and review performance before attributing the gap to usability.
3. 38/277 eligible first-observed buyers place another distinct order within 28 days. Investigate buying cadence and post-purchase needs before designing a return incentive.

**Candidate experiment:** after real-data validation, show delivery cost and timing near add-to-cart. Randomize eligible product-viewing pseudonymous users 1:1 before exposure; persist assignment. Primary: purchase within seven days of assignment, intent to treat. Guardrails: page speed, checkout errors and revenue per assigned user, with predeclared harm margins in the experiment brief.

**Planning assumptions:** baseline 15%, absolute MDE 3 pp, two-sided alpha 5%, power 80%, 500 eligible users/day. Approximation requires 2,402 users per arm. Allow 14 enrollment days plus seven outcome days, for a 21-day readout. These are assumptions, not a traffic forecast. Use a fixed horizon without efficacy peeking; safety stops require a documented new analysis plan.

**Conditions for action:** acquire the authorized sample, reconcile source totals and identity quality, validate the mechanism with research, then estimate an actual eligible baseline and guardrail precision. Ship only with a beneficial primary interval, acceptable practical value and harm margins ruled out. Current recommendation: **investigate, do not ship on fixture evidence**.

**Limitations:** no causal identification; pseudonyms are not people; prior history is unavailable; incomplete cohorts are excluded; obfuscation and seasonal history constrain even a future real-data interpretation. No experiment or revenue impact is claimed.
