# EA Pulse self-audit — 2026-08-07T09:54+03:00 EAT
**Health 67% · grade C** — 1 FAIL, 4 WARN, 5 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 118 tier-1 sources: 85 HEALTHY, 19 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🟢 | source staleness | PASS | No tier-1 HEALTHY source silent >14d. |
| 🟢 | radar feed freshness | PASS | 336 in-window obs; newest observation 2.3h old (2026-08-07T07:36:00+03:00). |
| 🟡 | edition cadence | WARN | Missing slots (last 2 full days): 2026-08-06 morning |
| 🟡 | signal quality | WARN | 7/12 editions in last 7d were Tier 2/3 (thin). Share 58%. |
| 🟡 | ledger hygiene | WARN | 58 calls: 52 open, 6 resolved. Overdue-open: 0. Missing source_url: 18. |
| 🟢 | data freshness | PASS | All tracked data files within their freshness limits. |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 5, 6, 8, 9, 10]; confident true=28 false=4. |
| 🟢 | forecast throughput | PASS | 19 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 9 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **edition cadence** (WARN): Confirm the scheduled Pulse task fired for each slot.
- **signal quality** (WARN): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.