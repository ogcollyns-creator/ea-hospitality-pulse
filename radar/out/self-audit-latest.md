# EA Pulse self-audit — 2026-10-06T12:26+03:00 EAT
**Health 43% · grade D** — 5 FAIL, 2 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 115 HEALTHY, 22 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 63 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 268 in-window obs; newest observation 0.7h old (2026-10-06T11:42:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-10-05 morning, 2026-10-05 midday, 2026-10-04 morning, 2026-10-04 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🔴 | ledger hygiene | FAIL | 216 calls: 153 open, 57 resolved. Overdue-open: 9. Missing source_url: 40. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 22d>10, calendar.js 69d>21 |
| 🟢 | rate-index integrity | PASS | n values seen: none; confident true=0 false=0. |
| 🔴 | forecast throughput | FAIL | 0 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 3 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P050, P059, P060, P071, P110, P112, P138, P140. 
- **forecast throughput** (FAIL): No new calls in a week — the differentiator is going cold.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.