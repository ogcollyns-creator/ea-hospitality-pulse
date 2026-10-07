# EA Pulse self-audit — 2026-10-07T12:22+03:00 EAT
**Health 48% · grade D** — 4 FAIL, 3 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 156 tier-1 sources: 115 HEALTHY, 22 MUTE, 19 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 68 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-cbk-press, ke-cbk-bulletin, ke-tri, ke-ktb-news, ke-tra |
| 🟢 | radar feed freshness | PASS | 836 in-window obs; newest observation 4.5h old (2026-10-07T07:50:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-10-06 morning, 2026-10-06 midday, 2026-10-05 morning, 2026-10-05 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟡 | ledger hygiene | WARN | 218 calls: 0 open, 0 resolved. Overdue-open: 0. Missing source_url: 218. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 5d>4, costs.js 23d>10, calendar.js 70d>21 |
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