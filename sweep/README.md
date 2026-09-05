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

---

## Where the gate runs

`radar/prepublish_gate.py --changed --fix --strict` used to run as the **first step
of `.github/workflows/post-to-telegram.yml`**. It no longer does, and it must not be
put back there.

### The failure that moved it

The sweep gate blocks when any tier-A source has `last_swept_date != today`. The
sweep is agent-driven — nothing polls it on a schedule — so the state file only
stays fresh if the authoring run refreshes and commits it.

The last sweep was logged **31 August 2026**. From 1 September the gate therefore
failed on every push. Because it was step one, the job died before
`actions/setup-python` had even run, and **six editions — 1 Sep morning, 1 Sep
evening, 3 Sep, 4 Sep, 5 Sep morning, 5 Sep evening — were built, committed and
published to the website but never posted to Telegram.**

Nobody noticed for five days, because a dead delivery job and a quiet news day look
identical from inside the channel.

### The rule

**The gate protects what gets written. It does not decide what gets delivered.**

By the time a commit reaches `editions-src/`, the edition is already live on the
website — `build-site.yml` does not consult the gate. Blocking Telegram at that
point does not prevent publication; it just removes the audience from an edition
that shipped anyway. That is the worst of both outcomes: the reader loses the
brief, and the quality problem the gate found goes unfixed because nobody sees the
log of a workflow they were not watching.

So:

| Stage | Where | Mode |
|---|---|---|
| Sweep + gate | Authoring run, **before** the edition file is written | `--fix --strict`, **blocking** |
| Gate report | `post-to-telegram.yml` | `--changed`, **non-blocking** (`continue-on-error`) |

### What the authoring run must do, every run

```bash
python3 sweep/sweep_due.py --slot {morning|midday|evening}   # get the list
python3 sweep/sweep_due.py --log <id> --outcome found|none|blocked --url ... --note ...
python3 radar/prepublish_gate.py --changed --fix --strict    # must exit 0
```

Then commit `sweep/sweep_state.json` and `sweep/sweep_log.jsonl` **with the
edition**, in the same commit. A sweep that is not committed did not happen, because
the Actions runner checks out a fresh clone and sees only what is in git.

If the gate blocks, fix the edition or complete the sweep. Do not push and hope.

### Catching up after a missed run

`post-to-telegram.yml` has a `workflow_dispatch` with a `files` input:

- blank → posts the most recently committed edition
- `pulse-2026-09-01-morning pulse-2026-09-01-evening` → posts exactly those, in the
  order given, with `gap_seconds` between them

Post backlogs oldest-first so the channel reads chronologically.
