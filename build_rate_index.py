#!/usr/bin/env python3
"""
EA Pulse Rate Index — index engine (v2, chain-linked).
Reads rates/basket.json, rates/observations.csv, rates/benchmarks.json
Writes rates.js  ->  window.RATE_INDEX for the website.

WHY v2: v1 took the median of raw rates per market-week and indexed that against a
fixed baseline median. That has three defects which daily collection would amplify:
  1. Mixed meal bases. The basket holds room-only, B&B, HB, FB, FB+, AI and fully
     inclusive rates. A median across them measures inclusion mix as much as price.
  2. Sample-composition bias. If a cheap property drops out of a week's sample the
     median moves even though no rate changed.
  3. No per-property dedupe. Observing a property daily would give it up to 7x the
     weight of a weekly-observed peer and push coverage above 100%.

METHOD (v2), published on the site for transparency:
  * Collapse each property to ONE rate per ISO week (median of that week's observations).
    Daily collection therefore improves freshness and matching, never weighting.
  * Compute CHAINED LINK RELATIVES on matched samples: for week t, take every property
    observed both at t and at its most recent prior observation (within LOOKBACK_WEEKS),
    and take the median of rate_t / rate_prev. Multiply the running index by that median.
    Because each property is only ever compared with ITSELF, the index is valid even
    though the basket mixes meal bases and rate types — a fully-inclusive lodge and a
    room-only city hotel can sit in one index as long as neither changes basis.
  * A property entering the basket contributes nothing until its SECOND observation,
    so new entrants cannot drag the index toward 100.
  * The chain starts at the first week with >= MIN_N distinct properties (index = 100).
  * medianRaw is property-weighted and is reported for context only. It is NOT
    comparable across markets: check levelComparable before quoting a level.
Run: python3 build_rate_index.py
"""
import os, json, csv, datetime, statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
MIN_N = 3           # distinct properties needed for a confident market reading
SPREADABLE = {"RO", "BB"}  # direct bases where an OTA "lowest rate" is a like-for-like comparison
LOOKBACK_WEEKS = 6  # how far back a property may be matched for a link relative


def iso_week(d):
    y, w, _ = datetime.date.fromisoformat(d).isocalendar()
    return f"{y}-W{w:02d}"


def week_start(tag):
    y, w = tag.split("-W")
    return datetime.date.fromisocalendar(int(y), int(w), 1).isoformat()


