# EA Pulse self-audit — 2026-09-09T10:34+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 135 tier-1 sources: 97 HEALTHY, 21 MUTE, 17 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 48 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa, ke-eta, ke-treasury |
| 🟢 | radar feed freshness | PASS | 358 in-window obs; newest observation 4.0h old (2026-09-09T06:36:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-08 midday, 2026-09-07 morning, 2026-09-07 midday, 2026-09-07 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 166 calls: 136 open, 29 resolved. Overdue-open: 0. Missing source_url: 39. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 25d>10, calendar.js 42d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 2, 3, 4, 5]; confident true=92 false=16. |
| 🟢 | forecast throughput | PASS | 21 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 3 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.