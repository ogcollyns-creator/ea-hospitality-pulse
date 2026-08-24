#!/usr/bin/env python3
"""
Extra hero-image sources layered around the Wikimedia fetch (fetch_edition_images.py).

  --press-kit    Assign a HUMAN-VETTED tourism-board / brand press-kit image to any
                 edition it matches, from img/press-kit/registry.json. Run BEFORE
                 fetch_edition_images.py so a matched edition keeps the press-kit shot.

  --ai-fallback  Generate an on-brand, rights-free illustration for any edition that
                 STILL has no hero after the Wikimedia pass. Run AFTER
                 fetch_edition_images.py. Uses a text-to-image API when IMAGE_API_KEY
                 is set, otherwise a deterministic Pillow illustration. It is never a
                 photograph of a real, named place — it is labelled an
                 'AI-assisted illustration'.

Both passes are best-effort and write:
  * img/editions/<edition-id>.jpg           the raw hero image
  * img/edition-credits.json                a credit entry carrying a 'source' field
so build_site.py and .github/scripts/post_telegram.py attribute them correctly.
See docs/image-policy.md. Any failure leaves the edition for the next source in the
chain, so the site never breaks and never shows an unattributed image.
"""
import os, re, json, sys, shutil, hashlib

HERE  = os.path.dirname(os.path.abspath(__file__))
IMG   = os.path.join(HERE, "img")
EDIMG = os.path.join(IMG, "editions")
PKDIR = os.path.join(IMG, "press-kit")
PKREG = os.path.join(PKDIR, "registry.json")
CREDITS_PATH = os.path.join(IMG, "edition-credits.json")
AIDIR = os.path.join(IMG, "ai")
WIDTH = 1600

# Brand palette / fonts (mirrors make_og_images.py).
TEAL=(10,79,72); TEAL2=(15,109,99); GOLD=(200,137,47); SAND=(246,241,231); WHITE=(255,255,255)
FONT  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---------- shared helpers ----------------------------------------------------
def _load_editions():
    try:
        d = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
        m = re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
        return json.loads(m.group(1)) if m else []
    except Exception as e:
        print(f"  hero_extra: could not load editions: {e}")
        return []

def _load_credits():
    try:
        return json.load(open(CREDITS_PATH, encoding="utf-8"))
    except Exception:
        return {}

def _save_credits(credits):
    tmp = CREDITS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(credits, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, CREDITS_PATH)

def _has_hero(eid, credits):
    return os.path.exists(os.path.join(EDIMG, eid + ".jpg")) and eid in credits

def _edition_text(e):
    return (e.get("summary","") + " " +
            re.sub(r"<[^>]+>", " ", e.get("bodyHtml",""))).lower()

def _headline(e):
    return (e.get("title") or e.get("edition") or "East Africa hospitality").strip()


# ---------- press-kit pass ----------------------------------------------------
def press_kit_pass():
    """Assign vetted press-kit images to matching editions that lack a hero."""
    try:
        reg = json.load(open(PKREG, encoding="utf-8"))
    except Exception as e:
        print(f"  press-kit: no usable registry ({e}) — skipping"); return
    images = reg.get("images", [])
    if not images:
        print("  press-kit: registry empty — nothing to assign (add vetted images to img/press-kit/)"); return

    try:
        from PIL import Image
    except ImportError:
        print("  press-kit: Pillow missing — skipping"); return

    editions = _load_editions()
    credits  = _load_credits()
    used = {v.get("title") for v in credits.values() if v.get("source_kind") == "press-kit"}
    assigned = 0

    for e in sorted(editions, key=lambda e: e.get("id","")):
        eid = e["id"]
        if _has_hero(eid, credits):
            continue
        text = _edition_text(e)
        best, best_score = None, 0
        for im in images:
            fpath = os.path.join(PKDIR, im.get("file",""))
            if not im.get("file") or not os.path.exists(fpath):
                continue
            if im.get("file") in used:
                continue                                   # one edition per image
            score = 0
            if eid in (im.get("editions") or []):
                score = 999                                # explicit pin wins
            else:
                score = sum(1 for t in (im.get("tags") or []) if t.lower() in text)
            if score > best_score:
                best, best_score = im, score
        if not best or best_score == 0:
            continue
        try:
            src = os.path.join(PKDIR, best["file"])
            img = Image.open(src).convert("RGB")
            if img.width > WIDTH:
                img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
            img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=85, optimize=True)
        except Exception as ex:
            print(f"  press-kit: failed to place {best.get('file')} for {eid}: {ex}"); continue
        credits[eid] = {
            "id": eid,
            "title": best["file"],
            "artist": best.get("artist") or best.get("source") or "Press kit",
            "source": best.get("source") or "Press kit",
            "license": best.get("license") or "Editorial use — press kit (grant logged)",
            "licenseurl": best.get("licenseurl") or "",
            "descurl": best.get("descurl") or "",
            "grant": best.get("grant") or "",
            "source_kind": "press-kit",
        }
        used.add(best["file"]); assigned += 1
        print(f"  press-kit: {eid}.jpg <- {best['file']} [{credits[eid]['source']}]")
    _save_credits(credits)
    print(f"  press-kit: assigned {assigned} edition(s)")


