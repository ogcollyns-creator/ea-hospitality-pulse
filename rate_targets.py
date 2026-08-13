#!/usr/bin/env python3
"""
Which properties should today's rate sweep chase?

Daily collection is only useful if it spreads across the basket rather than
re-observing the same easy properties. This ranks the basket by staleness and prints
the N most overdue, so a daily run covers the whole basket roughly weekly while
keeping every property's series evenly spaced.

Matched-sample chaining needs each property observed at least twice within the
LOOKBACK window, so evenness matters more than volume.

  python3 rate_targets.py [N]        # default 8
"""
import os, sys, csv, json, datetime
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8

basket = json.load(open(os.path.join(RD, "basket.json"), encoding="utf-8"))
last = {}
counts = defaultdict(int)
path = os.path.join(RD, "observations.csv")
if os.path.exists(path):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        p = r.get("property")
        d = r.get("observed_date")
        if not p or not d:
            continue
        counts[p] += 1
        last[p] = max(last.get(p, ""), d)

today = datetime.date.today()
# Properties documented as not trading (closed, never opened, rebranded into another
# basket entry) are excluded from targeting: surfacing them daily burns target slots
# that should go to properties that can actually be priced. The exclusion lives in
# basket.json["inactive"] so it stays auditable and reversible.
inactive = {(i.get("market"), i.get("property")) for i in basket.get("inactive", [])}
rankable = []
for mkey, meta in basket["markets"].items():
    for prop in meta["properties"]:
        if (mkey, prop) in inactive:
            continue
        if prop in last:
            age = (today - datetime.date.fromisoformat(last[prop])).days
            seen = last[prop]
        else:
            age = 9999
            seen = "never"
        rankable.append((age, mkey, prop, seen, counts[prop]))

rankable.sort(key=lambda x: (-x[0], x[1]))
print(f"Basket: {len(rankable)} targetable properties (excl. {len(inactive)} inactive) · observed at least once: "
      f"{sum(1 for r in rankable if r[3] != 'never')} · today {today}\n")
print(f"TOP {N} TARGETS FOR TODAY (stalest first):")
for age, mkey, prop, seen, c in rankable[:N]:
    label = "never observed" if seen == "never" else f"last seen {seen} ({age}d ago)"
    print(f"  [{mkey:9}] {prop:38} {label}, {c} obs")
print("\nRecord each verified rate with:")
print('  python3 add_rate.py <market> "<Property>" <usd> --basis <RO|BB|HB|FB|FB+|AI|FI> \\')
print('      --type <international|resident> --source "<where you saw it>, <date>"')
