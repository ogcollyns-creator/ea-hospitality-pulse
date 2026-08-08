# EA Pulse self-audit — 2026-08-08T08:38+03:00 EAT
**Health 53% · grade D** — 2 FAIL, 4 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 118 tier-1 sources: 85 HEALTHY, 19 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🟢 | source staleness | PASS | No tier-1 HEALTHY source silent >14d. |
| 🟢 | radar feed freshness | PASS | 437 in-window obs; newest observation 0.1h old (2026-08-08T08:32:00+03:00). |
| 🟡 | edition cadence | WARN | Missing slots (last 2 full days): 2026-08-06 morning |
| 🟡 | signal quality | WARN | 10/15 editions in last 7d were Tier 2/3 (thin). Share 67%. |
| 🟡 | ledger hygiene | WARN | 58 calls: 52 open, 6 resolved. Overdue-open: 0. Missing source_url: 18. |
| 🟢 | data freshness | PASS | All tracked data files within their freshness limits. |
| 🟡 | rate-index integrity | WARN | n values seen: [1, 5, 6, 8, 9, 10]; confident true=28 false=4. |
| 🟢 | forecast throughput | PASS | 17 new falsifiable calls logged in last 7d. |
| 🔴 | published content | FAIL | 4 published claim(s) now contradicted: 2026-08-05-midday UG L3->L4; 2026-08-05-midday RW L2->L3; 2026-08-05-morning UG L4->L3; 2026-08-05-morning RW L3->L2 |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **published content** (FAIL): Publish a correction and fix advisories.js; a live edition is stating a wrong level.
- **edition cadence** (WARN): Confirm the scheduled Pulse task fired for each slot.
- **signal quality** (WARN): A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources.
- **ledger hygiene** (WARN): Backfill source_url on early calls.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.