# ---------- AI / illustration fallback ---------------------------------------
_SCENES = [
    (("safari","serengeti","migration","wildebeest","big five","game drive","conservancy"),
     "a wide East African savannah at golden hour, acacia trees and distant plains"),
    (("gorilla","bwindi","volcanoes","virunga","primate","chimp"),
     "misty forested volcanic mountains of the Albertine Rift at dawn"),
    (("beach","zanzibar","diani","coast","nungwi","indian ocean","island","dhow"),
     "a calm Indian Ocean coastline with a wooden dhow and palm shade"),
    (("kigali","nairobi","kampala","city","skyline","cbd","convention","mice","conference"),
     "a clean modern East African city skyline under warm evening light"),
    (("aviation","airline","aircraft","airport","route","seat","airlift","flight"),
     "an airliner on an African apron at sunrise, warm sky, no visible livery"),
    (("kilimanjaro","uhuru","trek","mountain"),
     "a snow-capped equatorial mountain rising above golden plains"),
]
_DEFAULT_SCENE = "warm East African landscape at golden hour, layered hills and open sky"

def _scene_for(text):
    for keys, scene in _SCENES:
        if any(k in text for k in keys):
            return scene
    return _DEFAULT_SCENE

def _api_image(prompt):
    """Best-effort text-to-image via an OpenAI-compatible endpoint. Returns JPEG
    bytes or None. Controlled by env: IMAGE_API_KEY (required to attempt),
    IMAGE_API_URL, IMAGE_API_MODEL. Any problem -> None (caller draws instead)."""
    key = os.environ.get("IMAGE_API_KEY", "").strip()
    if not key:
        return None
    import urllib.request, base64
    url   = os.environ.get("IMAGE_API_URL",  "https://api.openai.com/v1/images/generations")
    model = os.environ.get("IMAGE_API_MODEL", "gpt-image-1")
    payload = json.dumps({"model": model, "prompt": prompt,
                          "size": "1536x1024", "n": 1}).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())
        d0 = (data.get("data") or [{}])[0]
        if d0.get("b64_json"):
            return base64.b64decode(d0["b64_json"])
        if d0.get("url"):
            with urllib.request.urlopen(d0["url"], timeout=120) as ir:
                return ir.read()
    except Exception as ex:
        print(f"  ai: image API failed ({ex}); using illustration")
    return None

