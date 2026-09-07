#!/usr/bin/env python3
"""
Give editions a real PHOTOGRAPH where one is genuinely relevant, using the
licence-verified multi-source pipeline in image_sources.py.

The problem this solves
-----------------------
On 28 Aug 2026 data cards became the default hero, for a good reason: the
Commons-only topic matcher kept reaching for regional scenery when it could not
match a subject, and a Zanzibar yield story ran under a baby elephant. A card
carrying the edition's own number is always relevant and never embarrassing.

The side effect was that EVERY edition became a card. Property owners reading
the site see a wall of typography and no photography, which reads as unfinished.
The original reasoning was about RELEVANCE, not about photographs being wrong.

So this pass restores photographs on the editions that have a genuine visual
subject, and leaves the data card everywhere else. Two things make that safe
now that were not true in August:

  1. Recall. Discovery spans Wikimedia Commons, Openverse and (when configured)
     Google Programmable Search, instead of Commons alone. More licence-clear
     candidates per topic means fewer desperate reaches for scenery.
  2. An explicit confidence bar. A topic must be genuinely evidenced in the
     edition text before any photo is assigned -- see MIN_TOPIC_SCORE. Below the
     bar the edition keeps its card. Silence beats a wrong picture.

Every image is licence-verified by image_sources.verify() against an
authoritative API before it is written. Nothing ships on a Google rights filter
alone. See docs/image-policy.md.

Order matters -- run this BEFORE hero_extra.py --data-card, which skips any
edition that already has a hero:

    python3 assign_edition_photos.py --dry-run          # report only
    python3 assign_edition_photos.py --limit 20         # assign up to 20
    python3 assign_edition_photos.py --replace-cards    # also revisit data-card editions

Network: Commons / Openverse / Google are unreachable from the Cowork sandbox,
so this runs on the GitHub runner. Best-effort by design -- any edition it
cannot satisfy keeps whatever hero it already had.
"""
import argparse, io, json, os, re, sys

import image_sources as isrc

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "editions-src")
IMG = os.path.join(HERE, "img")
EDIMG = os.path.join(IMG, "editions")
CREDITS = os.path.join(IMG, "edition-credits.json")

WIDTH = 1600
MIN_W, MIN_H = 1200, 630           # below this a hero crop looks soft
# A hero must match the LEAD STORY, not vocabulary that happens to appear
# somewhere in 1,500 words. Scoring is weighted so the headline decides:
# a hit in the lead counts triple, and no lead hit means no photo at all.
# Without this, the 6 Sep evening edition -- a piece about trips unbundling at
# the city end -- scored "aviation" on two incidental uses of "route" and
# "airport", which is precisely the mismatch the data card was introduced to stop.
LEAD_WEIGHT = 3
MIN_TOPIC_SCORE = 5                # weighted hits required before we trust a topic

# Topic -> (keywords proving the subject is really in the edition, search queries).
# Queries are concrete: broad ones return out-of-region stock and waste quota.
TOPICS = [
    ("gorilla",   ["gorilla", "bwindi", "volcanoes national park", "virunga",
                   "primate", "chimpanzee", "nyungwe", "permit"],
                  ["Bwindi Impenetrable Forest gorilla", "mountain gorilla Uganda",
                   "Volcanoes National Park Rwanda"]),
    ("migration", ["migration", "wildebeest", "mara river", "crossing", "serengeti"],
                  ["wildebeest migration Mara river crossing",
                   "Serengeti wildebeest migration", "Maasai Mara plains Kenya"]),
    ("aviation",  ["airline", "aviation", "aircraft", "jkia", "kenya airways",
                   "rwandair", "uganda airlines", "air tanzania", "route", "airport",
                   "seat capacity", "airlift", "frequencies"],
                  ["Kenya Airways aircraft", "Jomo Kenyatta International Airport",
                   "airliner Africa airport apron"]),
    ("beach",     ["beach", "resort", "coast", "diani", "nungwi", "watamu",
                   "indian ocean", "island", "reef", "dhow"],
                  ["Diani Beach Kenya", "Nungwi beach Zanzibar",
                   "Zanzibar dhow turquoise water"]),
    ("stonetown", ["stone town", "zanzibar city", "unguja", "swahili architecture"],
                  ["Stone Town Zanzibar architecture", "Stone Town Zanzibar street"]),
    ("nairobi",   ["nairobi", "westlands", "upper hill", "gigiri", "kilimani"],
                  ["Nairobi skyline Kenya", "Nairobi central business district"]),
    ("kigali",    ["kigali", "rwanda development board", "convention centre", "rdb"],
                  ["Kigali skyline Rwanda", "Kigali Convention Centre"]),
    ("kampala",   ["kampala", "entebbe", "uganda tourism board", "speke"],
                  ["Kampala city Uganda", "Entebbe Lake Victoria Uganda"]),
    ("amboseli",  ["amboseli", "kilimanjaro", "elephant", "tsavo"],
                  ["Amboseli elephants Kilimanjaro", "Mount Kilimanjaro from Amboseli"]),
    ("safari",    ["lodge", "camp", "tented", "game drive", "conservancy",
                   "laikipia", "samburu", "ngorongoro", "ruaha"],
                  ["safari tented camp Tanzania", "safari lodge Kenya",
                   "Ngorongoro Crater landscape"]),
    ("port",      ["port", "harbour", "cargo", "container", "dhow", "shipping", "quay"],
                  ["Dar es Salaam port harbour", "Mombasa port harbour"]),
    ("mice",      ["conference", "congress", "delegates", "convention", "summit",
                   "expo", "icca", "mice"],
                  ["conference hall Africa delegates", "Kigali Convention Centre interior"]),
]


