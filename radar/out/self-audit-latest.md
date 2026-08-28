# EA Pulse self-audit — 2026-08-28T17:36+03:00 EAT
**Health 45% · grade D** — 3 FAIL, 5 WARN, 2 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 132 tier-1 sources: 91 HEALTHY, 25 MUTE, 16 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 51 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟡 | radar feed freshness | WARN | 103 in-window obs; newest observation 8.6h old (2026-08-28T09:01:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-08-27 morning, 2026-08-27 midday, 2026-08-26 morning, 2026-08-26 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟡 | ledger hygiene | WARN | 137 calls: 113 open, 23 resolved. Overdue-open: 0. Missing source_url: 37. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 13d>10, calendar.js 30d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=65 false=8. |
| 🟢 | forecast throughput | PASS | 29 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 7 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **radar feed freshness** (WARN): Top up with a bounded scan before the edition.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.