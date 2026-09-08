#!/usr/bin/env python3
"""Primary Source Sweep — the must-check list for sources radar/fetcher.py cannot reach.

Why this exists
---------------
As of 28 Aug 2026, 100 of 161 registered sources (91 of them tier-1) had returned
nothing for 7+ days. The cause is not the registry — it is the HTTP layer: government
and regulator hosts across .go.ke / .go.tz / .go.ug / .rw reject the crawler's
requests (403 / Incapsula), while search engines crawl them freely.

Forcing scan.py to retry those hosts harder produces failures faster, not coverage.
So these sources move OFF the crawler and ONTO the agent's search path, which
demonstrably reaches them. This script decides what MUST be checked on a given run.

Two principles it encodes
-------------------------
1. Diarised beats polled. Statistical and regulatory releases land on known dates.
   You do not need change-detection for a scheduled release, you need a calendar
   alarm. Zanzibar's July record (OCGS, 14 Aug 2026) sat unread for a fortnight
   because nobody asked on the day it was due.
2. A miss is an observation. Every check is logged with its outcome, including
   "nothing today". That is what makes a Tier 3 skip defensible rather than lazy.

Unreachable is not an outcome. It is an escalation.
--------------------------------------------------
Added 8 Sep 2026. "blocked" used to be a free pass: one word, no evidence, and the
source silently left the day's coverage. On 8 Sep the whole sweep was skipped on
exactly that reasoning ("the sandbox cannot reach travel.state.gov"), the gate
failed, build-site died before the image steps, and the evening edition shipped
to Telegram pointing at an og: image that did not exist.

The premise was wrong. These sources are ON the agent search path precisely
BECAUSE the crawler cannot reach them. A 403 to urllib says nothing about whether
a search engine, a mirror, or the source's own PDF is reachable.

So a source may only be logged "blocked" AFTER a documented web scan:

    --outcome blocked --queries "q1 | q2" --scan-note "what came back"

with at least MIN_QUERIES distinct queries actually attempted. Logging "blocked"
without that evidence is REFUSED here, so it cannot enter state, and
prepublish_gate.py treats any undocumented blocked source as a BLOCKER rather
than a warning. Blocked WITH evidence stays publishable — as a declared blind
spot in the edition, which is the honest outcome.

Prefer "recovered": the primary host was unreachable, but the mandatory scan
found the substance elsewhere (mirror, gazette aggregator, wire copy, the PDF
itself). That is what the scan is FOR. Record the substitute URL.

Usage
-----
  python3 sweep/sweep_due.py --slot morning        # today's must-check list
  python3 sweep/sweep_due.py --log zn-ocgs --outcome found --url ... --note "..."
  python3 sweep/sweep_due.py --log ug-uwa  --outcome none
  python3 sweep/sweep_due.py --log adv-fr-kenya --outcome recovered \
        --url <mirror> --queries "a | b" --scan-note "primary 403; found via X"
  python3 sweep/sweep_due.py --log tz-bot --outcome blocked \
        --queries "a | b" --scan-note "3 queries| no dated Sep 2026 release anywhere"
  python3 sweep/sweep_due.py --assert-complete --slot evening   # HARD GATE, exit 1
  python3 sweep/sweep_due.py --status              # coverage + staleness report
"""
import json, os, sys, re, argparse, datetime
try:
    from zoneinfo import ZoneInfo; TZ = ZoneInfo("Africa/Nairobi")
except Exception:
    TZ = None

HERE  = os.path.dirname(os.path.abspath(__file__))
TIERS = os.path.join(HERE, "sweep_tiers.json")
STATE = os.path.join(HERE, "sweep_state.json")
LOG   = os.path.join(HERE, "sweep_log.jsonl")
MIN_QUERIES = 2          # a single query is a guess, not a scan
OUTCOMES = ["found", "none", "recovered", "blocked"]
MON   = ["January","February","March","April","May","June","July",
         "August","September","October","November","December"]


def now():
    return datetime.datetime.now(TZ) if TZ else datetime.datetime.now()


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def last_expected(sch, today):
    """Most recent date this source was expected to publish, or None."""
    t, y, m = sch.get("type"), today.year, today.month

    if t == "monthly_day":
        d = sch.get("day", 1)
        cur = today.replace(day=min(d, 28))
        if cur <= today:
            return cur
        pm = (today.replace(day=1) - datetime.timedelta(days=1))
        return pm.replace(day=min(d, 28))

    if t == "month_end":
        first = today.replace(day=1)
        prev_end = first - datetime.timedelta(days=1)
        this_end = (first.replace(year=y + (m == 12), month=(m % 12) + 1)
                    - datetime.timedelta(days=1))
        return this_end if this_end <= today else prev_end

    if t == "weekly_dow":
        dow = sch.get("dow", 4)                      # 0=Mon .. 6=Sun
        return today - datetime.timedelta(days=(today.weekday() - dow) % 7)

    if t in ("bimonthly_mpc", "quarterly"):
        return None                                   # handled by staleness below
    return None


