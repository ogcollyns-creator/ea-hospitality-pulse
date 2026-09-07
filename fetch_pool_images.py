#!/usr/bin/env python3
"""
Widen the curated image pool in img/ using licence-verified multi-source discovery.

Where this sits
---------------
`fetch_edition_images.py` assigns a Commons photo per edition and falls back to
the curated pool in img/ when it cannot satisfy one. That fallback is what makes
editions repeat generic photos: the pool is small and Commons search is literal.
This script grows the pool from Wikimedia Commons, Openverse AND Google (the
last as a discovery layer only), so the fallback has more to choose from.

It never publishes an image on Google's word. Every candidate is passed through
image_sources.verify(), which traces the licence back to an authoritative API.
Anything unverifiable is written to img/quarantine.json and skipped.

    python3 fetch_pool_images.py                 # all topics in POOL_TOPICS
    python3 fetch_pool_images.py gorilla beach   # only these topics
    python3 fetch_pool_images.py --dry-run       # discover + verify, download nothing

Credits are appended to img/credits.json in the SAME schema the site already
renders, so credits.html and the hero captions pick them up with no other change.

Runs on the GitHub runner (Commons/Openverse/Google are unreachable from the
Cowork sandbox). Best-effort by design: any failure leaves the existing pool
untouched rather than breaking a build.
"""
import io, json, os, re, sys

import image_sources as isrc

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
POOL_CREDITS = os.path.join(IMG, "credits.json")
QUARANTINE = os.path.join(IMG, "quarantine.json")
WIDTH = 1600
MIN_W, MIN_H = 1100, 620          # landscape, large enough for a hero crop

# topic -> search queries. Deliberately concrete: broad queries return
# out-of-region stock and burn the daily Google quota for nothing.
POOL_TOPICS = {
    "mara":      ["Maasai Mara wildebeest crossing", "Maasai Mara landscape Kenya"],
    "serengeti": ["Serengeti plains Tanzania", "Serengeti wildlife Tanzania"],
    "gorilla":   ["Bwindi Impenetrable Forest gorilla", "Volcanoes National Park Rwanda"],
    "beach":     ["Diani Beach Kenya", "Nungwi beach Zanzibar", "Zanzibar dhow beach"],
    "stonetown": ["Stone Town Zanzibar architecture", "Zanzibar Stone Town street"],
    "nairobi":   ["Nairobi skyline Kenya", "Nairobi central business district"],
    "kigali":    ["Kigali skyline Rwanda", "Kigali Convention Centre"],
    "kampala":   ["Kampala city Uganda", "Lake Victoria Entebbe Uganda"],
    "dar":       ["Dar es Salaam skyline Tanzania", "Dar es Salaam harbour"],
    "aviation":  ["Kenya Airways aircraft", "Jomo Kenyatta International Airport"],
    "amboseli":  ["Amboseli elephants Kilimanjaro", "Mount Kilimanjaro landscape"],
    "lodge":     ["safari tented camp Tanzania", "safari lodge Kenya interior"],
}


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _usable(c):
    """Landscape and large enough to crop a hero from."""
    w, h = int(c.get("width") or 0), int(c.get("height") or 0)
    if w and h and (w < MIN_W or h < MIN_H or w < h):
        return False
    return bool(c.get("image_url"))


def _slug(topic, i):
    return re.sub(r"[^a-z0-9]+", "-", f"pool-{topic}-{i}".lower()).strip("-")


def main(argv):
    dry = "--dry-run" in argv
    wanted = [a for a in argv[1:] if not a.startswith("--")] or list(POOL_TOPICS)
    unknown = [t for t in wanted if t not in POOL_TOPICS]
    if unknown:
        raise SystemExit(f"unknown topic(s): {', '.join(unknown)}\n"
                         f"available: {', '.join(POOL_TOPICS)}")

    os.makedirs(IMG, exist_ok=True)
    credits = _load(POOL_CREDITS, [])
    if not isinstance(credits, list):
        credits = []
    have = {c.get("descurl") for c in credits if isinstance(c, dict)}
    quarantined_all = _load(QUARANTINE, [])

    Image = None
    if not dry:
        try:
            from PIL import Image as _I
            Image = _I
        except ImportError:
            raise SystemExit("Pillow required: pip install pillow")

    print(f"google discovery: {'ON' if isrc.google_configured() else 'OFF (no CSE credentials)'}")
    added = 0

    for topic in wanted:
        print(f"\n[{topic}]")
        cands = []
        for q in POOL_TOPICS[topic]:
            cands += isrc.discover(q, per_source=5)
        good, bad = isrc.verify(cands)
        quarantined_all += [{"topic": topic, "title": c.get("title"),
                             "page_url": c.get("page_url"),
                             "reason": c.get("verify_note")} for c in bad]
        print(f"  {len(cands)} candidates -> {len(good)} licence-verified, {len(bad)} quarantined")

        kept = 0
        for c in good:
            if kept >= 3:
                break
            if not _usable(c) or c.get("page_url") in have:
                continue
            slug = _slug(topic, kept + 1)
            out = os.path.join(IMG, slug + ".jpg")
            if not dry:
                try:
                    img = Image.open(io.BytesIO(isrc._get(c["image_url"]))).convert("RGB")
                    if img.width > WIDTH:
                        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)),
                                         Image.LANCZOS)
                    img.save(out, "JPEG", quality=85, optimize=True)
                except Exception as e:
                    print(f"  skip {slug}: {e}")
                    continue
            credits.append({
                "slug": slug,
                "title": c.get("title", ""),
                "artist": c.get("artist", "Unknown"),
                "license": c.get("licence", ""),
                "licenseurl": c.get("licence_url", ""),
                "descurl": c.get("page_url", ""),
                "source": c.get("source", ""),
                "verified_via": c.get("verify_note", ""),
            })
            have.add(c.get("page_url"))
            kept += 1
            added += 1
            print(f"  + {slug}.jpg [{c.get('licence')}] {c.get('source')}")

    if not dry:
        with open(POOL_CREDITS, "w", encoding="utf-8") as f:
            json.dump(credits, f, indent=1, ensure_ascii=False)
        with open(QUARANTINE, "w", encoding="utf-8") as f:
            json.dump(quarantined_all[-500:], f, indent=1, ensure_ascii=False)

    print(f"\n{added} image(s) added to the pool; "
          f"{len(quarantined_all)} lifetime quarantine entries.")
    print("Every added image carries a licence traced to an authoritative API.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
