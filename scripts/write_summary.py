"""Generate portfolio narrative figures from the same aggregate snapshot."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'site/data.json').read_text())
f=next(x for x in d['funnels'] if x['mode']=='session' and x['device']=='All' and x['channel']=='All')
u=next(x for x in d['funnels'] if x['mode']=='user' and x['device']=='All' and x['channel']=='All')
r=d['repeat_purchase']; e=d['experiment']; q=d['quality']
memo=f'''# Product decision memo

**Independent project · synthetic fixture · no real Google data analyzed**

**Decision:** prioritize instrumentation validation and discovery before committing to a product change. The current run proves an analytical workflow; it does not prove a business problem.

**Question:** where do users abandon an ecommerce journey, which first-observed cohorts return, and what should the product team investigate next?

**Evidence in this fixture:** the ordered same-session funnel converts {f['k']:,}/{f['n']:,} product-view sessions ({f['rate']:.1%}; user-cluster 95% interval {f['ci'][0]:.1%}–{f['ci'][1]:.1%}). The seven-day user funnel converts {u['k']:,}/{u['n']:,} mature viewers ({u['rate']:.1%}; Wilson interval {u['ci'][0]:.1%}–{u['ci'][1]:.1%}). Different units and follow-up explain why these are not interchangeable. Repeat purchase is {r['k']}/{r['n']} eligible first-observed buyers ({r['rate']:.1%}) within 28 days.

**Investigation priorities:**

1. {d['hypotheses'][0]['evidence']} Validate missing events, then investigate cost visibility and clarity at the product-to-cart transition.
2. {d['hypotheses'][1]['evidence']} Inspect device differences within acquisition groups and review performance before attributing the gap to usability.
3. {d['hypotheses'][2]['evidence']} Investigate buying cadence and post-purchase needs before designing a return incentive.

**Candidate experiment:** after real-data validation, show delivery cost and timing near add-to-cart. Randomize eligible product-viewing pseudonymous users 1:1 before exposure; persist assignment. Primary: purchase within seven days of assignment, intent to treat. Guardrails: page speed, checkout errors and revenue per assigned user, with predeclared harm margins in the experiment brief.

**Planning assumptions:** baseline {e['baseline']:.0%}, absolute MDE {e['absolute_mde']*100:.0f} pp, two-sided alpha {e['alpha']:.0%}, power {e['power']:.0%}, {e['daily_users']} eligible users/day. Approximation requires {e['per_arm']:,} users per arm. Allow {e['enrollment_days']} enrollment days plus seven outcome days, for a {e['readout_days']}-day readout. These are assumptions, not a traffic forecast. Use a fixed horizon without efficacy peeking; safety stops require a documented new analysis plan.

**Conditions for action:** acquire the authorized sample, reconcile source totals and identity quality, validate the mechanism with research, then estimate an actual eligible baseline and guardrail precision. Ship only with a beneficial primary interval, acceptable practical value and harm margins ruled out. Current recommendation: **investigate, do not ship on fixture evidence**.

**Limitations:** no causal identification; pseudonyms are not people; prior history is unavailable; incomplete cohorts are excluded; obfuscation and seasonal history constrain even a future real-data interpretation. No experiment or revenue impact is claimed.
'''
(ROOT/'docs/decision-memo.md').write_text(memo,encoding='utf-8')
# A print-ready one-page HTML companion, sharing the exact generated memo.
import html
paragraphs=memo.split('\n\n')
body=''.join('<h1>'+html.escape(p[2:])+'</h1>' if p.startswith('# ') else '<p>'+html.escape(p).replace('**','')+'</p>' for p in paragraphs if p.strip())
memo_html='<!doctype html><html lang="en"><meta charset="utf-8"><title>Product decision memo</title><style>@page{size:A4;margin:15mm}body{font:14px/1.45 system-ui;color:#152c40;max-width:800px;margin:35px auto;padding:0 20px}h1{font-size:27px;border-bottom:3px solid #1758ce;padding-bottom:12px}p{margin:12px 0;white-space:pre-line}@media print{body{font:10pt/1.35 system-ui;margin:0;padding:0;max-width:none}h1{font-size:19pt}p{margin:8pt 0}}</style>'+body+'</html>'
(ROOT/'docs/decision-memo.html').write_text(memo_html,encoding='utf-8')
findings=f'''<!-- GENERATED FINDINGS START -->
All figures below are **synthetic fixture results**, not Google-store findings. Observation window: 2020-11-01 inclusive to 2021-02-01 exclusive, UTC.

| Measure | Validated fixture result |
|---|---|
| Input → modeled events | {q['raw_rows']:,} → {q['modeled_events']:,}; event-name totals reconcile |
| Ordered session funnel | {' → '.join(format(x,',') for x in f['counts'])} |
| Session conversion | {f['k']:,}/{f['n']:,} = {f['rate']:.1%}; 95% cluster interval {f['ci'][0]:.1%}–{f['ci'][1]:.1%} |
| Seven-day user conversion | {u['k']:,}/{u['n']:,} = {u['rate']:.1%}; 95% Wilson interval {u['ci'][0]:.1%}–{u['ci'][1]:.1%} |
| 28-day repeat purchase | {r['k']}/{r['n']} = {r['rate']:.1%}; 95% Wilson interval {r['ci'][0]:.1%}–{r['ci'][1]:.1%} |
| Purchase reconciliation | {q['raw_purchases']} raw = {q['canonical_purchases']} canonical + {q['duplicate_purchases']} duplicate + {q['missing_transaction']} missing ID |
| Incomplete user follow-up | {q['immature_user_funnels']} first-view users excluded |

The largest fixture step loss is product view → cart. The recommended next action is to validate instrumentation and investigate friction, **not** to claim an opportunity's causal or revenue value. See the [one-page decision memo](docs/decision-memo.md).
<!-- GENERATED FINDINGS END -->'''
readme=ROOT/'README.md'
text=readme.read_text(encoding='utf-8')
start=text.index('<!-- GENERATED FINDINGS START -->');end=text.index('<!-- GENERATED FINDINGS END -->')+len('<!-- GENERATED FINDINGS END -->')
readme.write_text(text[:start]+findings+text[end:],encoding='utf-8')
print('Generated decision memo and README findings from site/data.json')
