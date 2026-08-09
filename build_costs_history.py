#!/usr/bin/env python3
"""Emit costs-history.js from rates/costs-history.csv for the Cost Index chart."""
import os, csv, json, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "rates", "costs-history.csv")
OUT = os.path.join(HERE, "costs-history.js")

# Metrics worth charting: comparable over time and meaningful as a line.
CHARTABLE_GROUPS = ("Currency", "Fuel", "Inflation")

rows = []
if os.path.exists(SRC):
    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

series = collections.defaultdict(list)
meta = {}
for r in rows:
    if not any(r["group"].startswith(g) for g in CHARTABLE_GROUPS):
        continue
    key = r["metric"]
    try:
        v = float(r["value_num"])
    except (ValueError, KeyError):
        continue
    series[key].append({"date": r["observed_date"], "value": v})
    meta[key] = {"group": r["group"], "unit": r["unit"], "source": r["source"]}

for k in series:
    series[k].sort(key=lambda p: p["date"])

dates = sorted({p["date"] for s in series.values() for p in s})

payload = {
    "updated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
    "startedOn": dates[0] if dates else None,
    "dates": dates,
    "pointsPerMetric": {k: len(v) for k, v in series.items()},
    "chartable": [k for k, v in series.items() if len(v) > 1],
    "note": ("The Cost-Side Index previously stored only a current reading per metric, with change "
             "described in prose. This series is built forward from the first snapshot — it does not "
             "reconstruct history that was never recorded. Charts appear once a metric has at least "
             "two observations."),
    "metrics": {k: {"meta": meta[k], "points": v} for k, v in series.items()},
}

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// EA Pulse Cost-Side Index — historical series.\n")
    f.write("// Built forward from the first snapshot by snapshot_costs.py; not backfilled.\n")
    f.write("window.COSTS_HISTORY = ")
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")

print(f"costs-history.js — {len(series)} metrics tracked, {len(dates)} date(s)")
print(f"  chartable now (>=2 points): {len(payload['chartable'])}")
if not payload["chartable"]:
    print("  (expected — the series starts today and fills as snapshots accumulate)")
