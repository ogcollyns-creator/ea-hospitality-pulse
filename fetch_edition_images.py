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
import os, io, json, time, hashlib, re, sys, urllib.parse, urllib.request
import datetime as _dt

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

# ---- RECENCY GUARDRAIL ------------------------------------------------------
# The brief refuses to publish an undated fact; it should not publish an undated
# photo either. A candidate must state a capture date on Commons AND that date
# must fall inside MAX_AGE_YEARS. Undated files are rejected, not assumed fresh.
MAX_AGE_YEARS = 3
MIN_DATE = _dt.date.today() - _dt.timedelta(days=int(365.25 * MAX_AGE_YEARS))

# Queries appended after the topic query when the topic pool is exhausted by the
# age gate or the no-reuse rule. Ordered specific -> broad.
# Queries appended after the topic query when the topic pool is exhausted by the
# age gate or the no-reuse rule. Every one names a PLACE OR SUBJECT, never a bare
# country-plus-year: "Kenya 2024" matches an Olympic rugby fixture just as well as
# a landscape, and did exactly that before this list was rewritten.
WIDEN = [
    "Zanzibar beach coast", "Serengeti national park landscape",
    "Maasai Mara landscape", "Mount Kilimanjaro landscape",
    "Volcanoes National Park Rwanda", "Lake Victoria landscape",
    "Nairobi skyline cityscape", "Kigali cityscape",
    "Dar es Salaam waterfront", "Indian Ocean coast Tanzania",
    "Kenya national park scenery", "Uganda landscape scenery",
    "East Africa landscape", "African wildlife national park",
]
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
             "manhole", "factory", "warehouse", "classroom", "kiosk",
             # sport, competition and staged-event imagery — a rugby match is not
             # a hospitality hero, however recent the photograph
             "rugby", "olympic", "olympics", "football", "soccer", "cricket",
             "athletics", "marathon", "sevens", "tournament", "championship",
             "match ", "fixture", "stadium", "medal", "podium", "referee",
             "team photo", "squad", "portrait of", "headshot", "press conference",
             "conference room", "delegates", "ceremony", "parade", "protest march",
             "military", "soldier", "parliament", "election", "campaign rally")

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


def _parse_commons_date(em):
    """Best capture date for a Commons file, or None if it states none.

    Prefers DateTimeOriginal (when the photo was taken) over DateTime (when the
    file was touched). A year-only value is read as 1 July of that year — the
    midpoint, so a bare year neither flatters nor unfairly fails the gate.
    """
    for key in ("DateTimeOriginal", "DateTime"):
        raw = _strip((em.get(key) or {}).get("value", ""))
        if not raw:
            continue
        m = re.search(r"(\d{4})[-:/](\d{1,2})[-:/](\d{1,2})", raw)
        if m:
            y, mo, d = (int(x) for x in m.groups())
            try:
                return _dt.date(y, mo, d)
            except ValueError:
                pass
        m = re.search(r"\b(19|20)(\d{2})\b", raw)
        if m:
            y = int(m.group(0))
            if 1900 <= y <= _dt.date.today().year:
                return _dt.date(y, 7, 1)
    return None


def _sha(b):
    return hashlib.sha256(b).hexdigest()

def search_candidates(query, limit=80, sort=None):
    q = {"action":"query","format":"json","generator":"search",
         "gsrsearch":f"{query} filetype:bitmap","gsrnamespace":"6","gsrlimit":str(limit),
         "prop":"imageinfo","iiprop":"url|size|mime|extmetadata","iiurlwidth":str(WIDTH)}
    if sort:
        q["gsrsort"] = sort
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
        taken = _parse_commons_date(em)
        if taken is None:                           continue   # undated -> rejected
        if taken < MIN_DATE:                        continue   # older than MAX_AGE_YEARS
        out.append({"title": title,
                    "taken": taken.isoformat(),
                    "thumb": ii.get("thumburl") or ii.get("url"),
                    "descurl": ii.get("descriptionurl", "https://commons.wikimedia.org/wiki/File:" + title),
                    "artist": _strip(em.get("Artist", {}).get("value", "")) or "Unknown",
                    "license": _strip(em.get("LicenseShortName", {}).get("value", "")) or "See source",
                    "licenseurl": em.get("LicenseUrl", {}).get("value", "")})
    return out

def _load_editions():
    d = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
    m = re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
    return json.loads(m.group(1)) if m else []


def _existing_hashes(skip_id=None):
    """sha256 -> edition id, for every image already on disk."""
    out = {}
    if not os.path.isdir(EDIMG):
        return out
    for fn in os.listdir(EDIMG):
        if not fn.endswith(".jpg"):
            continue
        eid = fn[:-4]
        if eid == skip_id:
            continue
        try:
            with open(os.path.join(EDIMG, fn), "rb") as fh:
                out.setdefault(_sha(fh.read()), eid)
        except OSError:
            pass
    return out


