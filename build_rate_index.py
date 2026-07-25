#!/usr/bin/env python3
"""
EA Pulse Rate Index — index engine.
Reads rates/basket.json, rates/observations.csv, rates/benchmarks.json
Writes rates.js  ->  window.RATE_INDEX for the website.

Index method (published on the site for transparency):
  * For each market and ISO week, take the MEDIAN observed lead-in rate.
    Median (not mean) so one luxury outlier can't swing the market reading.
  * The first week with >=3 observations for a market becomes its BASELINE = 100.
  * Index_t = median_t / median_baseline * 100.
  * Coverage = observations / basket size, shown so readers can judge reliability.
    A market week with <3 observations is recorded but flagged low-confidence.
Run: python3 build_rate_index.py
"""
import os, json, csv, datetime, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
MIN_N = 3  # minimum observations for a confident market reading

def iso_week(d):
    y, w, _ = datetime.date.fromisoformat(d).isocalendar()
    return f"{y}-W{w:02d}"

def week_start(tag):
    y, w = tag.split("-W")
    return datetime.date.fromisocalendar(int(y), int(w), 1).isoformat()

def main():
    basket = json.load(open(os.path.join(RD, "basket.json"), encoding="utf-8"))
    try:
        benchmarks = json.load(open(os.path.join(RD, "benchmarks.json"), encoding="utf-8"))
    except Exception:
        benchmarks = {"updated": "", "items": []}

    rows = []
    with open(os.path.join(RD, "observations.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r.get("observed_date") or not r.get("rate_usd"):
                continue
            try:
                r["rate_usd"] = float(r["rate_usd"])
            except ValueError:
                continue
            rows.append(r)

    # group: market -> week -> [rates]
    grouped = {}
    for r in rows:
        m = (r.get("market") or "").strip().lower()
        if m not in basket["markets"]:
            continue
        grouped.setdefault(m, {}).setdefault(iso_week(r["observed_date"]), []).append(r["rate_usd"])

    markets_out = {}
    for key, meta in basket["markets"].items():
        weeks = grouped.get(key, {})
        size = len(meta["properties"])
        series = []
        for wk in sorted(weeks):
            vals = weeks[wk]
            series.append({
                "week": wk, "weekStart": week_start(wk),
                "median": round(statistics.median(vals), 2),
                "n": len(vals),
                "coverage": round(100 * len(vals) / size),
                "confident": len(vals) >= MIN_N,
            })
        # baseline = first confident week
        base = next((p["median"] for p in series if p["confident"]), None)
        for p in series:
            p["index"] = round(p["median"] / base * 100, 1) if base else None
        latest = series[-1] if series else None
        prev = series[-2] if len(series) > 1 else None
        wow = None
        if latest and prev and prev["median"]:
            wow = round((latest["median"] - prev["median"]) / prev["median"] * 100, 1)
        markets_out[key] = {
            "label": meta["label"], "segment": meta["segment"], "country": meta["country"],
            "basketSize": size, "series": series, "baseline": base,
            "latest": latest, "wow": wow,
        }

    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "convention": basket["convention"],
        "minN": MIN_N,
        "totalObservations": len(rows),
        "basketSize": sum(len(m["properties"]) for m in basket["markets"].values()),
        "markets": markets_out,
        "benchmarks": benchmarks,
    }
    with open(os.path.join(HERE, "rates.js"), "w", encoding="utf-8") as f:
        f.write("window.RATE_INDEX = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"rates.js built — {len(rows)} observations across {len(markets_out)} markets.")

if __name__ == "__main__":
    main()
