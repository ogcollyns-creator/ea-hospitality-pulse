# EA Pulse self-audit — 2026-10-03T11:34+03:00 EAT
**Health 50% · grade D** — 4 FAIL, 2 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 114 HEALTHY, 23 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 59 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 723 in-window obs; newest observation 4.3h old (2026-10-03T07:17:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-10-02 morning, 2026-10-02 midday, 2026-10-01 morning, 2026-10-01 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🔴 | ledger hygiene | FAIL | 216 calls: 153 open, 57 resolved. Overdue-open: 8. Missing source_url: 40. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 19d>10, calendar.js 66d>21 |
| 🟢 | rate-index integrity | PASS | n values seen: none; confident true=0 false=0. |
| 🟢 | forecast throughput | PASS | 7 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 3 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P050, P059, P060, P071, P112, P138, P140, P176. 
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.