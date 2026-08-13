#!/usr/bin/env python3
"""
Build the public JSON API for EA Hospitality Pulse.

Static endpoints under /api/v1/. GitHub Pages serves them with permissive CORS,
so any site can fetch them client-side without a proxy.

Each endpoint carries a consistent envelope: meta (source, licence, generated
timestamp, docs link) plus data. Consumers should read `meta.generated` and
cache accordingly rather than polling — these files change a few times a day
at most.

Run after any data rebuild:  python3 build_api.py
"""
import json, os, re, datetime, csv

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(HERE, "api", "v1")
os.makedirs(API, exist_ok=True)
CFG = json.load(open(os.path.join(HERE, "site_config.json")))
BASE = CFG["base"]
NOW = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

LICENCE = ("Free for reasonable use with attribution to EA Hospitality Pulse and a link to "
           + BASE + ". Do not resell or repackage as a competing data product. "
           "See " + BASE + "/terms.html")

def jsvar(path, var):
    """Evaluate a window.<VAR> data file in Node and return it as Python data.

    These files are hand-written JavaScript with unquoted keys, trailing commas
    and comments — valid JS, but not valid JSON, so they cannot be parsed
    directly. Node is the only thing that reads them correctly by definition.
    """
    import subprocess
    js = ("global.window={};require(%s);"
          "process.stdout.write(JSON.stringify(window.%s));" % (json.dumps(os.path.join(HERE, path)), var))
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or "node failed").strip().splitlines()[-1])
    if not out.stdout.strip() or out.stdout.strip() == "undefined":
        raise RuntimeError("window.%s is undefined in %s" % (var, path))
    return json.loads(out.stdout)

def emit(name, data, description, source):
    payload = {
        "meta": {
            "endpoint": f"{BASE}/api/v1/{name}.json",
            "description": description,
            "source": source,
            "generated": NOW,
            "publisher": "EA Hospitality Pulse",
            "docs": f"{BASE}/api.html",
            "methodology": f"{BASE}/methodology.html",
            "licence": LICENCE,
            "version": "v1",
        },
        "data": data,
    }
    p = os.path.join(API, name + ".json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    return name, os.path.getsize(p)

built = []

# ---- rate index ----
try:
    r = jsvar("rates.js", "RATE_INDEX")
    slim = {
        "updated": r.get("updated"),
        "basketSize": r.get("basketSize"),
        "totalObservations": r.get("totalObservations"),
        "distinctProperties": r.get("distinctProperties"),
        "convention": r.get("convention"),
        "markets": {
            k: {
                "label": v.get("label"), "country": v.get("country"), "segment": v.get("segment"),
                "index": (v.get("latest") or {}).get("index"),
                "week": (v.get("latest") or {}).get("week"),
                "n": (v.get("latest") or {}).get("n"),
                "matched": (v.get("latest") or {}).get("matched"),
                "confident": (v.get("latest") or {}).get("confident"),
                "levelComparable": v.get("levelComparable"),
                # wowPct is published ONLY when every matched pair compared a like-for-like
                # meal basis. Where a pair's basis changed (typically an undocumented UNK
                # observation now documented), the link measures a change in what is included,
                # not a change in price — so we withhold, per the null contract in api.html.
                "wowPct": (v.get("wow") if not v.get("basisChangedPairs") else None),
                "wowWithheld": (None if not v.get("basisChangedPairs") else
                                f"basis changed in {v.get('basisChangedPairs')} of "
                                f"{(v.get('latest') or {}).get('matched')} matched pairs"),
                "wowCleanPct": v.get("wowClean"),
                "series": [{"week": p.get("week"), "index": p.get("index"),
                            "n": p.get("n"), "matched": p.get("matched")}
                           for p in (v.get("series") or [])],
            } for k, v in (r.get("markets") or {}).items()
        },
    }
    built.append(emit("rate-index", slim,
        "EA Pulse Rate Index — chain-linked, matched-sample published-rate index by market. "
        "Index only; levels are suppressed where levelComparable is false.",
        "Weekly direct-booking-engine observations at a fixed convention (2 nights, 30-day lead, 2 adults, USD)."))
except Exception as e:
    print("  ! rate-index skipped:", e)

# ---- advisories ----
try:
    a = jsvar("advisories.js", "ADVISORIES")
    built.append(emit("advisories", a,
        "Travel advisory levels for East African markets from issuing governments.",
        "Official government travel advisory pages. Always verify against the issuing source before acting."))
except Exception as e:
    print("  ! advisories skipped:", e)

# ---- pipeline ----
try:
    p = jsvar("pipeline.js", "PIPELINE")
    built.append(emit("pipeline", p,
        "Hotel development pipeline — branded chain benchmark plus individually sourced signings, "
        "openings and closures across the five markets.",
        "W Hospitality Group chain pipeline benchmark plus individually verified project reporting."))
except Exception as e:
    print("  ! pipeline skipped:", e)

# ---- MICE ----
try:
    m = jsvar("mice.js", "MICE")
    built.append(emit("mice", m,
        "Confirmed conference, exhibition and major event calendar driving compression across East Africa.",
        "Organiser announcements and venue confirmations."))
except Exception as e:
    print("  ! mice skipped:", e)

# ---- costs ----
try:
    c = jsvar("costs.js", "COSTS")
    built.append(emit("cost-index", c,
        "Cost-Side Index — FX, fuel, energy and food inputs that move operator margin.",
        "Official regulator and central bank releases (EPRA, central banks, statistics bureaus)."))
except Exception as e:
    print("  ! cost-index skipped:", e)

# ---- rules & fees ----
try:
    ru = jsvar("rules.js", "RULES")
    built.append(emit("rules-and-fees", ru,
        "Regulatory tracker — levies, park fees, visa rules and tax changes with effective dates.",
        "Government gazettes, regulator notices and official fee schedules."))
except Exception as e:
    print("  ! rules skipped:", e)

# ---- raw rate observations (CSV mirrored to JSON) ----
try:
    obs = list(csv.DictReader(open(os.path.join(HERE, "rates", "observations.csv"), encoding="utf-8")))
    for o in obs:
        try: o["rate_usd"] = float(o["rate_usd"])
        except Exception: pass
        try: o["los"] = int(o["los"])
        except Exception: pass
    built.append(emit("rate-observations", obs,
        "Every individual rate observation behind the Rate Index, with source, basis and conversion note. "
        "This is the audit trail — each row records what was observed and how it was normalised.",
        "Direct booking engines and named OTAs, collected weekly."))
except Exception as e:
    print("  ! observations skipped:", e)

# ---- index of endpoints ----
idx = {
    "meta": {
        "name": "EA Hospitality Pulse public API",
        "version": "v1",
        "generated": NOW,
        "docs": f"{BASE}/api.html",
        "licence": LICENCE,
        "contact": "ceo@eahospitalitypulse.com",
    },
    "endpoints": [
        {"name": n, "url": f"{BASE}/api/v1/{n}.json", "bytes": b} for n, b in built
    ],
}
with open(os.path.join(API, "index.json"), "w", encoding="utf-8") as f:
    json.dump(idx, f, ensure_ascii=False, indent=1)

print(f"API v1 built — {len(built)} endpoints")
for n, b in built:
    print(f"  /api/v1/{n}.json  ({b:,} bytes)")
