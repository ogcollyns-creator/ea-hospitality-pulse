# EA Pulse self-audit — 2026-09-30T12:02+03:00 EAT
**Health 60% · grade C** — 3 FAIL, 2 WARN, 5 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 114 HEALTHY, 23 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 59 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 650 in-window obs; newest observation 4.5h old (2026-09-30T07:32:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-09-29 morning, 2026-09-29 midday, 2026-09-29 evening, 2026-09-28 morning, 2026-09-28 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 216 calls: 153 open, 57 resolved. Overdue-open: 0. Missing source_url: 40. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 16d>10, calendar.js 63d>21 |
| 🟢 | rate-index integrity | PASS | n values seen: none; confident true=0 false=0. |
| 🟢 | forecast throughput | PASS | 9 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 2 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.