#!/usr/bin/env python3
"""
EA Pulse Rate Index — what to collect THIS WEEK.

The basket is 136 properties. Checking all of them every week was the job that
became unsustainable, and the evidence says most of it was wasted: 82% of bush
week-on-week readings never moved (Volcanoes 88%, Serengeti/Mara 81%, Bwindi 78%),
against 30% for city and 11% for Nairobi alone.

So cadence is now tiered by segment and ROTATED, not dropped:

    city   every 1 week    rates reprice continuously
    beach  every 2 weeks   shoulder/peak turns
    bush   every 3 weeks   seasonal rate sheets

WHY THIS IS SAFE FOR THE INDEX. build_rate_index.py compares each property only
with ITSELF and matches back up to LOOKBACK_WEEKS = 6. A 2- or 3-week cadence is
inside that window, so the chain-linked link relatives are computed exactly as
before — the index measures the same thing, just with fewer redundant reads.
The one real constraint is MIN_N = 3 matched pairs per market-week, so rotation
groups are sized to keep every market at 3+ every week. No market-week should
fall to 'unconfident' because of cadence.

    python3 rates_due.py                 # this week's list
    python3 rates_due.py --week 2026-W40 # a specific ISO week
    python3 rates_due.py --check         # verify no market drops below MIN_N
    python3 rates_due.py --stale         # properties overdue against their cadence
"""
import argparse, csv, datetime, json, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
BASKET = os.path.join(HERE, "rates", "basket.json")
OBS = os.path.join(HERE, "rates", "observations.csv")
MIN_N = 3          # must match build_rate_index.py
LOOKBACK_WEEKS = 6 # must match build_rate_index.py


def iso_week(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def week_index(tag):
    """Absolute week counter, so 'mod cadence' is stable across a year boundary."""
    y, w = int(tag[:4]), int(tag[6:])
    return y * 53 + w


def load():
    with open(BASKET, encoding="utf-8") as f:
        return json.load(f)


def due_for(market, tag):
    """Properties in `market` due in ISO week `tag`."""
    every = market.get("cadenceWeeks", 1)
    if every <= 1:
        return list(market["properties"])
    rot = market.get("rotation") or {}
    return list(rot.get(str(week_index(tag) % every), []))


def last_seen():
    """property -> most recent observed ISO week (direct channel only)."""
    seen = {}
    if not os.path.exists(OBS):
        return seen
    with open(OBS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("channel", "direct") != "direct":
                continue
            try:
                d = datetime.date.fromisoformat(r["observed_date"])
            except Exception:
                continue
            tag = iso_week(d)
            k = (r["market"], r["property"])
            if k not in seen or tag > seen[k]:
                seen[k] = tag
    return seen


def cmd_due(b, tag):
    seen = last_seen()
    total = 0
    print(f"RATE INDEX — collection due for {tag}\n" + "=" * 58)
    for key, m in b["markets"].items():
        props = due_for(m, tag)
        if not props:
            continue
        total += len(props)
        every = m.get("cadenceWeeks", 1)
        cad = "weekly" if every == 1 else f"every {every} weeks"
        print(f"\n{m['label']}  ({m['segment']}, {cad}) — {len(props)} to check")
        for p in props:
            was = seen.get((key, p))
            gap = ""
            if was:
                g = week_index(tag) - week_index(was)
                gap = f"  last seen {was} ({g}w ago)"
                if g > LOOKBACK_WEEKS:
                    gap += "  ⚠ BEYOND LOOKBACK — chain will break"
            else:
                gap = "  (never observed)"
            print(f"   • {p}{gap}")
    print("\n" + "=" * 58)
    print(f"{total} properties this week (was 136 on a full weekly sweep).")
    print("Log each with:  python3 add_rate.py <market> \"<property>\" <usd> --basis BB --type international --source \"...\"")


def cmd_check(b):
    """Every market must clear MIN_N matched pairs in every week of the cycle."""
    bad = 0
    print(f"Rotation safety check (MIN_N={MIN_N}, LOOKBACK_WEEKS={LOOKBACK_WEEKS})\n" + "=" * 58)
    for key, m in b["markets"].items():
        every = m.get("cadenceWeeks", 1)
        if every <= 1:
            print(f"  {m['label']:22} weekly, {len(m['properties']):2} props           OK")
            continue
        if every > LOOKBACK_WEEKS:
            print(f"  {m['label']:22} cadence {every}w EXCEEDS lookback {LOOKBACK_WEEKS}w  FAIL")
            bad += 1
            continue
        sizes = [len(v) for v in (m.get("rotation") or {}).values()]
        ok = sizes and min(sizes) >= MIN_N
        print(f"  {m['label']:22} every {every}w, groups {sizes}  {'OK' if ok else 'FAIL — a week drops below MIN_N'}")
        if not ok:
            bad += 1
    print("=" * 58)
    print("All markets hold a confident reading every week." if not bad
          else f"{bad} market(s) would produce an unconfident week — resize the groups.")
    return 1 if bad else 0


def cmd_stale(b, tag):
    seen = last_seen()
    rows = []
    for key, m in b["markets"].items():
        every = m.get("cadenceWeeks", 1)
        for p in m["properties"]:
            was = seen.get((key, p))
            if not was:
                rows.append((999, m["label"], p, "never observed"))
                continue
            g = week_index(tag) - week_index(was)
            if g > every:
                rows.append((g, m["label"], p, f"{g}w ago, cadence {every}w"))
    rows.sort(reverse=True)
    print(f"Overdue against cadence as at {tag}\n" + "=" * 58)
    if not rows:
        print("  Nothing overdue.")
    for g, mk, p, why in rows:
        flag = "  ⚠ beyond lookback" if g > LOOKBACK_WEEKS and g != 999 else ""
        print(f"  {mk:22} {p:38} {why}{flag}")
    print("=" * 58)
    print(f"{len(rows)} property(ies) overdue.")


def main():
    ap = argparse.ArgumentParser(description="What to collect for the EA Pulse Rate Index this week.")
    ap.add_argument("--week", help="ISO week, e.g. 2026-W40 (default: current)")
    ap.add_argument("--check", action="store_true", help="verify the rotation never drops a market below MIN_N")
    ap.add_argument("--stale", action="store_true", help="list properties overdue against their cadence")
    a = ap.parse_args()
    b = load()
    tag = a.week or iso_week(datetime.date.today())
    if a.check:
        sys.exit(cmd_check(b))
    if a.stale:
        cmd_stale(b, tag)
        return
    cmd_due(b, tag)


if __name__ == "__main__":
    main()