def week_delta(a, b):
    """Whole weeks between two ISO week tags."""
    return round((datetime.date.fromisoformat(week_start(a))
                  - datetime.date.fromisoformat(week_start(b))).days / 7)


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
            r["market"] = (r.get("market") or "").strip().lower()
            r["week"] = iso_week(r["observed_date"])
            rows.append(r)

    # market -> channel -> property -> week -> [rates]   (per-property dedupe happens here)
    g = {}
    meta_rows = {}
    basis_at = {}
    for r in rows:
        if r["market"] not in basket["markets"]:
            continue
        ch = (r.get("channel") or "direct").strip().lower()
        g.setdefault(r["market"], {}).setdefault(ch, {}).setdefault(r["property"], {}) \
            .setdefault(r["week"], []).append(r["rate_usd"])
        meta_rows.setdefault(r["market"], {}).setdefault(ch, {}).setdefault(r["week"], []).append(r)
        basis_at.setdefault(r["market"], {}).setdefault(ch, {}).setdefault(r["property"], {}) \
            .setdefault(r["week"], set()).add(r.get("basis") or "?")

    def build_series(pw, size, mrows):
        """Chain one channel's observations into an index series."""
        all_weeks = sorted({w for weeks in pw.values() for w in weeks})
        series = []
        for wk in all_weeks:
            obs_props = sorted([p for p in pw if wk in pw[p]])
            vals = [pw[p][wk] for p in obs_props]
            raw = mrows.get(wk, [])
            bmix = Counter(x.get("basis") or "?" for x in raw)
            tmix = Counter(x.get("rate_type") or "?" for x in raw)
            series.append({
                "week": wk, "weekStart": week_start(wk),
                "median": round(statistics.median(vals), 2),
                "n": len(obs_props), "observations": len(raw),
                "coverage": round(100 * len(obs_props) / size),
                "confident": len(obs_props) >= MIN_N,
                "basisMix": dict(bmix), "rateTypeMix": dict(tmix),
                "levelComparable": len(bmix) == 1 and len(tmix) == 1,
                "matched": 0, "link": None, "index": None,
            })
        start = next((i for i, p in enumerate(series) if p["confident"]), None)
        if start is not None:
            series[start]["index"] = 100.0
            running = 100.0
            for i in range(start + 1, len(series)):
                wk = series[i]["week"]
                pairs = []
                for p in pw:
                    if wk not in pw[p]:
                        continue
                    prior = [w for w in pw[p] if w < wk and 0 < week_delta(wk, w) <= LOOKBACK_WEEKS]
                    if prior and pw[p][max(prior)]:
                        pairs.append(pw[p][wk] / pw[p][max(prior)])
                if pairs:
                    link = statistics.median(pairs)
                    running *= link
                    series[i]["link"] = round(link, 5)
                series[i]["matched"] = len(pairs)
                series[i]["index"] = round(running, 1)
                if series[i]["confident"] and len(pairs) < MIN_N:
                    series[i]["confident"] = False
        return series, start

    def collapse(chan_props):
        return {p: {w: statistics.median(v) for w, v in weeks.items()}
                for p, weeks in chan_props.items()}

    markets_out = {}
    for key, mmeta in basket["markets"].items():
        chans = g.get(key, {})
        size = len(mmeta["properties"])
        mr = meta_rows.get(key, {})

        pw_direct = collapse(chans.get("direct", {}))
        pw_ota = collapse(chans.get("ota", {}))

        series, start = build_series(pw_direct, size, mr.get("direct", {})) if pw_direct else ([], None)
        ota_series, _ = build_series(pw_ota, size, mr.get("ota", {})) if pw_ota else ([], None)

        latest = series[-1] if series else None
        wow = round((latest["link"] - 1) * 100, 1) if latest and latest.get("link") is not None else None
        ota_latest = ota_series[-1] if ota_series else None
        ota_wow = (round((ota_latest["link"] - 1) * 100, 1)
                   if ota_latest and ota_latest.get("link") is not None else None)

        # ---- commission-leakage spread: OTA vs direct, same property, same week ----
        # Only meaningful where the DIRECT rate is room-only or B&B. An OTA "lowest
        # rate" against a fully-inclusive safari rate compares two different products,
        # so those markets are suppressed rather than published misleadingly.
        spread_series = []
        bs = basis_at.get(key, {})
        ota_weeks = sorted({w for weeks in pw_ota.values() for w in weeks})
        for wk in ota_weeks:
            pairs = []
            skipped = 0
            for p in pw_ota:
                if wk not in pw_ota[p] or p not in pw_direct or wk not in pw_direct[p]:
                    continue
                dbases = bs.get("direct", {}).get(p, {}).get(wk, set())
                if not dbases or not dbases.issubset(SPREADABLE):
                    skipped += 1
                    continue
                d = pw_direct[p][wk]
                if d:
                    pairs.append(pw_ota[p][wk] / d - 1)
            if pairs or skipped:
                spread_series.append({
                    "week": wk, "weekStart": week_start(wk),
                    "spreadPct": round(statistics.median(pairs) * 100, 1) if pairs else None,
                    "n": len(pairs), "skippedNonComparableBasis": skipped,
                })

        overall_b, overall_t = Counter(), Counter()
        for x in rows:
            if x["market"] == key and (x.get("channel") or "direct") == "direct":
                overall_b[x.get("basis") or "?"] += 1
                overall_t[x.get("rate_type") or "?"] += 1

        markets_out[key] = {
            "label": mmeta["label"], "segment": mmeta["segment"], "country": mmeta["country"],
            "basketSize": size,
            "series": series,
            "baseline": series[start]["median"] if start is not None else None,
            "latest": latest, "wow": wow,
            "basisMix": dict(overall_b), "rateTypeMix": dict(overall_t),
            "levelComparable": len(overall_b) == 1 and len(overall_t) == 1,
            "residentOnly": len(overall_t) == 1 and "resident" in overall_t,
            "ota": ({"series": ota_series, "latest": ota_latest, "wow": ota_wow}
                    if ota_series else None),
            "spread": (spread_series or None),
            "spreadLatest": (spread_series[-1] if spread_series else None),
        }

    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "convention": basket["convention"],
        "minN": MIN_N,
        "lookbackWeeks": LOOKBACK_WEEKS,
        "method": "chain-linked matched-sample",
        "methodNote": ("Each property is compared only with itself, so the index measures rate "
                       "MOVEMENT validly even though the basket mixes meal bases and rate types. "
                       "Raw medians are context only and are not comparable across markets — "
                       "check levelComparable before quoting a level."),
        "spreadNote": ("Commission-leakage spread = median of (OTA rate / direct rate - 1) for the "
                       "same property in the same week. Computed only where the direct rate is "
                       "room-only or B&B, since an OTA lowest rate is not comparable with a "
                       "fully-inclusive safari rate. Markets where no property qualifies report null."),
        "totalObservations": len(rows),
        "distinctProperties": len({(r["market"], r["property"]) for r in rows}),
        "basketSize": sum(len(m["properties"]) for m in basket["markets"].values()),
        "markets": markets_out,
        "benchmarks": benchmarks,
    }
    with open(os.path.join(HERE, "rates.js"), "w", encoding="utf-8") as f:
        f.write("window.RATE_INDEX = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"rates.js built — {len(rows)} observations, "
          f"{out['distinctProperties']} distinct properties, {len(markets_out)} markets.")
    for k, m in markets_out.items():
        if m["latest"]:
            sp = m.get('spreadLatest')
            sptxt = ''
            if sp:
                sptxt = (f" spread={sp['spreadPct']}% (n={sp['n']}"
                         f"{', ' + str(sp['skippedNonComparableBasis']) + ' skipped: basis' if sp['skippedNonComparableBasis'] else ''})")
            print(f"  {k:9} idx={m['latest']['index']} wow={m['wow']} "
                  f"props={m['latest']['n']}/{m['basketSize']} "
                  f"conf={m['latest']['confident']} levelComparable={m['levelComparable']}"
                  f"{' RESIDENT-ONLY' if m['residentOnly'] else ''}"
                  f"{' | OTA idx=' + str(m['ota']['latest']['index']) if m.get('ota') and m['ota']['latest'] else ''}"
                  f"{sptxt}")


if __name__ == "__main__":
    main()
