# EA Pulse self-audit — 2026-08-04T13:49+03:00 EAT
**Health 60% · grade D** — 2 FAIL, 2 WARN, 5 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 117 tier-1 sources: 74 HEALTHY, 26 MUTE, 17 SILENT. Blind examples: ke-gazettes-africa, ke-tenders, ug-gazette, ug-bou, tz-gazette, tz-mnrt |
| 🟢 | source staleness | PASS | No tier-1 HEALTHY source silent >14d. |
| 🟢 | radar feed freshness | PASS | 157 in-window obs; newest observation 0.6h old (2026-08-04T13:16:00+03:00). |
| 🟢 | edition cadence | PASS | 8 editions in last 2d; no slot gaps. |
| 🔴 | signal quality | FAIL | 4/5 editions in last 7d were Tier 2/3 (thin). Share 80%. |
| 🟡 | ledger hygiene | WARN | 52 calls: 47 open, 5 resolved. Overdue-open: 0. Missing source_url: 18. |
| 🟢 | data freshness | PASS | All tracked data files within their freshness limits. |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 2, 4, 5, 6, 8]; confident true=28 false=4. |
| 🟢 | forecast throughput | PASS | 26 new falsifiable calls logged in last 7d. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **signal quality** (FAIL): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.