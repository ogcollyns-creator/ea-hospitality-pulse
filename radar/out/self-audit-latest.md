# EA Pulse self-audit — 2026-08-29T12:23+03:00 EAT
**Health 40% · grade D** — 4 FAIL, 4 WARN, 2 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 132 tier-1 sources: 91 HEALTHY, 25 MUTE, 16 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 49 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟡 | radar feed freshness | WARN | 495 in-window obs; newest observation 6.6h old (2026-08-29T05:45:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-08-28 morning, 2026-08-28 evening, 2026-08-27 morning, 2026-08-27 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🔴 | ledger hygiene | FAIL | 137 calls: 113 open, 23 resolved. Overdue-open: 1. Missing source_url: 37. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 14d>10, calendar.js 31d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=65 false=8. |
| 🟢 | forecast throughput | PASS | 27 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 4 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P032. Backfill source_url on early calls.
- **radar feed freshness** (WARN): Top up with a bounded scan before the edition.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.