# EA Pulse self-audit — 2026-08-17T08:05+03:00 EAT
**Health 62% · grade C** — 2 FAIL, 4 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 123 tier-1 sources: 86 HEALTHY, 23 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 38 tier-1 HEALTHY sources quiet >14d: ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 212 in-window obs; newest observation 1.8h old (2026-08-17T06:18:00+03:00). |
| 🟡 | edition cadence | WARN | Missing slots (last 2 full days): 2026-08-15 midday, 2026-08-15 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 92 calls: 72 open, 20 resolved. Overdue-open: 0. Missing source_url: 23. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 5d>4 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=53 false=6. |
| 🟢 | forecast throughput | PASS | 30 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 4 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (WARN): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.