# EA Pulse self-audit — 2026-09-18T10:37+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 146 tier-1 sources: 105 HEALTHY, 23 MUTE, 18 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 51 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa, ke-eta |
| 🟢 | radar feed freshness | PASS | 498 in-window obs; newest observation 3.3h old (2026-09-18T07:21:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-17 midday, 2026-09-16 morning, 2026-09-16 midday, 2026-09-16 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 193 calls: 141 open, 50 resolved. Overdue-open: 0. Missing source_url: 37. |
| 🟡 | data freshness | WARN | Stale/again-verify: calendar.js 51d>21, pipeline.js 29d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 2, 3, 4, 5]; confident true=99 false=21. |
| 🟢 | forecast throughput | PASS | 19 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 4 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.