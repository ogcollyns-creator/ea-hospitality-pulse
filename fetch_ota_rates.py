#!/usr/bin/env python3
"""
EA Pulse — OTA rate puller (Google Hotels metasearch via SerpApi).

Gets the rate a guest actually sees on the OTAs — including Booking.com and Expedia,
which surface as price sources inside Google Hotels — WITHOUT scraping either site.
Booking.com and Expedia both prohibit automated collection and disallow the relevant
paths in robots.txt. SerpApi is a licensed reseller of Google Hotels results and is the
sanctioned route. Do not replace this with a scraper.

WHY IT PAYS FOR ITSELF: the index collapses each property to ONE rate per ISO week, so
OTA rates are only needed weekly. A 40-property basket is ~160 searches/month, inside
SerpApi's free tier (250/month). Widening the basket moves you to the $25/mo tier.

WHAT IT UNLOCKS: rates land on channel 'ota' and chain as a series separate from the
direct rates already collected. build_rate_index.py then computes the commission-leakage
spread — median of (OTA / direct - 1) for the same property in the same week. That is the
number nobody publishes for East Africa, and it speaks straight to an owner's P&L.

BASIS CAVEAT (deliberate): Google Hotels does not state meal basis, so OTA rows are
recorded as basis UNK. Chaining is unaffected — a property is only ever compared with
itself. But the SPREAD is only computed where the DIRECT rate is room-only or B&B,
because an OTA lowest rate against a fully-inclusive safari rate compares two different
products. Safari markets will therefore show a suppressed spread. That is correct.

SETUP: export SERPAPI_KEY=...   (in CI: repository secret of the same name)
Without a key the script exits cleanly and writes nothing.

  python3 fetch_ota_rates.py --dry-run     # inspect response shape, spends 1 call
  python3 fetch_ota_rates.py [--max N]     # default 10 properties per run
"""
import os, sys, csv, json, time, datetime, difflib, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
OBS = os.path.join(RD, "observations.csv")
KEY = os.environ.get("SERPAPI_KEY", "").strip()
DELAY = 1.0
NAME_MATCH_MIN = 0.90   # required when a name has no distinctive token at all
MIN_SIM_WITH_TOKEN = 0.45  # required when the distinctive token DOES match
# Words that carry no identifying power — every third property is a "Beach Resort".
GENERIC = {"hotel","hotels","resort","resorts","beach","spa","lodge","lodges","camp","camps",
           "tented","the","and","by","safari","house","inn","suites","suite","club","palace",
           "villa","bay","park","place","grand","royal"}
# District and country names match across completely different properties.
GEO = {"nairobi","mombasa","diani","zanzibar","kigali","kampala","entebbe","westlands","gigiri",
       "nungwi","kiwengwa","mara","masai","maasai","serengeti","kenya","tanzania","uganda",
       "rwanda","africa","east","upper","hill","munyonyo"}
HEADER = ["observed_date", "market", "property", "rate_usd", "stay_date",
          "los", "source", "note", "basis", "rate_type", "channel"]


def flagval(name, default=None):
    a = sys.argv
    for i, t in enumerate(a):
        if t == name and i + 1 < len(a):
            return a[i + 1]
    return default


def iso_week(d):
    y, w, _ = datetime.date.fromisoformat(d).isocalendar()
    return f"{y}-W{w:02d}"


def search(query, cin, cout):
    p = {"engine": "google_hotels", "q": query, "check_in_date": cin,
         "check_out_date": cout, "adults": "2", "currency": "USD",
         "gl": "us", "hl": "en", "api_key": KEY}
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(p)
    with urllib.request.urlopen(url, timeout=40) as r:
        return json.loads(r.read().decode())


def tokens(name):
    return [t for t in "".join(c if c.isalnum() else " " for c in name.lower()).split() if t]


def distinctive(name):
    """The tokens that actually identify a property, minus generic and geographic noise."""
    return {t for t in tokens(name) if t not in GENERIC and t not in GEO and len(t) >= 4}


def sim(a, b):
    """Similarity that survives word-order differences.

    'Kigali Marriott' vs 'Marriott Hotel Kigali' scores 0.44 on raw sequence matching —
    below any sane floor — because SequenceMatcher is order-sensitive. Comparing the
    token-sorted forms as well lifts it to 0.83, which is what a human would say.
    """
    a, b = a.lower(), b.lower()
    raw = difflib.SequenceMatcher(None, a, b).ratio()
    srt = difflib.SequenceMatcher(None, " ".join(sorted(tokens(a))),
                                  " ".join(sorted(tokens(b)))).ratio()
    return max(raw, srt)


