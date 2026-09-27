# EA Pulse self-audit — 2026-09-27T11:34+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 114 HEALTHY, 23 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 56 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa |
| 🟢 | radar feed freshness | PASS | 171 in-window obs; newest observation 4.4h old (2026-09-27T07:12:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-26 morning, 2026-09-26 midday, 2026-09-25 morning, 2026-09-25 midday, 2026-09-25 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 213 calls: 152 open, 55 resolved. Overdue-open: 0. Missing source_url: 40. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 13d>10, calendar.js 60d>21, pipeline.js 38d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 2, 3, 4, 5]; confident true=100 false=22. |
| 🟢 | forecast throughput | PASS | 16 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 1 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.