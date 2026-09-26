# EA Pulse self-audit — 2026-09-26T11:00+03:00 EAT
**Health 47% · grade D** — 4 FAIL, 3 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 153 tier-1 sources: 112 HEALTHY, 23 MUTE, 18 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 56 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa |
| 🟢 | radar feed freshness | PASS | 377 in-window obs; newest observation 4.0h old (2026-09-26T07:00:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-25 morning, 2026-09-25 midday, 2026-09-25 evening, 2026-09-24 morning, 2026-09-24 midday, 2026-09-24 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🔴 | ledger hygiene | FAIL | 209 calls: 154 open, 50 resolved. Overdue-open: 1. Missing source_url: 37. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 12d>10, calendar.js 59d>21, pipeline.js 37d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 2, 3, 4, 5]; confident true=100 false=22. |
| 🟢 | forecast throughput | PASS | 15 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 1 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P017. 
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.