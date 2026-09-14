# EA Pulse self-audit — 2026-09-14T11:07+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 141 tier-1 sources: 102 HEALTHY, 21 MUTE, 18 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 50 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa, ke-eta |
| 🟢 | radar feed freshness | PASS | 152 in-window obs; newest observation 4.3h old (2026-09-14T06:52:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-13 morning, 2026-09-13 midday, 2026-09-12 morning, 2026-09-12 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 179 calls: 132 open, 46 resolved. Overdue-open: 0. Missing source_url: 37. |
| 🟡 | data freshness | WARN | Stale/again-verify: calendar.js 47d>21, pipeline.js 25d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 2, 3, 4, 5]; confident true=92 false=16. |
| 🟢 | forecast throughput | PASS | 19 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 3 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.