def is_due(entry, st, today):
    """Return (due: bool, reason: str)."""
    sch = entry.get("schedule") or {}
    t   = sch.get("type")
    swept = st.get("last_swept_date")
    swept_d = None
    if swept:
        try:
            swept_d = datetime.date.fromisoformat(swept)
        except Exception:
            pass

    if t in ("bimonthly_mpc", "quarterly"):
        window = 55 if t == "bimonthly_mpc" else 85
        if not swept_d:
            return True, "never swept"
        age = (today - swept_d).days
        return (age >= window, f"{age}d since last sweep (window {window}d)")

    exp = last_expected(sch, today)
    if not exp:
        return True, "no schedule — sweep"
    if swept_d and swept_d >= exp:
        return False, f"covered (swept {swept_d}, expected {exp})"
    overdue = (today - exp).days
    grace = sch.get("grace", 3)
    tag = "DUE" if overdue <= grace else f"OVERDUE by {overdue - grace}d"
    return True, f"{tag} — expected {exp}"


def build(slot, today):
    tiers = load(TIERS, {}).get("entries", [])
    state = load(STATE, {})
    out = {"A": [], "B": [], "C": []}

    for e in tiers:
        st = state.get(e["id"], {})
        if e["tier"] == "A":
            out["A"].append((e, "every run"))
        elif e["tier"] == "B":
            due, why = is_due(e, st, today)
            if due:
                out["B"].append((e, why))
        else:
            out["C"].append((e, st.get("last_swept_date") or "never"))

    # Tier C rotates on a 3-day cycle; the morning run carries it.
    if slot == "morning":
        out["C"].sort(key=lambda x: (x[1] == "never" and "0" or x[1]))
        idx = today.toordinal() % 3
        out["C"] = [c for i, c in enumerate(out["C"]) if i % 3 == idx]
    else:
        out["C"] = []
    return out


def q(entry, today):
    return (entry.get("query", entry["id"])
            .replace("{MON}", MON[today.month - 1])
            .replace("{YYYY}", str(today.year)))


def _norm_queries(raw):
    """Queries are supplied pipe- or newline-separated. Dedupe, drop blanks."""
    if not raw:
        return []
    parts = [x.strip() for x in re.split(r"[|\n]+", raw)]
    seen, out = set(), []
    for x in parts:
        k = x.lower()
        if x and k not in seen:
            seen.add(k); out.append(x)
    return out


def escalation_ok(rec):
    """Has this 'blocked'/'recovered' record earned its status with a real scan?

    Backwards compatible by design: records written before 8 Sep 2026 carry no
    'queries' key. They are treated as UNDOCUMENTED, which is the honest reading
    -- we genuinely do not know whether a scan happened.
    """
    if rec.get("last_outcome") not in ("blocked", "recovered"):
        return True
    qs = rec.get("queries") or []
    return len(qs) >= MIN_QUERIES and bool((rec.get("scan_note") or "").strip())


