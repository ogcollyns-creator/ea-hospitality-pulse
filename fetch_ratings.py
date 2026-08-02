#!/usr/bin/env python3
"""
EA Pulse Reputation Index — Google Places ratings puller.

Pulls the public star rating and review count for every property in the rate basket
via the official Google Places API (New), appends them to a history file, and writes
reviews.js -> window.REVIEWS for the website.

WHY THIS ROUTE: Booking.com and Expedia both prohibit automated collection in their
terms and disallow the relevant paths in robots.txt, and neither exposes a public API
for reading reviews. Google Places is an official, licensed, paid API and is the
defensible way to track reputation. Do not replace it with a scraper.

COST — READ BEFORE RAISING THE CADENCE. On 1 March 2025 Google replaced the pooled
US$200 monthly credit with PER-SKU free caps that do not pool: 10,000 calls/month for
Essentials, 5,000 for Pro, 1,000 for Enterprise. Place Details including `rating` sits in
the ENTERPRISE tier, so the free allowance is 1,000 calls/month.

A 40-property basket pulled WEEKLY is ~173 calls/month — comfortably free.
The same basket pulled DAILY is ~1,200 calls/month — over the cap, and billable.

MIN_HOURS is therefore set to 150 (~6.25 days) so this script can be invoked daily and
will still only pull each property once a week. That is not a compromise: star ratings
are lifetime averages and barely move day to day. The signal worth having is review
VELOCITY over weeks, which a weekly cadence captures perfectly.
Adding review TEXT moves the call to Enterprise+Atmosphere (~US$40/1,000) AND consumes
the same 1,000 free calls; leave FETCH_REVIEW_TEXT=0 unless you have a reason.

SETUP: export GOOGLE_PLACES_API_KEY=...   (in CI: repository secret of the same name)
Without a key the script exits cleanly and leaves reviews.js untouched, so the daily
job never fails just because the key is absent.

Run: python3 fetch_ratings.py [--force]
"""
import os, sys, json, csv, time, datetime, urllib.request, urllib.error, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, "rates")
PLACES_CACHE = os.path.join(RD, "places.json")       # property -> place_id (permanent)
HISTORY = os.path.join(RD, "ratings_history.csv")    # append-only observation ledger
KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
FETCH_TEXT = os.environ.get("FETCH_REVIEW_TEXT", "0") == "1"
MIN_HOURS = 150         # ~6.25 days: one pull per property per week. See COST note.
DELAY = 0.15            # courtesy pause between calls
UA = "EAHospitalityPulse/1.0 (+https://eahospitalitypulse.com; ogcollyns@gmail.com)"


def _post(url, payload, field_mask):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": KEY,
                 "X-Goog-FieldMask": field_mask, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def _get(url, field_mask):
    req = urllib.request.Request(
        url, headers={"X-Goog-Api-Key": KEY, "X-Goog-FieldMask": field_mask, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def resolve_place_id(name, market_label, cache):
    """Resolve a property to a Google place ID once, then cache it forever."""
    if name in cache:
        return cache[name]
    try:
        d = _post("https://places.googleapis.com/v1/places:searchText",
                  {"textQuery": f"{name}, {market_label}, East Africa", "maxResultCount": 1},
                  "places.id,places.displayName")
        pl = (d.get("places") or [])
        if not pl:
            cache[name] = None
        else:
            cache[name] = pl[0]["id"]
            print(f"  resolved {name} -> {cache[name]}")
    except Exception as e:
        print(f"  ! resolve failed for {name}: {e}")
        return None
    time.sleep(DELAY)
    return cache[name]


def main():
    force = "--force" in sys.argv
    if not KEY:
        print("GOOGLE_PLACES_API_KEY not set — skipping ratings pull (reviews.js untouched).")
        print("Add the key as a repo secret to enable the reputation index.")
        return 0

    basket = json.load(open(os.path.join(RD, "basket.json"), encoding="utf-8"))
    cache = json.load(open(PLACES_CACHE, encoding="utf-8")) if os.path.exists(PLACES_CACHE) else {}

    hist = []
    if os.path.exists(HISTORY):
        with open(HISTORY, encoding="utf-8") as f:
            hist = list(csv.DictReader(f))
    last_seen = {}
    for h in hist:
        last_seen[h["property"]] = max(last_seen.get(h["property"], ""), h["observed_at"])

    now = datetime.datetime.now(datetime.timezone.utc)
    fields = "id,displayName,rating,userRatingCount"
    if FETCH_TEXT:
        fields += ",reviews"

    fresh = []
    for mkey, meta in basket["markets"].items():
        for prop in meta["properties"]:
            if not force and last_seen.get(prop):
                try:
                    age = (now - datetime.datetime.fromisoformat(last_seen[prop])).total_seconds() / 3600
                    if age < MIN_HOURS:
                        continue
                except Exception:
                    pass
            pid = resolve_place_id(prop, meta["label"], cache)
            if not pid:
                continue
            try:
                d = _get(f"https://places.googleapis.com/v1/places/{pid}", fields)
            except Exception as e:
                print(f"  ! details failed for {prop}: {e}")
                continue
            rating = d.get("rating")
            count = d.get("userRatingCount")
            if rating is None:
                continue
            fresh.append({"observed_at": now.isoformat(), "market": mkey, "property": prop,
                          "place_id": pid, "rating": rating, "review_count": count or 0})
            time.sleep(DELAY)

    json.dump(cache, open(PLACES_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    if fresh:
        exists = os.path.exists(HISTORY)
        with open(HISTORY, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["observed_at", "market", "property",
                                              "place_id", "rating", "review_count"])
            if not exists:
                w.writeheader()
            w.writerows(fresh)
        hist += fresh
    print(f"ratings pulled: {len(fresh)} properties this run; {len(hist)} rows in history.")

    # ---- roll up to reviews.js ----
    latest = {}
    for h in hist:
        k = h["property"]
        if k not in latest or h["observed_at"] > latest[k]["observed_at"]:
            latest[k] = h
    markets_out = {}
    for mkey, meta in basket["markets"].items():
        pts = [latest[p] for p in meta["properties"] if p in latest]
        if not pts:
            continue
        ratings = [float(p["rating"]) for p in pts]
        counts = [int(p["review_count"]) for p in pts]
        markets_out[mkey] = {
            "label": meta["label"], "segment": meta["segment"], "country": meta["country"],
            "medianRating": round(statistics.median(ratings), 2),
            "properties": len(pts), "basketSize": len(meta["properties"]),
            "totalReviews": sum(counts),
            "items": sorted(({"property": p["property"], "rating": float(p["rating"]),
                              "reviews": int(p["review_count"])} for p in pts),
                            key=lambda x: -x["rating"]),
        }
    out = {"updated": now.strftime("%Y-%m-%d %H:%M UTC"),
           "source": "Google Places API (New) — official licensed API",
           "note": ("Public star ratings and review counts for the fixed rate basket. "
                    "Ratings are lifetime averages and move slowly; the useful signal is "
                    "review VELOCITY (new reviews per week) and divergence between neighbours."),
           "markets": markets_out}
    with open(os.path.join(HERE, "reviews.js"), "w", encoding="utf-8") as f:
        f.write("window.REVIEWS = " + json.dumps(out, ensure_ascii=False, indent=1) + ";\n")
    print(f"reviews.js built — {len(markets_out)} markets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
