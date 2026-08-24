# EA Pulse self-audit — 2026-08-24T08:23+03:00 EAT
**Health 57% · grade D** — 3 FAIL, 3 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 131 tier-1 sources: 90 HEALTHY, 25 MUTE, 16 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 46 tier-1 HEALTHY sources quiet >14d: ke-gazettes-africa, ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-ktb-news, ke-tra, ke-tourism-fund, ke-kcaa |
| 🟢 | radar feed freshness | PASS | 356 in-window obs; newest observation 0.6h old (2026-08-24T07:47:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-08-23 morning, 2026-08-23 midday, 2026-08-22 morning, 2026-08-22 midday |
| 🟡 | signal quality | WARN | Only 0 tier-tagged editions in 7d — too few to judge. |
| 🟢 | ledger hygiene | PASS | 116 calls: 93 open, 23 resolved. Overdue-open: 0. Missing source_url: 25. |
| 🟡 | data freshness | WARN | Stale/again-verify: advisories.js 12d>4, calendar.js 26d>21 |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=64 false=8. |
| 🟢 | forecast throughput | PASS | 24 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 4 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **data freshness** (WARN): Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.