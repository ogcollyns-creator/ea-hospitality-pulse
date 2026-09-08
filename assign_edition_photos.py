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
    # ---------------------------------------------------------------- SUBJECTS
    # Added 8 Sep 2026. Until now every topic in this list was scenery -- safari,
    # beach, gorilla, skyline. So when the lead was an Ebola outbreak, a fuel
    # review or a currency move, the BEST this pipeline could do was a pretty
    # photograph of the right country. That is why those editions kept falling
    # through to a card or, worse, to a district boundary map.
    #
    # Subject frames are deliberately listed FIRST: on a story about a thing,
    # a picture of the thing beats a picture of the place it happened.
    #
    # Health queries target RESPONSE INFRASTRUCTURE -- treatment centres, PPE,
    # laboratories, health workers -- never patients. An outbreak hero must not
    # put a sick person's face on a hospitality brief.
    ("health",    ["ebola", "outbreak", "epidemic", "pheic", "who afro", "africa cdc",
                   "cholera", "marburg", "mpox", "quarantine", "case fatality",
                   "treatment centre", "treatment center", "health worker", "vaccine",
                   "bundibugyo", "surveillance", "ministry of health", "beds"],
                  ["Ebola treatment centre health workers",
                   "health worker personal protective equipment outbreak response",
                   "mobile laboratory outbreak response Africa",
                   "WHO emergency medical supplies airlift",
                   "airport thermal screening health check"]),
    ("energy",    ["epra", "fuel price", "diesel", "petrol", "kerosene", "tariff",
                   "kilowatt", "kwh", "generator", "electricity", "power cut",
                   "load shedding", "solar", "grid", "pump price"],
                  ["fuel tanker filling station Africa", "electricity transmission pylons Africa",
                   "solar panels hotel roof", "diesel generator installation"]),
    ("currency",  ["shilling", "inflation", "cpi", "central bank", "forex", "exchange rate",
                   "reserves", "interest rate", "mpc", "devaluation", "cost base",
                   "levy", "vat", "tax", "duty", "bond"],
                  ["East African banknotes currency", "central bank building Africa",
                   "foreign exchange bureau counter", "calculator financial documents desk"]),
    ("logistics", ["port", "harbour", "cargo", "container", "freight", "customs",
                   "supply chain", "shipping", "imports", "border post"],
                  ["Mombasa port container terminal", "Dar es Salaam harbour cargo",
                   "container ship loading crane Africa"]),
    ("build",     ["construction", "pipeline", "keys", "groundbreaking", "refurbishment",
                   "development", "opened", "inaugurated", "new hotel", "rooms opening",
                   "investment", "signed", "brand launch"],
                  ["hotel construction site crane Africa", "new hotel building exterior Africa",
                   "resort under construction tropical"]),
    ("labour",    ["strike", "union", "staffing", "wages", "recruitment", "training",
                   "workforce", "graduates", "hospitality college", "chefs", "skills"],
                  ["hotel staff training hospitality school",
                   "hotel housekeeping staff at work", "chefs working hotel kitchen"]),
    ("policy",    ["gazette", "regulation", "licence", "permit fee", "advisory",
                   "parliament", "ministry", "directive", "circular", "compliance",
                   "visa", "eta", "immigration"],
                  ["government building parliament East Africa",
                   "passport immigration border control desk",
                   "official government gazette document"]),
    # ---------------------------------------------------------------- SCENERY
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