def sweep_shortfall(slot, today):
    """What is missing before this slot may publish. Returns (hard, soft)."""
    tiers = load(TIERS, {}).get("entries", [])
    state = load(STATE, {})
    iso = today.isoformat()
    hard, soft = [], []

    for e in tiers:
        eid, tier = e["id"], e.get("tier")
        rec = state.get(eid, {})
        fresh = rec.get("last_swept_date") == iso
        if tier == "A":
            if not fresh:
                hard.append(f"{eid}: not checked today")
            elif not escalation_ok(rec):
                hard.append(f"{eid}: logged '{rec.get('last_outcome')}' with no documented web scan "
                            f"(need >={MIN_QUERIES} queries + --scan-note)")
        elif tier == "B":
            due, why = is_due(e, rec, today)
            if due and not fresh:
                soft.append(f"{eid}: diarised and due ({why}) but not checked today")
            elif fresh and not escalation_ok(rec):
                soft.append(f"{eid}: logged '{rec.get('last_outcome')}' with no documented web scan")

    declare = [i for i, v in state.items()
               if v.get("last_swept_date") == iso and v.get("last_outcome") == "blocked"]
    return hard, soft, sorted(declare)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=["morning", "midday", "evening"], default="morning")
    ap.add_argument("--log"); ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--note", default=""); ap.add_argument("--url", default="")
    ap.add_argument("--queries", default="",
                    help="Pipe-separated search queries actually attempted. Required for "
                         "--outcome blocked|recovered.")
    ap.add_argument("--scan-note", dest="scan_note", default="",
                    help="What the mandatory web scan returned. Required for blocked|recovered.")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--assert-complete", dest="assert_complete", action="store_true",
                    help="HARD GATE. Exit 1 unless every tier-A source for the slot is checked "
                         "today and every blocked/recovered source carries scan evidence.")
    a = ap.parse_args()
    today = now().date()

    if a.assert_complete:
        hard, soft, declare = sweep_shortfall(a.slot, today)
        print(f"SWEEP ASSERTION — {a.slot} — {today:%a %d %b %Y}")
        for x in soft:
            print(f"  \u26a0\ufe0f  {x}")
        if hard:
            print(f"\n\u26d4 SWEEP INCOMPLETE — {len(hard)} tier-A shortfall(s). Do NOT draft yet.")
            for x in hard:
                print(f"   - {x}")
            print("\nUnreachable is not an outcome. Run the mandatory web scan, then log:")
            print("   --outcome recovered --url <substitute> --queries \"a | b\" --scan-note \"...\"")
            print("   --outcome blocked   --queries \"a | b | c\" --scan-note \"what came back\"")
            sys.exit(1)
        print("\n\u2705 Sweep complete — every tier-A source checked today.")
        if declare:
            print("   DECLARE THESE AS A BLIND SPOT IN THE EDITION: " + ", ".join(declare))
        return

    if a.log:
        outcome = a.outcome or "none"
        queries = _norm_queries(a.queries)
        if outcome in ("blocked", "recovered"):
            # The whole point of the escalation ladder: a source is never simply
            # "unreachable". It is unreachable AFTER a scan that is on the record.
            if len(queries) < MIN_QUERIES or not a.scan_note.strip():
                print(f"\u26d4 REFUSED — cannot log '{outcome}' for {a.log} without a documented web scan.")
                print(f"   Need at least {MIN_QUERIES} distinct --queries and a --scan-note.")
                print(f"   Got {len(queries)} quer{'y' if len(queries)==1 else 'ies'} and "
                      f"{'a' if a.scan_note.strip() else 'NO'} scan note.")
                print("   These sources sit on the agent search path BECAUSE the crawler is")
                print("   blocked on them. A crawler 403 is not evidence that the story is unreachable.")
                sys.exit(2)
            if outcome == "recovered" and not a.url.strip():
                print(f"\u26d4 REFUSED — 'recovered' means the scan FOUND the substance elsewhere. "
                      f"Supply --url for the substitute source.")
                sys.exit(2)
        state = load(STATE, {})
        rec = {"last_swept_date": today.isoformat(),
               "last_outcome": outcome,
               "last_note": a.note, "last_url": a.url}
        if queries:
            rec["queries"] = queries
        if a.scan_note.strip():
            rec["scan_note"] = a.scan_note.strip()
        state[a.log] = rec
        json.dump(state, open(STATE, "w"), indent=1, sort_keys=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now().isoformat(), "id": a.log,
                                "outcome": outcome, "note": a.note, "url": a.url,
                                "queries": queries, "scan_note": a.scan_note.strip()}) + "\n")
        extra = f"  ({len(queries)} queries logged)" if queries else ""
        print(f"logged {a.log}: {outcome}{extra}")
        return

    if a.status:
        tiers = load(TIERS, {}).get("entries", []); state = load(STATE, {})
        never = [e["id"] for e in tiers if e["id"] not in state]
        print(f"sweep sources: {len(tiers)}   swept at least once: {len(tiers)-len(never)}   never: {len(never)}")
        if never:
            print("  never swept:", ", ".join(never[:18]), "..." if len(never) > 18 else "")
        return

    d = build(a.slot, today)
    total = sum(len(v) for v in d.values())
    print(f"PRIMARY SOURCE SWEEP — {a.slot} — {today:%a %d %b %Y}")
    print(f"{total} sources to check. These are NOT optional; log every one, hit or miss.\n")
    for tier, label in (("A", "TIER A — every run"),
                        ("B", "TIER B — diarised, due now"),
                        ("C", "TIER C — rotation")):
        if not d[tier]:
            continue
        print(f"{label}  ({len(d[tier])})")
        for e, why in d[tier]:
            print(f"  [{e['id']}] {e['name']}  ·  {why}")
            print(f"      search: {q(e, today)}")
        print()
    print("Log each result:  python3 sweep/sweep_due.py --log <id> --outcome found|none --note \"...\"")
    print("Unreachable? NOT a free pass — run the mandatory web scan first, then:")
    print("  --outcome recovered --url <substitute> --queries \"a | b\" --scan-note \"...\"")
    print("  --outcome blocked   --queries \"a | b\" --scan-note \"what the scan returned\"")
    print(f"\nThen assert before drafting:  python3 sweep/sweep_due.py --assert-complete --slot {a.slot}")


if __name__ == "__main__":
    main()
