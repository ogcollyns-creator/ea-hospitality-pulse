# EA Pulse self-audit — 2026-08-13T09:17+03:00 EAT
**Health 50% · grade D** — 3 FAIL, 4 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 120 tier-1 sources: 85 HEALTHY, 21 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 37 tier-1 HEALTHY sources quiet >14d: ke-knbs-releases, ke-knbs-calendar, ke-cbk-bulletin, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 516 in-window obs; newest observation 0.4h old (2026-08-13T08:52:00+03:00). |
| 🟡 | edition cadence | WARN | Missing slots (last 2 full days): 2026-08-12 evening |
| 🔴 | signal quality | FAIL | 6/7 editions in last 7d were Tier 2/3 (thin). Share 86%. |
| 🟡 | ledger hygiene | WARN | 74 calls: 62 open, 12 resolved. Overdue-open: 0. Missing source_url: 20. |
| 🟡 | data freshness | WARN | Stale/again-verify: costs.js 15d>10 |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 3, 4, 5, 6, 7]; confident true=53 false=6. |
| 🟢 | forecast throughput | PASS | 18 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 8 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **signal quality** (FAIL): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **edition cadence** (WARN): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.