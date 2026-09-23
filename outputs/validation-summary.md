# Validation receipt

Run date: 2026-09-23. Source: **synthetic fixture only**.

| Check | Result |
|---|---|
| Python analytical tests | 15 passed |
| Fixture events reconciled | 7,165 input = 7,165 modeled; every event-name count matches |
| Purchase bridge | 483 raw = 440 canonical + 39 duplicate + 4 missing transaction ID |
| User follow-up exclusion | 82 immature first-view users excluded |
| Static build | Passed; precomputed JSON, HTML, CSS and JS |
| JavaScript syntax | Node syntax check passed |
| Desktop/mobile routes | Six routes each at 1440px and 390px; no document overflow |
| Interactive controls | Device/channel intersection, scope, empty state and calculator passed |
| Accessibility checks | Semantic labels and tables, keyboard focus, visible focus styles, enlarged-text overflow check; not a formal WCAG audit |
| Browser console | No page errors |
| Local links | Supporting artifact links return HTTP 200 |
| Visual inspection | Desktop/mobile overview, desktop retention, mobile experiment reviewed from screenshots |
| Decision memo | PDF verified as one A4 page; rendered and visually inspected |
| Real BigQuery queries | Not executed: no authorized project/credentials/connector |
| Independent source reconciliation | Tested with handcrafted inputs, not executed against BigQuery |
| GitHub push | Blocked: no usable Git credentials; integration denied repository writes with HTTP 403 |
| GitHub CI / Pages | Workflows implemented; not run remotely because push is blocked |

`browser-validation.json` contains the automated UI check receipt. Screenshots are in `outputs/screenshots/`. This receipt does not claim causal validity or real business impact.
