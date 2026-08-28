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

Usage
-----
  python3 sweep/sweep_due.py --slot morning        # today's must-check list
  python3 sweep/sweep_due.py --log zn-ocgs --outcome found --url ... --note "..."
  python3 sweep/sweep_due.py --log ug-uwa  --outcome none
  python3 sweep/sweep_due.py --status              # coverage + staleness report
"""
import json, os, sys, argparse, datetime
try:
    from zoneinfo import ZoneInfo; TZ = ZoneInfo("Africa/Nairobi")
except Exception:
    TZ = None

HERE  = os.path.dirname(os.path.abspath(__file__))
TIERS = os.path.join(HERE, "sweep_tiers.json")
STATE = os.path.join(HERE, "sweep_state.json")
LOG   = os.path.join(HERE, "sweep_log.jsonl")
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", choices=["morning", "midday", "evening"], default="morning")
    ap.add_argument("--log"); ap.add_argument("--outcome", choices=["found", "none", "blocked"])
    ap.add_argument("--note", default=""); ap.add_argument("--url", default="")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    today = now().date()

    if a.log:
        state = load(STATE, {})
        state[a.log] = {"last_swept_date": today.isoformat(),
                        "last_outcome": a.outcome or "none",
                        "last_note": a.note, "last_url": a.url}
        json.dump(state, open(STATE, "w"), indent=1, sort_keys=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now().isoformat(), "id": a.log,
                                "outcome": a.outcome or "none",
                                "note": a.note, "url": a.url}) + "\n")
        print(f"logged {a.log}: {a.outcome}")
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
    print("Log each result:  python3 sweep/sweep_due.py --log <id> --outcome found|none|blocked --note \"...\"")


if __name__ == "__main__":
    main()
