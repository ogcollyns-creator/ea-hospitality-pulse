# EA Pulse self-audit — 2026-08-11T08:37+03:00 EAT
**Health 52% · grade D** — 2 FAIL, 5 WARN, 3 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 118 tier-1 sources: 85 HEALTHY, 19 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🟢 | source staleness | PASS | No tier-1 HEALTHY source silent >14d. |
| 🟡 | radar feed freshness | WARN | 0 obs in window but no first-seen stamps parsed. |
| 🟡 | edition cadence | WARN | Missing slots (last 2 full days): 2026-08-09 midday |
| 🟡 | signal quality | WARN | 8/13 editions in last 7d were Tier 2/3 (thin). Share 62%. |
| 🔴 | ledger hygiene | FAIL | 66 calls: 59 open, 7 resolved. Overdue-open: 1. Missing source_url: 18. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 7d>4, costs.js 13d>10 |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 3, 4, 5, 6, 7]; confident true=53 false=6. |
| 🟢 | forecast throughput | PASS | 16 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 8 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P030. Backfill source_url on early calls.
- **edition cadence** (WARN): Confirm the scheduled Pulse task fired for each slot.
- **signal quality** (WARN): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.