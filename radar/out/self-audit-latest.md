# EA Pulse self-audit — 2026-08-20T07:56+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 126 tier-1 sources: 88 HEALTHY, 24 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 48 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-tourism-fund |
| 🟢 | radar feed freshness | PASS | 411 in-window obs; newest observation 1.7h old (2026-08-20T06:13:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-08-19 midday, 2026-08-18 midday, 2026-08-18 evening |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 106 calls: 85 open, 21 resolved. Overdue-open: 0. Missing source_url: 23. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 8d>4, calendar.js 22d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=65 false=6. |
| 🟢 | forecast throughput | PASS | 32 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 6 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.