def pick(props, want):
    """Match a basket property to a Google Hotels result.

    Fuzzy similarity ALONE is not safe here. In the first live run 'Sankara Westlands'
    matched 'Hyatt Place Nairobi Westlands' at 0.61 and 'Diani Reef Beach Resort'
    matched 'Ziwa Beach Resort' at 0.75 — two different hotels, because the shared
    tokens were a district name and the words 'Beach Resort'. So we additionally
    require a DISTINCTIVE token (the actual hotel name) to survive into the match.
    A missed match costs one empty cell; a wrong match silently poisons the index.
    """
    want_d = distinctive(want)
    best, score, rejected = None, 0.0, []
    floor = MIN_SIM_WITH_TOKEN if want_d else NAME_MATCH_MIN
    for p in props:
        nm = p.get("name") or ""
        sc = sim(want, nm)
        if want_d and not (want_d & distinctive(nm)):
            if sc >= 0.55:
                rejected.append((nm, sc, "no distinctive token in common"))
            continue
        if sc < floor:
            continue
        if sc > score:
            best, score = p, sc
    return (best, score, rejected) if best is not None else (None, score, rejected)


def main():
    dry = "--dry-run" in sys.argv
    maxn = int(flagval("--max", "10"))
    if not KEY:
        print("SERPAPI_KEY not set — skipping OTA pull (nothing written).")
        print("Free tier is 250 searches/month; a 40-property basket needs ~160.")
        return 0

    basket = json.load(open(os.path.join(RD, "basket.json"), encoding="utf-8"))
    conv = basket["convention"]
    today = datetime.date.today()
    cin = today + datetime.timedelta(days=conv["lead_days"])
    cout = cin + datetime.timedelta(days=conv["los"])
    this_week = iso_week(today.isoformat())

    seen = set()
    if os.path.exists(OBS):
        for r in csv.DictReader(open(OBS, encoding="utf-8")):
            if (r.get("channel") or "direct") == "ota" and r.get("observed_date"):
                if iso_week(r["observed_date"]) == this_week:
                    seen.add(r["property"])

    todo = [(m, p) for m, meta in basket["markets"].items()
            for p in meta["properties"] if p not in seen]
    if not todo:
        print(f"All basket properties already have an OTA observation for {this_week}. Nothing to do.")
        return 0
    print(f"{len(todo)} properties without an OTA rate for {this_week}; "
          f"pulling up to {maxn}. Stay {cin} -> {cout}.\n")

    written, rows_out = 0, []
    for mkey, prop in todo[:1 if dry else maxn]:
        label = basket["markets"][mkey]["label"]
        try:
            d = search(f"{prop} {label}", cin.isoformat(), cout.isoformat())
        except Exception as e:
            print(f"  ! {prop}: {e}")
            continue
        props = (d.get("properties") or [])
        if dry:
            print("=== DRY RUN — response shape for:", prop, "===")
            print("top-level keys:", sorted(d.keys())[:14])
            if props:
                p0 = props[0]
                print("property keys:", sorted(p0.keys()))
                print("name:", p0.get("name"))
                print("rate_per_night:", json.dumps(p0.get("rate_per_night"), ensure_ascii=False))
                pr = p0.get("prices")
                print("prices present:", bool(pr))
                if pr:
                    print("PRICE SOURCES (this answers the Booking/Expedia question):")
                    for x in pr[:8]:
                        print("   -", x.get("source"),
                              json.dumps(x.get("rate_per_night"), ensure_ascii=False))
            else:
                print("no properties returned for this query")
            return 0

        match, score, rejected = pick(props, prop)
        if not match:
            why = f"best {score:.2f}"
            if rejected:
                why += "; rejected " + "; ".join(f"'{n}' ({s:.2f}, {r})" for n, s, r in rejected[:2])
            print(f"  - {prop}: no confident match — skipped ({why})")
            continue
        rpn = (match.get("rate_per_night") or {})
        rate = rpn.get("extracted_lowest")
        if not rate:
            print(f"  - {prop}: matched '{match.get('name')}' but no extractable rate — skipped")
            continue
        srcs = [x.get("source") for x in (match.get("prices") or []) if x.get("source")]
        note = (f"Matched '{match.get('name')}' (similarity {score:.2f}); "
                f"lowest displayed nightly rate, inclusions not stated by Google."
                + (f" Price sources: {', '.join(srcs[:6])}." if srcs else ""))
        rows_out.append([today.isoformat(), mkey, prop, rate, cin.isoformat(), conv["los"],
                         f"Google Hotels via SerpApi, {today.isoformat()}", note,
                         "UNK", "international", "ota"])
        written += 1
        print(f"  + {prop}: US${rate}" + (f"  [{', '.join(srcs[:3])}]" if srcs else ""))
        time.sleep(DELAY)

    if rows_out:
        exists = os.path.exists(OBS)
        with open(OBS, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not exists:
                w.writerow(HEADER)
            w.writerows(rows_out)
    print(f"\n{written} OTA observations written. Rebuild with: python3 build_rate_index.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