# ---------------------------------------------------------------- destination
# When no specific subject can be evidenced, a real photograph of the market the
# edition is about beats an abstract gradient. This is ordinary trade-press
# practice: the picture illustrates the DESTINATION, not the event. It stays
# honest because the photograph is real, licensed and credited -- the failure
# mode we care about is synthetic imagery implying footage of a real incident,
# and a licensed skyline implies nothing.
COUNTRY_MARKERS = {
    "KE": (["kenya", "nairobi", "mombasa", "\U0001F1F0\U0001F1EA", "knbs", "kws", "epra",
            "diani", "maasai mara", "jkia", "kenya airways"],
           ["Nairobi skyline Kenya", "Nairobi city Kenya", "Diani Beach Kenya",
            "Maasai Mara landscape Kenya"]),
    "UG": (["uganda", "kampala", "entebbe", "\U0001F1FA\U0001F1EC", "ubos", "uwa", "bwindi"],
           ["Kampala city Uganda", "Entebbe Lake Victoria Uganda",
            "Uganda landscape hills"]),
    "TZ": (["tanzania", "dar es salaam", "arusha", "\U0001F1F9\U0001F1FF", "serengeti",
            "kilimanjaro", "tanapa", "ngorongoro"],
           ["Dar es Salaam skyline Tanzania", "Serengeti plains Tanzania",
            "Mount Kilimanjaro Tanzania"]),
    "ZNZ": (["zanzibar", "stone town", "unguja", "nungwi", "ocgs"],
            ["Stone Town Zanzibar", "Nungwi beach Zanzibar",
             "Zanzibar dhow Indian Ocean"]),
    "RW": (["rwanda", "kigali", "\U0001F1F7\U0001F1FC", "rdb", "volcanoes national park",
            "nisr", "kwita izina"],
           ["Kigali skyline Rwanda", "Kigali city Rwanda",
            "Rwanda hills landscape"]),
}
# Regional catch-all when an edition is genuinely pan-EA.
REGIONAL_QUERIES = ["East Africa landscape", "Nairobi skyline Kenya",
                    "Serengeti plains Tanzania"]


def detect_market(text, lead=""):
    """Primary market for an edition, weighted to the lead. Returns a code or None."""
    lead = lead or text
    scores = {}
    for code, (markers, _q) in COUNTRY_MARKERS.items():
        scores[code] = (sum(1 for m in markers if m in text)
                        + 3 * sum(1 for m in markers if m in lead))
    # Zanzibar is a separate market in this product, but every Zanzibar story also
    # says "Tanzania", so TZ outscores it on raw counts and a Zanzibar beach piece
    # ends up under a photo of Dar es Salaam. Zanzibar wins its own stories.
    best = max(scores, key=lambda k: scores[k]) if scores else None
    if not best or scores[best] < 2:
        return None
    # ...but only against TZ. Overriding a genuine Uganda or Kenya winner would be
    # worse than the problem it fixes.
    if best == "TZ" and scores.get("ZNZ", 0) >= 2:
        return "ZNZ"
    return best


def destination_queries(text, lead=""):
    code = detect_market(text, lead)
    if code:
        return code, COUNTRY_MARKERS[code][1]
    return "EA", REGIONAL_QUERIES

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


# The item marker is normally written **1\ufe0f\u20e3 HEADLINE**. The anchored
# pattern could not see past the bold marks, so lead_text() fell back to the
# masthead for most editions -- and detect_topic() rejects any topic with no
# LEAD presence. That silently suppressed the hero on a large share of runs.
_LEAD_ITEM = re.compile(r"^\**\s*1\ufe0f?\u20e3\s*(.+?)\s*\**$", re.M)


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


PLACEHOLDER_KINDS = ("data-card", "illustration")


def _is_placeholder(entry):
    kind = (entry or {}).get("source_kind") or ""
    return kind in PLACEHOLDER_KINDS or str((entry or {}).get("title", "")).startswith("Data card")


def _is_data_card(entry):
    return _is_placeholder(entry)


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
    ap.add_argument("--destination-fallback", action="store_true",
                    help="for editions with no confident subject, use a licensed "
                         "photograph of the market instead of leaving a placeholder")
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
        _lead = lead_text(_md)
        hit = detect_topic(_md, _lead)
        if hit:
            topic, queries, score = hit
        elif a.destination_fallback:
            # No specific subject -- illustrate the MARKET with a real photograph.
            topic, queries = destination_queries(_md, _lead)
            topic, score = f"destination:{topic}", 0
        else:
            skipped_topic += 1
            print(f"  keep card  {eid}  (no confident visual subject)")
            continue

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
