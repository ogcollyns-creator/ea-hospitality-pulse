# EA Pulse self-audit — 2026-08-15T08:39+03:00 EAT
**Health 50% · grade D** — 4 FAIL, 2 WARN, 4 PASS

| | Check | Status | Detail |
|-|-|-|-|
| 🔴 | source coverage | FAIL | 120 tier-1 sources: 85 HEALTHY, 21 MUTE, 14 SILENT. Blind examples: ke-tenders, ug-bou, tz-mnrt, tz-tanapa, tz-immigration, tz-tenders |
| 🔴 | source staleness | FAIL | 37 tier-1 HEALTHY sources quiet >14d: ke-knbs-releases, ke-knbs-calendar, ke-tri, ke-tourism-ministry, ke-ktb-news, ke-tra, ke-kcaa, ke-kaa |
| 🟢 | radar feed freshness | PASS | 421 in-window obs; newest observation 0.7h old (2026-08-15T07:55:00+03:00). |
| 🔴 | edition cadence | FAIL | Missing slots (last 2 full days): 2026-08-14 morning, 2026-08-14 midday, 2026-08-14 evening, 2026-08-13 evening |
| 🟡 | signal quality | WARN | Only 2 tier-tagged editions in 7d — too few to judge. |
| 🔴 | ledger hygiene | FAIL | 81 calls: 67 open, 14 resolved. Overdue-open: 3. Missing source_url: 20. |
| 🟢 | data freshness | PASS | All tracked data files within their freshness limits. |
| 🟡 | rate-index integrity | WARN | n values seen: [0, 1, 3, 4, 5, 6]; confident true=53 false=6. |
| 🟢 | forecast throughput | PASS | 23 new falsifiable calls logged in last 7d. |
| 🟢 | published content | PASS | 5 recent editions; no advisory claim contradicts the board. |

## Actions
- **source coverage** (FAIL): Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner.
- **source staleness** (FAIL): Confirm the source still publishes; fix URL if it moved.
- **edition cadence** (FAIL): Confirm the scheduled Pulse task fired for each slot.
- **ledger hygiene** (FAIL): Resolve overdue calls now: P044, P047, P056. 
- **rate-index integrity** (WARN): Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.