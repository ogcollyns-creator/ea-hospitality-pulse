#!/usr/bin/env python3
"""
Assign a DISTINCT, licence-clear Wikimedia Commons photo to EVERY edition and
credit it automatically.

Runs on the build runner (Commons is unreachable from the Cowork sandbox).
Best-effort by design: any edition it cannot satisfy is simply left for
make_og_images.py to fill from the curated pool, so the site never breaks and
never shows a blank card.

    python3 fetch_edition_images.py   # -> img/editions/<id>.jpg + img/edition-credits.json
    python3 build_site.py             # heroes, cards and credits pick them up

Every image is CC0 / public-domain / CC-BY / CC-BY-SA from Wikimedia Commons;
author + licence + source are captured straight from the Commons API, so the
attribution rendered under each hero and on credits.html is correct by
construction.
"""
import os, io, json, time, hashlib, re, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, "img")
EDIMG = os.path.join(IMG, "editions")
API  = "https://commons.wikimedia.org/w/api.php"
UA   = "EAHospitalityPulse-image-fetch/1.0 (https://eahospitalitypulse.com; ceo@eahospitalitypulse.com)"
WIDTH = 1600

# theme -> (keywords to detect it in the edition text, Commons search query).
# First strongest keyword hit wins; queries are concrete because Commons search
# is literal. Add rows here to widen coverage.
TOPICS = [
    ("aviation",    ["airline","aviation","aircraft","jkia","kenya airways","rwandair","air tanzania","uganda airlines","route launch","direct flight","seat capacity","airlift","frequencies","load factor","widebody","airport","airfare"],
                     "airliner aircraft airport Africa"),
    ("gorilla",     ["gorilla","chimpanzee","bwindi","volcanoes national park","virunga","nyungwe","primate","golden monkey"],
                     "mountain gorilla Rwanda"),
    ("migration",   ["wildebeest","mara river","great migration","river crossing","maasai mara","the migration"],
                     "wildebeest migration Maasai Mara"),
    ("amboseli",    ["amboseli","elephant","tusker","tsavo"],
                     "elephants Amboseli Kilimanjaro"),
    ("kilimanjaro", ["kilimanjaro","uhuru peak","machame","marangu","trekking","mountaineering"],
                     "Mount Kilimanjaro Tanzania"),
    ("safari",      ["safari","serengeti","savannah","game drive","game reserve","ngorongoro","tarangire","big five","big cat","leopard","cheetah","lion","wildlife","conservancy"],
                     "Serengeti wildlife safari"),
    ("stonetown",   ["stone town","forodhani","old fort","spice tour","swahili architecture"],
                     "Stone Town Zanzibar"),
    ("beach",       ["diani","nungwi","kendwa","watamu","kilifi","malindi","dhow","coral reef","snorkel","white sand","beach","coast","resort","indian ocean","island"],
                     "Zanzibar beach Indian Ocean"),
    ("mice",        ["conference","convention","mice","summit","congress","expo","exhibition","delegates","business events","icca","trade show"],
                     "Kigali Convention Centre Rwanda"),
    ("kigali",      ["kigali","nyarugenge","rwandan capital","rwanda"],
                     "Kigali city skyline"),
    ("kampala",     ["kampala","entebbe","munyonyo","speke resort","pearl of africa","murchison","jinja","source of the nile","lake victoria"],
                     "Kampala city skyline"),
    ("nairobi",     ["nairobi","cbd","westlands","upper hill","gigiri","expressway","kilimani"],
                     "Nairobi city skyline"),
]
DEFAULT_QUERY = "East Africa savannah landscape"
ALLOWED_LIC = ("cc0", "public domain", "pdm", "cc by", "cc-by", "cc by-sa", "cc-by-sa", "attribution")
BAD_TITLE = ("map", "logo", "flag", "coat of arms", "seal", "diagram", "chart", "icon",
             "svg", "poster", "banner", "screenshot", ".pdf", "locator", "emblem",
             "graph", "timeline", "signature",
             # negative-tone imagery — wrong look for a hospitality brand
             "scrapheap", "scrap", "wreck", "wreckage", "crash", "abandoned",
             "derelict", "graveyard", "boneyard", "junkyard", "demolition",
             "demolished", "destroyed", "riot", "protest", "slum", "cemetery",
             "funeral", "disaster", "burnt", "burned",
             # infrastructure / sanitation / facility-documentation — not hospitality imagery
             "toilet", "cubicle", "uddt", "latrine", "sanitation", "sewer", "sewage",
             "drainage", "landfill", "dumpsite", "garbage", "rubbish", "compost",
             "borehole", "mortuary", "prison", "informal settlement", "roadworks",
             "construction site", "substation", "transformer", "quarry", "sludge",
             "manhole", "factory", "warehouse", "classroom", "kiosk")

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def _strip(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()

def topic_for(text):
    t = (text or "").lower()
    best, score = None, 0
    for key, kws, q in TOPICS:
        s = sum(t.count(k) for k in kws)
        if s > score:
            score, best = s, q
    return best  # None if nothing matched -> DEFAULT_QUERY

def search_candidates(query, limit=40):
    q = {"action":"query","format":"json","generator":"search",
         "gsrsearch":f"{query} filetype:bitmap","gsrnamespace":"6","gsrlimit":str(limit),
         "prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":str(WIDTH)}
    data = json.loads(_get(API + "?" + urllib.parse.urlencode(q)))
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for p in sorted(pages.values(), key=lambda x: x.get("index", 1e9)):
        ii = (p.get("imageinfo") or [None])[0]
        if not ii:
            continue
        title = p.get("title", "")[5:]  # strip "File:"
        w, h, mime = ii.get("width", 0), ii.get("height", 0), ii.get("mime", "")
        em = ii.get("extmetadata", {})
        lic = _strip(em.get("LicenseShortName", {}).get("value", "")).lower()
        tl = title.lower()
        if mime not in ("image/jpeg", "image/png"): continue
        if w < 1200 or h < 600:                     continue
        if w < h * 1.15:                            continue   # landscape only
        if not any(a in lic for a in ALLOWED_LIC):  continue
        if any(b in tl for b in BAD_TITLE):         continue
        out.append({"title": title,
                    "thumb": ii.get("thumburl") or ii.get("url"),
                    "descurl": ii.get("descriptionurl", "https://commons.wikimedia.org/wiki/File:" + title),
                    "artist": _strip(em.get("Artist", {}).get("value", "")) or "Unknown",
                    "license": _strip(em.get("LicenseShortName", {}).get("value", "")) or "See source",
                    "licenseurl": em.get("LicenseUrl", {}).get("value", "")})
    return out

def main(editions=None):
    if editions is None:
        d = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
        m = re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
        editions = json.loads(m.group(1)) if m else []
    os.makedirs(EDIMG, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow required: pip install pillow")
    # idempotent: load prior assignments, keep them, only fetch editions that
    # have no image yet — so builds are fast, polite to Commons, and stable.
    try:
        credits = json.load(open(os.path.join(IMG, "edition-credits.json"), encoding="utf-8"))
    except Exception:
        credits = {}
    cache = {}
    used = set(v.get("title") for v in credits.values() if v.get("title"))
    ok = fell = 0
    for e in sorted(editions, key=lambda e: e.get("id", "")):   # stable order
        eid = e["id"]
        if os.path.exists(os.path.join(EDIMG, eid + ".jpg")) and eid in credits:
            continue                                            # already assigned, keep stable
        text = e.get("summary", "") + " " + re.sub(r"<[^>]+>", " ", e.get("bodyHtml", ""))
        query = topic_for(text) or DEFAULT_QUERY
        try:
            if query not in cache:
                cache[query] = search_candidates(query); time.sleep(0.5)
            cands = cache[query]
        except Exception as ex:
            fell += 1; print(f"  search fail {eid}: {ex}"); continue
        pick = None
        if cands:
            start = int(hashlib.md5(eid.encode()).hexdigest(), 16) % len(cands)
            for i in range(len(cands)):
                c = cands[(start + i) % len(cands)]
                if c["title"] not in used:
                    pick = c; break
            if pick is None:
                pick = cands[start]                  # exhausted -> allow a reuse
        if not pick:
            fell += 1; print(f"  no candidate {eid} ({query}) -> pool fallback"); continue
        try:
            img = Image.open(io.BytesIO(_get(pick["thumb"]))).convert("RGB")
            if img.width > WIDTH:
                img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
            img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=85, optimize=True)
            used.add(pick["title"])
            credits[eid] = {"id": eid, "title": pick["title"], "artist": pick["artist"],
                            "license": pick["license"], "licenseurl": pick["licenseurl"],
                            "descurl": pick["descurl"]}
            ok += 1; print(f"  ok  {eid}.jpg <- {pick['title']} [{pick['license']}]")
            time.sleep(0.4)
        except Exception as ex:
            fell += 1; print(f"  dl fail {eid}: {ex}")
    json.dump(credits, open(os.path.join(IMG, "edition-credits.json"), "w", encoding="utf-8"), indent=1)
    print(f"\n{ok} edition images fetched, {fell} left to the curated pool.")

if __name__ == "__main__":
    main()
