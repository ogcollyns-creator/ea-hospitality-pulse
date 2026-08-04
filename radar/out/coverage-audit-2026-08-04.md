# Radar source-coverage audit — 4 August 2026

**Trigger.** On 4 Aug the midday Pulse was led by a US Embassy Nairobi dengue
health alert published 3 Aug. The radar never surfaced it; it was caught by a
manual coast scan. This audit asks how many other sources share the same failure.

## Root cause of the miss
`ke-usembassy-alerts` is correctly registered (tier 1, all slots, 120-min
cadence). But its alerts index isn't parseable into headline anchors from the
server HTML, so `scan_html` falls to its **whole-page-hash fallback** and emits a
contentless `"[page changed]"` observation — `published_ts: null`, no headline,
no link to the alert. That observation scores near the bottom and never reached
`candidates.md`. The source had also produced nothing usable since 29 July.

## Method
No network needed. Every source is classified purely on ledger evidence
(`radar/out/items.jsonl`), which is the correct signal anyway:
- **HEALTHY** — has produced parsed `item`/`doc` rows.
- **MUTE** — has produced ONLY `page-change` rows (the blind fallback).
- **SILENT** — zero rows ever. *(Treat with some caution: the local ledger is a
  restore export; a genuinely live-only source can read SILENT here. MUTE is
  unambiguous.)*

Reproduce: `python3 radar/audit_sources.py --stale-days 14`

## Result — 150 sources: 99 HEALTHY, 30 MUTE, 21 SILENT
The blind set is not random noise — it is disproportionately the high-value
upstream sources the whole "break it first" thesis depends on.

**Tier-1 MUTE (26)** — only page-change noise, never parsed:
`ke-usembassy-alerts`, `us-fedreg-cdc`, `who-don` (WHO Disease Outbreak News),
gazettes (`ke-gazettes-africa`, `ug-gazette`, `tz-gazette`, `rw-gazette`),
central banks (`ug-bou`, `rw-bnr`), `tz-tanapa` (parks), `tz-immigration`
(entry-rules), `zn-moh` (health), airlines (`air-ug`, `air-tc`, `air-jambojet`,
`air-precision`, `air-airlink`), hotel groups (`dev-marriott`, `dev-kempinski`),
`rw-visitrwanda`, `sm-wttc`, `ug-mediacentre`, `ke-tenders`, `tz-tenders`,
`tz-mnrt`, `zn-zrb`.

**Tier-1 SILENT (17)** — no rows at all, verify on the runner first:
every US advisory page source (`adv-us-kenya/uganda/tanzania/rwanda`),
`cdc-travel-notices`, `osac-kenya`, `ke-epra-press`, `ke-epra-fuel` (the fuel
review!), `ug-ucaa`, `ug-moh`, `zn-ocgs`, `zn-tourism`, `ke-kaa-tenders`,
`air-tk`, `sm-unwto`, `adv-au-kenya`, `adv-au-tanzania`.

## Fixes
1. **Shipped now (code, tested offline):** a tier-1 source in a must-open
   category (`advisory, health, gazette, entry-rules, aviation, central-bank,
   parks, regulator, ministry, airline`) that lands in the page-change fallback
   is now given an **`OPEN THIS`** verdict that floats to the TOP of
   `candidates.md`, regardless of numeric score. Unit-tested in
   `radar/tests/test_assign_verdict.py` (8/8). This alone would have caught the
   dengue miss: a triager would have seen "OPEN THIS — tier-1 advisory page
   moved" at the top and opened the page.
2. **Shipped now (tooling):** `radar/audit_sources.py` — run it after each scan
   so a blind tier-1 source is a visible finding, not a silent gap.
3. **Needs runner validation (not done from sandbox — proxy 403s all hosts):**
   per-source remediation for the 26 MUTE + 17 SILENT tier-1 sources — prefer an
   RSS/feed URL where one exists (WordPress `/feed/`, govdelivery for the US
   embassy/State pages), else a `frag` selector to isolate the notice list, else
   flag as JS-rendered and needing a headless fetch. This is the follow-up work.
