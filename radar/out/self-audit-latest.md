# EA Pulse self-audit — 2026-08-12T08:33+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 118 tier-1 sources: 85 HEALTHY, 19 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 40 tier-1 HEALTHY sources quiet >14d: ke-knbs-releases, ke-knbs-calendar, ke-cbk-press, ke-cbk-bulletin, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra |
| 🟢 | radar feed freshness | PASS | 357 in-window obs; newest observation 5.4h old (2026-08-12T03:09:00+03:00). |
| 🟢 | edition cadence | PASS | 7 editions in last 2d; no slot gaps. |
| 🟡 | signal quality | WARN | 7/10 editions in last 7d were Tier 2/3 (thin). Share 70%. |
| 🔴 | ledger hygiene | FAIL | 71 calls: 63 open, 8 resolved. Overdue-open: 1. Missing source_url: 18. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 8d>4, costs.js 14d>10 |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 3, 4, 5, 6, 7]; confident true=53 false=6. |
| 🟢 | forecast throughput | PASS | 19 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 9 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P057. Backfill source_url on early calls.
- **signal quality** (WARN): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.