def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def _illustration(eid, headline, scene):
    """Deterministic on-brand illustration (no network). 1536x1024 landscape."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1536, 1024
    seed = int(hashlib.sha256(eid.encode()).hexdigest(), 16)
    # deterministic accent shift so cards aren't identical
    shift = seed % 30
    top = (TEAL[0], min(TEAL[1]+shift, 120), min(TEAL[2]+shift, 120))
    bot = (max(TEAL[0]-4,0), max(TEAL[1]-24,0), max(TEAL[2]-22,0))
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        r = round(top[0]*(1-t) + bot[0]*t)
        g = round(top[1]*(1-t) + bot[1]*t)
        b = round(top[2]*(1-t) + bot[2]*t)
        for x in range(W):
            px[x, y] = (r, g, b)
    d = ImageDraw.Draw(img)
    # abstract "horizon + hills" motif, deterministic
    base = int(H*0.66)
    for i, amp in enumerate((90, 60, 34)):
        off = (seed >> (i*4)) % 120
        col = (top[0], top[1]+18+i*10, top[2]+16+i*8)
        pts = [(0, H)]
        for x in range(0, W+1, 24):
            import math
            yv = base + i*70 + int(amp*math.sin((x+off)/ (150+i*40)))
            pts.append((x, yv))
        pts.append((W, H))
        d.polygon(pts, fill=col)
    # sun/moon disc
    cx = int(W*0.78); cy = int(H*0.30); rr = 70
    d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=GOLD)
    try:
        fk = ImageFont.truetype(FONTB, 30)
        fh = ImageFont.truetype(FONTB, 64)
        ff = ImageFont.truetype(FONT, 24)
    except Exception:
        fk = fh = ff = ImageFont.load_default()
    d.text((70, 70), "EA HOSPITALITY PULSE", font=fk, fill=SAND)
    d.line((70, 118, 70+260, 118), fill=GOLD, width=4)
    lines = _wrap(d, headline, fh, W-140)[:4]
    y = int(H*0.40)
    for ln in lines:
        d.text((70, y), ln, font=fh, fill=WHITE); y += 74
    tag = "AI-ASSISTED ILLUSTRATION · not a photograph"
    tw = d.textlength(tag, font=ff)
    d.rectangle((70, H-70, 70+tw+28, H-30), fill=(0,0,0))
    d.text((84, H-64), tag, font=ff, fill=SAND)
    os.makedirs(EDIMG, exist_ok=True)
    img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=88, optimize=True)

def ai_fallback_pass():
    """Generate a rights-free hero for any edition still missing one."""
    try:
        import PIL  # noqa
    except ImportError:
        print("  ai: Pillow missing — skipping"); return
    editions = _load_editions()
    credits  = _load_credits()
    made = 0
    for e in sorted(editions, key=lambda e: e.get("id","")):
        eid = e["id"]
        if _has_hero(eid, credits):
            continue
        text = _edition_text(e)
        scene = _scene_for(text)
        headline = _headline(e)
        prompt = (f"Editorial illustration for a hospitality brief. Scene: {scene}. "
                  f"Warm, painterly, calm, no text, no logos, no watermarks, "
                  f"no real people, wide 3:2 aspect.")
        blob = _api_image(prompt)
        try:
            if blob:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(blob)).convert("RGB")
                if im.width > WIDTH:
                    im = im.resize((WIDTH, round(im.height*WIDTH/im.width)), Image.LANCZOS)
                os.makedirs(EDIMG, exist_ok=True)
                im.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=88, optimize=True)
                kind_src = "AI-generated (text-to-image)"
            else:
                _illustration(eid, headline, scene)
                kind_src = "AI-assisted illustration"
        except Exception as ex:
            print(f"  ai: failed for {eid}: {ex}"); continue
        credits[eid] = {
            "id": eid,
            "title": "AI-assisted illustration",
            "artist": "EA Hospitality Pulse",
            "source": kind_src,
            "license": "Original artwork — no third-party rights",
            "licenseurl": "",
            "descurl": "",
            "source_kind": "ai",
        }
        made += 1
        print(f"  ai: {eid}.jpg <- {kind_src}")
    _save_credits(credits)
    print(f"  ai: generated {made} edition hero(es)")


# ---------- Openverse pass (broad public-image pool, credited) ---------------
# Openverse (openverse.org, a Creative Commons / WordPress project) aggregates
# CC0, public-domain and CC-BY/BY-SA images from Flickr, Wikimedia, museums,
# Nappy, Rawpixel and more — a far larger pool than Wikimedia alone. Every result
# carries creator, source, licence and a landing URL, so attribution is exact.
# Runs BEFORE the Wikimedia fetch: for any edition lacking a hero it tries the
# per-edition image_queries.json subject first, then a headline-derived query.
OPENVERSE_API = "https://api.openverse.org/v1/images/"
OV_LICENSES = "cc0,pdm,by,by-sa"   # commercial-safe only (no NC/ND)

def _load_overrides():
    try:
        return json.load(open(os.path.join(HERE, "image_queries.json"), encoding="utf-8"))
    except Exception:
        return {}

def _openverse_search(query):
    import urllib.request, urllib.parse
    q = urllib.parse.urlencode({
        "q": query, "license": OV_LICENSES, "size": "large",
        "aspect_ratio": "wide", "page_size": "20", "mature": "false"})
    req = urllib.request.Request(OPENVERSE_API + "?" + q,
        headers={"User-Agent": "EAHospitalityPulse/1.0 (https://eahospitalitypulse.com)"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode()).get("results", []) or []
    except Exception as ex:
        print(f"  openverse: search failed [{query}]: {ex}")
        return []

def openverse_pass():
    """Assign a broad-pool, credited Openverse image to any edition without a hero."""
    try:
        from PIL import Image
    except ImportError:
        print("  openverse: Pillow missing — skipping"); return
    import urllib.request, io
    editions  = _load_editions()
    credits   = _load_credits()
    overrides = _load_overrides()
    used = {v.get("descurl") for v in credits.values() if v.get("descurl")}
    got = 0
    for e in sorted(editions, key=lambda e: e.get("id","")):
        eid = e["id"]
        if _has_hero(eid, credits):
            continue
        queries = overrides.get(eid) or [ (_headline(e) + " East Africa").strip(),
                                          "East Africa tourism landscape" ]
        picked = None
        for query in queries:
            for c in _openverse_search(query):
                url = c.get("url")
                w, h = c.get("width") or 0, c.get("height") or 0
                if not url or c.get("foreign_landing_url") in used:
                    continue
                if w and h and (w < 1200 or w < h * 1.15):
                    continue                      # landscape, large enough
                picked = c; break
            if picked:
                break
        if not picked:
            continue
        try:
            req = urllib.request.Request(picked["url"],
                headers={"User-Agent": "EAHospitalityPulse/1.0 (+https://eahospitalitypulse.com)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                blob = r.read()
            im = Image.open(io.BytesIO(blob)).convert("RGB")
            if im.width < 1200 or im.width < im.height * 1.15:
                continue
            if im.width > WIDTH:
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
            os.makedirs(EDIMG, exist_ok=True)
            im.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=85, optimize=True)
        except Exception as ex:
            print(f"  openverse: fetch failed for {eid}: {ex}"); continue
        prov = picked.get("source") or picked.get("provider") or "Openverse"
        credits[eid] = {
            "id": eid,
            "title": picked.get("title") or query,
            "artist": picked.get("creator") or prov,
            "source": f"Openverse · {prov}",
            "license": (picked.get("license","").upper() + " " + (picked.get("license_version") or "")).strip() or "See source",
            "licenseurl": picked.get("license_url") or "",
            "descurl": picked.get("foreign_landing_url") or picked.get("url") or "",
            "source_kind": "openverse",
        }
        used.add(credits[eid]["descurl"]); got += 1
        print(f"  openverse: {eid}.jpg <- {credits[eid]['title'][:50]} [{credits[eid]['source']}]")
    _save_credits(credits)
    print(f"  openverse: assigned {got} edition(s)")



# ---------- editorial / news-photo pass (Google-search-sourced, unlicensed) --
# Curated, hand-verified picks from a news/web image search (Google Images or
# equivalent) for a SPECIFIC edition id. Unlike press-kit (local vetted files)
# and Openverse (CC-licensed pool), these are direct hotlinks to a publisher's
# image, fetched at build time and credited to the ORIGINAL outlet/photographer
# for transparency — but carry NO reuse licence. Entries are added by hand
# (img/editorial-picks.json) after a human/agent search confirms the photo is
# genuinely on-topic; there is no live scraping in CI. An explicit pin here
# always wins over every other source, including an existing hero, so it is
# also the correction mechanism for a wrong automatic pick.
EDPICKS = os.path.join(IMG, "editorial-picks.json")

def _load_editorial_picks():
    try:
        return json.load(open(EDPICKS, encoding="utf-8"))
    except Exception as e:
        print(f"  editorial: no usable picks file ({e}) — skipping"); return {}

def editorial_pass():
    """Assign a hand-picked, web/Google-search-sourced photo to any edition
    named in img/editorial-picks.json. Always overrides — this is the manual
    correction channel, so a pin must be able to replace a bad automatic hero."""
    picks = _load_editorial_picks()
    if not picks:
        return
    try:
        from PIL import Image
    except ImportError:
        print("  editorial: Pillow missing — skipping"); return
    import urllib.request, io
    credits = _load_credits()
    done = 0
    for eid, pick in picks.items():
        url = pick.get("url")
        if not url:
            continue
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; EAHospitalityPulse/1.0; "
                              "+https://eahospitalitypulse.com)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                blob = r.read()
            im = Image.open(io.BytesIO(blob)).convert("RGB")
            if im.width > WIDTH:
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
            os.makedirs(EDIMG, exist_ok=True)
            im.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=88, optimize=True)
        except Exception as ex:
            print(f"  editorial: failed to fetch {eid} <- {url}: {ex}"); continue
        credits[eid] = {
            "id": eid,
            "title": pick.get("title") or eid,
            "artist": pick.get("artist") or pick.get("outlet") or "Unknown",
            "source": pick.get("outlet") or "Web/Google Images search",
            "license": "Editorial use — sourced via web/Google Images search; "
                       "no reuse licence granted, credited to original publisher",
            "licenseurl": "",
            "descurl": pick.get("descurl") or url,
            "source_kind": "editorial",
        }
        done += 1
        print(f"  editorial: {eid}.jpg <- {pick.get('outlet','?')} [{url[:70]}]")
    _save_credits(credits)
    print(f"  editorial: assigned {done} edition(s)")

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--editorial" in args:
        editorial_pass()
    if "--press-kit" in args:
        press_kit_pass()
    if "--openverse" in args:
        openverse_pass()
    if "--ai-fallback" in args:
        ai_fallback_pass()
    if not args:
        print("usage: hero_extra.py [--editorial] [--press-kit] [--openverse] [--ai-fallback]")
