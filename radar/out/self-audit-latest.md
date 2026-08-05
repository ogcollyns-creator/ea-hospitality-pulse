# EA Pulse self-audit — 2026-08-05T14:28+03:00 EAT
**Health 72% · grade C** — 1 FAIL, 3 WARN, 6 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 118 tier-1 sources: 82 HEALTHY, 20 MUTE, 16 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🟢 | source staleness | PASS | No tier-1 HEALTHY source silent >14d. |
| 🟢 | radar feed freshness | PASS | 196 in-window obs; newest observation 1.3h old (2026-08-05T13:12:00+03:00). |
| 🟢 | edition cadence | PASS | 8 editions in last 2d; no slot gaps. |
| 🟡 | signal quality | WARN | 5/8 editions in last 7d were Tier 2/3 (thin). Share 62%. |
| 🟡 | ledger hygiene | WARN | 54 calls: 49 open, 5 resolved. Overdue-open: 0. Missing source_url: 18. |
| 🟢 | data freshness | PASS | All tracked data files within their freshness limits. |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 3, 5, 6, 8, 9]; confident true=28 false=4. |
| 🟢 | forecast throughput | PASS | 22 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 11 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **signal quality** (WARN): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.