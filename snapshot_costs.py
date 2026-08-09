#!/usr/bin/env python3
"""
Append the current Cost-Side Index reading to rates/costs-history.csv.

costs.js holds only a current value per metric plus a prose change note, so
there has never been a series to chart. This script snapshots the numeric part
of each metric every time it runs, building the history forward from today.

It is deliberately additive and idempotent per (date, metric): running twice on
the same day updates rather than duplicates, so a re-run after a costs.js fix
corrects the record instead of doubling it.

Run after every costs.js update:  python3 snapshot_costs.py
"""
import os, re, csv, json, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rates", "costs-history.csv")
HEADER = ["observed_date", "group", "metric", "value_num", "unit", "raw_value", "period", "source"]

def load_costs():
    js = ("global.window={};require(%s);process.stdout.write(JSON.stringify(window.COSTS));"
          % json.dumps(os.path.join(HERE, "costs.js")))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit("could not read costs.js: " + (r.stderr or "").strip()[:200])
    return json.loads(r.stdout)

NUM = re.compile(r"(-?[\d,]+(?:\.\d+)?)")

def parse_value(v):
    """Return (number, unit) from strings like 'KSh 214.03/L', '129.30', '13.6%'."""
    if v is None:
        return None, ""
    s = str(v).strip()
    m = NUM.search(s.replace(",", ""))
    if not m:
        return None, ""
    try:
        n = float(m.group(1))
    except ValueError:
        return None, ""
    unit = (s[:m.start()] + s[m.end():]).strip()
    unit = re.sub(r"\s+", " ", unit)
    return n, unit

def main():
    costs = load_costs()
    today = datetime.date.today().isoformat()
    rows = []
    for it in costs.get("items", []):
        n, unit = parse_value(it.get("value"))
        if n is None:
            continue
        rows.append({
            "observed_date": today,
            "group": it.get("group", ""),
            "metric": it.get("metric", ""),
            "value_num": n,
            "unit": unit,
            "raw_value": it.get("value", ""),
            "period": it.get("period", ""),
            "source": it.get("source", ""),
        })

    existing = []
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    keep = [r for r in existing if not (r["observed_date"] == today and
            any(r["metric"] == n["metric"] for n in rows))]
    allrows = keep + rows
    allrows.sort(key=lambda r: (r["observed_date"], r["group"], r["metric"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in allrows:
            w.writerow(r)

    dates = sorted({r["observed_date"] for r in allrows})
    print(f"costs-history.csv — {len(allrows)} rows, {len(rows)} snapshotted today")
    print(f"  distinct metrics: {len({r['metric'] for r in allrows})}")
    print(f"  distinct dates:   {len(dates)}  {dates[:1]}..{dates[-1:]}")
    if len(dates) < 2:
        print("  NOTE: one date only — charts stay flat until this has run on at least two.")

if __name__ == "__main__":
    main()