def _load_credits():
    try:
        with open(CREDITS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _edition_text(eid):
    p = os.path.join(SRC, eid + ".md")
    try:
        return open(p, encoding="utf-8").read().lower()
    except Exception:
        return ""


_LEAD_ITEM = re.compile(r"^1\ufe0f\u20e3\s*(.+)$", re.M)


def lead_text(md):
    """The edition's own headline area: the first numbered item, plus the
    opening lines before it. This is what the hero has to agree with."""
    parts = []
    m = _LEAD_ITEM.search(md)
    if m:
        parts.append(m.group(1))
    head = re.split(r"\n\u2501{3,}", md, 1)[0]
    parts.append(head[:600])
    return " ".join(parts).lower()


def detect_topic(text, lead=""):
    """Return (topic, queries, score) for the best-evidenced topic, or None.

    Weighted: a keyword in the lead counts LEAD_WEIGHT times. A topic with no
    lead presence at all is rejected outright, however often it appears in the
    body -- that is the guard against decorative mismatches.
    """
    lead = lead or text
    best = None
    for name, keys, queries in TOPICS:
        body_hits = sum(1 for k in keys if k in text)
        lead_hits = sum(1 for k in keys if k in lead)
        if not lead_hits:
            continue                     # not what the edition is about
        score = body_hits + LEAD_WEIGHT * lead_hits
        if best is None or score > best[2]:
            best = (name, queries, score)
    if best and best[2] >= MIN_TOPIC_SCORE:
        return best
    return None


def _is_data_card(entry):
    return str(entry.get("title", "")).startswith("Data card")


def _usable(c):
    w, h = int(c.get("width") or 0), int(c.get("height") or 0)
    if w and h and (w < MIN_W or h < MIN_H or w < h):
        return False
    return bool(c.get("image_url"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing")
    ap.add_argument("--limit", type=int, default=25,
                    help="max editions to assign in one run (protects API quota)")
    ap.add_argument("--replace-cards", action="store_true",
                    help="also revisit editions currently showing a data card")
    ap.add_argument("--only", default="", help="comma-separated edition ids")
    a = ap.parse_args(argv)

    os.makedirs(EDIMG, exist_ok=True)
    credits = _load_credits()

    Image = None
    if not a.dry_run:
        try:
            from PIL import Image as _I
            Image = _I
        except ImportError:
            print("Pillow required: pip install pillow", file=sys.stderr)
            return 1

    ids = [f[:-3] for f in sorted(os.listdir(SRC)) if f.endswith(".md")]
    if a.only:
        want = {s.strip() for s in a.only.split(",") if s.strip()}
        ids = [i for i in ids if i in want]

    # candidates: no hero at all, or a data card when --replace-cards is set
    todo = []
    for eid in ids:
        cur = credits.get(eid)
        if cur is None:
            todo.append(eid)
        elif a.replace_cards and _is_data_card(cur):
            todo.append(eid)

    used_pages = {v.get("descurl") for v in credits.values() if isinstance(v, dict)}

    print(f"google discovery: {'ON' if isrc.google_configured() else 'OFF (no CSE credentials)'}")
    print(f"{len(todo)} edition(s) eligible; assigning at most {a.limit}\n")

    assigned = skipped_topic = skipped_nocand = 0
    for eid in todo:
        if assigned >= a.limit:
            print("limit reached — stopping")
            break
        _md = _edition_text(eid)
        hit = detect_topic(_md, lead_text(_md))
        if not hit:
            skipped_topic += 1
            print(f"  keep card  {eid}  (no confident visual subject)")
            continue
        topic, queries, score = hit

        cands = []
        for q in queries:
            cands += isrc.discover(q, per_source=4)
            if len(cands) >= 12:
                break
        good, bad = isrc.verify(cands)
        good = [c for c in good if _usable(c) and c.get("page_url") not in used_pages]
        if not good:
            skipped_nocand += 1
            print(f"  keep card  {eid}  [{topic}] no licence-verified candidate passed quality")
            continue

        pick = good[0]
        out = os.path.join(EDIMG, eid + ".jpg")
        if not a.dry_run:
            try:
                img = Image.open(io.BytesIO(isrc._get(pick["image_url"]))).convert("RGB")
                if img.width > WIDTH:
                    img = img.resize((WIDTH, round(img.height * WIDTH / img.width)),
                                     Image.LANCZOS)
                img.save(out, "JPEG", quality=88, optimize=True)
            except Exception as e:
                print(f"  FAILED     {eid}: {e}")
                continue
            credits[eid] = {
                "id": eid,
                "title": pick.get("title", ""),
                "artist": pick.get("artist", "Unknown"),
                "license": pick.get("licence", ""),
                "licenseurl": pick.get("licence_url", ""),
                "descurl": pick.get("page_url", ""),
                "source": pick.get("source", ""),
                "verified_via": pick.get("verify_note", ""),
            }
        used_pages.add(pick.get("page_url"))
        assigned += 1
        print(f"  PHOTO      {eid}  [{topic}/{score}] {pick.get('licence')} · "
              f"{pick.get('title', '')[:46]}")

    if not a.dry_run and assigned:
        with open(CREDITS, "w", encoding="utf-8") as f:
            json.dump(credits, f, indent=1, ensure_ascii=False, sort_keys=True)

    print(f"\nassigned {assigned} photo(s); {skipped_topic} kept a card for lack of a "
          f"visual subject; {skipped_nocand} found no verified candidate.")
    if a.dry_run:
        print("dry run — nothing written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
