# Primary Source Sweep

## The failure this fixes

On 28 August 2026 an audit of `radar/out/items.jsonl` found **100 of 161 registered
sources had returned nothing for seven days or more — 91 of them tier-1.** Forty-eight
froze on the same afternoon (28 July 2026, within two hours of each other) and fifteen
had *never once* returned an observation.

Among the dark: every UK FCDO advisory page, all four national gazettes, TANAPA, NCAA,
UWA, EPRA's fuel review, all four central banks, and `zn-ocgs` — Zanzibar's statistics
office.

The cost was not theoretical. On 28 August the midday edition argued Zanzibar's arrivals
growth was "running out" on the strength of a June print. Zanzibar's July figure —
**107,801 arrivals, an all-time July record** — had been published by OCGS on **14 August**,
a fortnight earlier. We missed it because `zn-ocgs` has never worked and nobody checked
by hand. That edition carries a correction.

## Diagnosis

Five tier-1 sources across three countries dying within two hours of each other is not
five site redesigns. It is one transport change. Government hosts across `.go.ke`,
`.go.tz`, `.go.ug` and `.rw` reject the crawler (403 / Incapsula) while serving search
engines freely.

**So the URLs are not wrong. The transport is.** Re-pointing a registry URL because the
crawler got a 403 corrupts first-seen history and fixes nothing. Those sources are
flagged `"transport": "agent-search"` in `radar/registry.json` precisely to stop that.

## The fix

Move them off `radar/fetcher.py` and onto the agent's search path, which demonstrably
reaches them — KNBS, EPRA, OCGS and UWA were all retrieved in four queries during the
audit.

Two principles:

1. **Diarised beats polled.** Statistical and regulatory releases land on known dates.
   You don't need change-detection for a scheduled release, you need a calendar alarm.
   Polling a monthly release three times a day is ninety wasted checks and one missed
   number.
2. **A miss is an observation.** Every check is logged with its outcome, including
   "nothing today". That is what makes a Tier 3 skip defensible rather than lazy.

## Tiers

| Tier | What | When |
|---|---|---|
| **A** (17) | Moves without warning, high consequence — advisories, outbreak bulletins, gazettes, park fee notices, KCAA circulars | **Every run** |
| **B** (12) | Diarised releases — EPRA, KNBS, CBK bulletin, OCGS, BNR, NISR, UBOS, BoU, NBS, BoT, TRI, ZRB | **When due or overdue**, per schedule |
| **C** (73) | Everything else dark | 3-day rotation, morning run |

## Use

```bash
python3 sweep/sweep_due.py --slot morning     # today's must-check list
python3 sweep/sweep_due.py --log zn-ocgs --outcome found --url ... --note "July 107,801 (+9.6%)"
python3 sweep/sweep_due.py --log ug-uwa  --outcome none
python3 sweep/sweep_due.py --log tz-nbs  --outcome blocked --note "paywalled"
python3 sweep/sweep_due.py --status
```

Outcomes: `found` (something publishable), `none` (checked, nothing new — a real
observation), `blocked` (couldn't reach it — declare as a blind spot in the edition).

## Enforcement

`radar/prepublish_gate.py` blocks publication when tier-A sources are unchecked for the
day, and warns when any source came back `blocked` so the edition declares the gap
rather than implying coverage it doesn't have. This is a machine check, not a paragraph
in a runbook — the previous version of this rule lived only in prose and was skipped for
a month.

Keep `sweep_tiers.json` schedules in sync with `calendar.js`; `calendar.js` is the
human-facing diary, `sweep_tiers.json` is the machine schedule.