def audit(fix=False, fix_legacy=False):
    """Report editions whose hero image breaks the guardrail.

    Three distinct faults, deliberately not lumped together:
      duplicate — byte-identical to another edition's image. Always a defect.
      stale     — credits record a capture date older than the gate.
      legacy    — assigned before the guardrail existed, so no date was recorded.
                  Not evidence of a bad image, only of an unverified one.

    --fix clears duplicates and stale entries. Legacy entries are left alone
    unless --fix-legacy is passed, because re-fetching the whole archive under a
    strict age gate would push most editions onto the small curated pool and
    make the archive look worse, not better.
    """
    try:
        credits = json.load(open(os.path.join(IMG, "edition-credits.json"), encoding="utf-8"))
    except Exception:
        credits = {}
    seen, dupes, legacy, stale = {}, [], [], []
    for fn in sorted(os.listdir(EDIMG)) if os.path.isdir(EDIMG) else []:
        if not fn.endswith(".jpg"):
            continue
        eid = fn[:-4]
        with open(os.path.join(EDIMG, fn), "rb") as fh:
            h = _sha(fh.read())
        if h in seen:
            dupes.append((eid, seen[h]))
        else:
            seen[h] = eid
        taken = (credits.get(eid) or {}).get("taken")
        if not taken:
            legacy.append(eid)
            continue
        try:
            if _dt.date.fromisoformat(taken) < MIN_DATE:
                stale.append((eid, taken))
        except ValueError:
            legacy.append(eid)

    print(f"AUDIT — gate: capture date on or after {MIN_DATE.isoformat()} "
          f"(MAX_AGE_YEARS={MAX_AGE_YEARS})")
    print(f"  duplicate images      : {len(dupes)}")
    for eid, orig in dupes:
        print(f"      {eid}  ==  {orig}")
    print(f"  stale (dated too old) : {len(stale)}")
    for eid, t in stale:
        print(f"      {eid}  taken {t}")
    print(f"  legacy (no date on record): {len(legacy)}  [pre-guardrail; not auto-cleared]")

    targets = [e for e, _ in dupes] + [e for e, _ in stale]
    if fix_legacy:
        targets += legacy
    if (fix or fix_legacy) and targets:
        for eid in dict.fromkeys(targets):
            fp = os.path.join(EDIMG, eid + ".jpg")
            if os.path.exists(fp):
                os.remove(fp)
            credits.pop(eid, None)
        json.dump(credits, open(os.path.join(IMG, "edition-credits.json"), "w",
                                encoding="utf-8"), indent=1)
        print(f"\n  cleared {len(dict.fromkeys(targets))} entries — next build re-fetches them.")
    return targets


def main(editions=None, refresh=()):
    if editions is None:
        editions = _load_editions()
    os.makedirs(EDIMG, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow required: pip install pillow")
    try:
        credits = json.load(open(os.path.join(IMG, "edition-credits.json"), encoding="utf-8"))
    except Exception:
        credits = {}

    # forced refresh: drop the assignment so the loop below re-picks it
    for eid in refresh:
        credits.pop(eid, None)
        fp = os.path.join(EDIMG, eid + ".jpg")
        if os.path.exists(fp):
            os.remove(fp)
        print(f"  refresh requested: {eid}")

    cache = {}
    used = set(v.get("title") for v in credits.values() if v.get("title"))
    hashes = _existing_hashes()
    ok = fell = 0
    for e in sorted(editions, key=lambda e: e.get("id", "")):   # stable order
        eid = e["id"]
        if os.path.exists(os.path.join(EDIMG, eid + ".jpg")) and eid in credits:
            continue                                            # already compliant, keep stable
        text = e.get("summary", "") + " " + re.sub(r"<[^>]+>", " ", e.get("bodyHtml", ""))
        topic = topic_for(text) or DEFAULT_QUERY

        # Specific first, then progressively broader. Within each query, try the
        # default relevance ranking and then newest-uploaded, which surfaces the
        # recent files the age gate needs.
        plans = [(topic, None), (topic, "create_timestamp_desc"), (DEFAULT_QUERY, None)]
        plans += [(w, "create_timestamp_desc") for w in WIDEN]

        pick = None
        for query, sort in plans:
            key = (query, sort)
            if key not in cache:
                try:
                    cache[key] = search_candidates(query, sort=sort)
                    time.sleep(0.5)
                except Exception as ex:
                    print(f"  search fail {eid} [{query}]: {ex}")
                    cache[key] = []
            cands = [c for c in cache[key] if c["title"] not in used]
            if not cands:
                continue
            start = int(hashlib.md5(eid.encode()).hexdigest(), 16) % len(cands)
            for i in range(len(cands)):
                c = cands[(start + i) % len(cands)]
                try:
                    blob = _get(c["thumb"])
                except Exception:
                    continue
                h = _sha(blob)
                if h in hashes:                 # byte-identical to another edition
                    used.add(c["title"])        # never offer it again either
                    continue
                pick, pick_blob, pick_hash = c, blob, h
                break
            if pick:
                break

        if not pick:
            # NO SILENT REUSE. Fall through to the curated pool in make_og_images.
            fell += 1
            print(f"  no compliant candidate {eid} (age gate {MIN_DATE}) -> curated pool")
            continue
        try:
            img = Image.open(io.BytesIO(pick_blob)).convert("RGB")
            if img.width > WIDTH:
                img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
            img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=85, optimize=True)
            with open(os.path.join(EDIMG, eid + ".jpg"), "rb") as fh:
                hashes[_sha(fh.read())] = eid
            used.add(pick["title"])
            credits[eid] = {"id": eid, "title": pick["title"], "artist": pick["artist"],
                            "license": pick["license"], "licenseurl": pick["licenseurl"],
                            "descurl": pick["descurl"], "taken": pick["taken"]}
            ok += 1
            print(f"  ok  {eid}.jpg <- {pick['title']} [{pick['license']}] taken {pick['taken']}")
            time.sleep(0.4)
        except Exception as ex:
            fell += 1
            print(f"  dl fail {eid}: {ex}")
    json.dump(credits, open(os.path.join(IMG, "edition-credits.json"), "w", encoding="utf-8"), indent=1)
    print(f"\n{ok} edition images fetched, {fell} left to the curated pool.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--audit" in args:
        audit(fix="--fix" in args, fix_legacy="--fix-legacy" in args)
    else:
        refresh = []
        if "--refresh" in args:
            refresh = [a for a in args[args.index("--refresh") + 1:] if not a.startswith("--")]
        main(refresh=refresh)
