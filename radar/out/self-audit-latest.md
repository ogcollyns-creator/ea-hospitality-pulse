# EA Pulse self-audit — 2026-10-14T11:03+03:00 EAT
**Health 48% · grade D** — 4 FAIL, 3 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 115 HEALTHY, 22 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 62 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kaa |
| 🟢 | radar feed freshness | PASS | 191 in-window obs; newest observation 0.8h old (2026-10-14T10:16:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-10-13 morning, 2026-10-13 midday, 2026-10-12 morning, 2026-10-12 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟡 | ledger hygiene | WARN | 229 calls: 0 open, 0 resolved. Overdue-open: 0. Missing source_url: 229. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 30d>10, calendar.js 77d>21, mice.js 21d>14 |
| 🟢 | rate-index integrity | PASS | n values seen: none; confident true=0 false=0. |
| 🔴 | forecast throughput | FAIL | 0 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 3 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **forecast throughput** (FAIL): No new calls in a week — the differentiator is going cold.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.