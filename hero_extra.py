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
import os, re, json, sys, shutil, hashlib, io

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

# Heroes that are placeholders rather than pictures. A pass running with
# replace_cards=True is allowed to take these over; a real photograph or a vetted
# press-kit image is never overwritten.
_PLACEHOLDER_KINDS = ("data-card", "illustration")


def _has_hero(eid, credits, replace_cards=False):
    """True when the edition already has a hero this pass must not touch.

    Without replace_cards this is 'any hero at all', which is why the AI pass
    silently did nothing for weeks: every edition already carried a data card
    from an earlier run, so reordering the workflow changed nothing on its own.
    """
    if not (os.path.exists(os.path.join(EDIMG, eid + ".jpg")) and eid in credits):
        return False
    if replace_cards:
        kind = (credits.get(eid) or {}).get("source_kind") or ""
        if kind in _PLACEHOLDER_KINDS:
            return False          # a placeholder is fair game
    return True

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
        if _has_hero(eid, credits, replace_cards):
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

# ---------------------------------------------------------------- AI guardrails
# House style is PHOTOREALISTIC (owner decision, 7 Sep 2026), disclosed in the
# credit line under every hero. That raises the stakes on subject matter rather
# than lowering them: a synthetic photograph of generic savannah is decoration,
# but a synthetic photograph of a real incident is fabricated evidence.
#
# So these editions never get a generated hero. They fall through to the data
# card, which cannot misrepresent anything. The test is not "is the topic
# sensitive" but "would a photorealistic image imply we have footage of a real
# event we do not have footage of".
_NO_AI_SUBJECTS = (
    # incidents and casualties
    "crash", "accident", "collision", "wreck", "fatal", "death", "died", "killed",
    "injur", "casualt", "funeral", "mourn",
    # unrest and security
    "strike", "protest", "riot", "unrest", "clash", "attack", "terror", "abduct",
    "kidnap", "shooting", "gunmen", "militant", "police", "arrest", "raid",
    # health emergencies
    "ebola", "outbreak", "epidemic", "cholera", "dengue", "mpox", "quarantine",
    "patient", "ward", "morgue", "infect",
    # legal and political process
    "court", "hearing", "petition", "ruling", "judge", "tribunal", "lawsuit",
    "parliament", "impeach", "election", "ballot",
    # named-entity depiction risks
    "president", "minister", "ceo resign",
)


# Scanning the whole edition blocks almost everything: a market brief mentions
# "police" or "court" in a passing context line most days, and one incidental hit
# should not veto the hero. The hero stands for the LEAD story, so the lead is what
# gets judged -- plus a dominance check, so an edition genuinely about an outbreak
# is still caught when its headline is oblique.
_BODY_DOMINANCE = 4


def _ai_lead_text(md):
    """Headline area of an edition: first numbered item plus the opening lines."""
    parts = []
    m = re.search(r"^1\ufe0f\u20e3\s*(.+)$", md or "", re.M)
    if m:
        parts.append(m.group(1))
    parts.append(re.split(r"\n\u2501{3,}", md or "", 1)[0][:600])
    return " ".join(parts).lower()


def ai_subject_blocked(text, lead=None):
    """Terms that veto a photorealistic hero, or [] when generation is safe.

    Blocks when the subject is in the LEAD, or when it dominates the body.
    """
    t = (text or "").lower()
    lead = _ai_lead_text(text) if lead is None else (lead or "").lower()
    lead_hits = {w for w in _NO_AI_SUBJECTS if w in lead}
    body_hits = {w for w in _NO_AI_SUBJECTS if w in t}
    if lead_hits:
        return sorted(lead_hits)
    if len(body_hits) >= _BODY_DOMINANCE:
        return sorted(body_hits)
    return []


def build_ai_prompt(scene):
    """Photorealistic house style, with the depiction limits baked in."""
    return (
        "A photorealistic editorial photograph for a hospitality market-intelligence "
        f"brief. Scene: {scene}. "
        "Natural light, documentary travel-photography style, shallow depth of field, "
        "wide 3:2 composition, high detail. "
        "STRICT: no people's faces and no identifiable individuals; no real company "
        "logos, airline liveries, brand marks or signage; no text, captions, "
        "watermarks or numbers anywhere in the image; no depiction of any specific "
        "real-world news event, incident, protest, crash or medical setting; no "
        "documents, screens or charts. Generic location, not a named landmark."
    )

def _scene_for(text):
    for keys, scene in _SCENES:
        if any(k in text for k in keys):
            return scene
    return _DEFAULT_SCENE

# Model -> the size that model actually accepts. Getting this wrong is a 400,
# and until now a 400 was swallowed and reported as "using illustration".
_MODEL_SIZES = {
    "gpt-image-1": "1536x1024",
    "dall-e-3":    "1792x1024",
    "dall-e-2":    "1024x1024",
}
_API_DIAG = []          # human-readable notes from the last run, for the log


def _api_error_detail(ex):
    """Pull the API's own message out of an HTTPError body.

    urllib raises HTTPError whose str() is only 'HTTP Error 403: Forbidden'. The
    reason lives in the JSON body -- e.g. 'Your organization must be verified to
    use the model gpt-image-1'. Swallowing that is why this failed silently for
    days, so we read the body and print it.
    """
    body = ""
    try:
        body = ex.read().decode("utf-8", "replace")[:800]
    except Exception:
        pass
    code = msg = ""
    try:
        j = json.loads(body)
        err = j.get("error") or {}
        code = err.get("code") or err.get("type") or ""
        msg = err.get("message") or ""
    except Exception:
        msg = body
    status = getattr(ex, "code", "?")
    return f"HTTP {status}" + (f" [{code}]" if code else "") + (f": {msg}" if msg else "")


def _api_image(prompt, _models=None):
    """Text-to-image via an OpenAI-compatible endpoint. Returns JPEG bytes or None.

    env: IMAGE_API_KEY (required), IMAGE_API_URL, IMAGE_API_MODEL.
    Tries the configured model, then falls back through the others -- gpt-image-1
    requires organisation verification on OpenAI and 403s without it, which should
    degrade to dall-e-3 rather than to no image at all.
    """
    import urllib.request, urllib.error, base64
    key = os.environ.get("IMAGE_API_KEY", "").strip()
    if not key:
        _API_DIAG.append("IMAGE_API_KEY not set — no generation attempted")
        return None

    url = os.environ.get("IMAGE_API_URL", "https://api.openai.com/v1/images/generations")
    first = os.environ.get("IMAGE_API_MODEL", "gpt-image-1").strip()
    models = _models or ([first] + [m for m in ("dall-e-3", "dall-e-2") if m != first])

    for model in models:
        size = _MODEL_SIZES.get(model, "1024x1024")
        body = {"model": model, "prompt": prompt[:3900], "size": size, "n": 1}
        if model.startswith("dall-e"):
            body["response_format"] = "b64_json"   # gpt-image-1 always returns b64
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            d0 = (data.get("data") or [{}])[0]
            if d0.get("b64_json"):
                _API_DIAG.append(f"{model}: ok")
                return base64.b64decode(d0["b64_json"])
            if d0.get("url"):
                with urllib.request.urlopen(d0["url"], timeout=180) as ir:
                    _API_DIAG.append(f"{model}: ok (via url)")
                    return ir.read()
            _API_DIAG.append(f"{model}: response had no image payload")
        except urllib.error.HTTPError as ex:
            detail = _api_error_detail(ex)
            _API_DIAG.append(f"{model}: {detail}")
            print(f"  ai: {model} failed — {detail}")
            # auth/quota problems will not be fixed by trying another model
            if getattr(ex, "code", 0) in (401, 429) or "billing" in detail.lower():
                break
        except Exception as ex:
            _API_DIAG.append(f"{model}: {type(ex).__name__}: {ex}")
            print(f"  ai: {model} failed — {type(ex).__name__}: {ex}")
    return None


def check_image_api():
    """Preflight: report exactly why generation is or is not working.

    Never prints the key. Prints its length and last 4 characters only, which is
    enough to tell 'not set' from 'set but wrong' without leaking anything.
    """
    key = os.environ.get("IMAGE_API_KEY", "").strip()
    url = os.environ.get("IMAGE_API_URL", "https://api.openai.com/v1/images/generations")
    model = os.environ.get("IMAGE_API_MODEL", "gpt-image-1")
    print("— image API preflight —")
    if not key:
        print("  IMAGE_API_KEY: NOT SET")
        print("  -> add it at Settings > Secrets and variables > Actions.")
        return 1
    print(f"  IMAGE_API_KEY: set ({len(key)} chars, ends '{key[-4:]}')")
    print(f"  endpoint: {url}")
    print(f"  model:    {model} (falls back to dall-e-3, dall-e-2)")
    blob = _api_image("A calm empty landscape at golden hour, no text, no people.")
    for note in _API_DIAG:
        print(f"  {note}")
    if blob:
        print(f"  RESULT: generation WORKS ({len(blob)} bytes)")
        return 0
    print("  RESULT: generation FAILED — see the messages above.")
    print("  Common causes: gpt-image-1 needs organisation verification "
          "(platform.openai.com/settings/organization/general); "
          "401 = bad key; 429 = no credit or rate limit.")
    return 1


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
    """Deterministic, TEXT-FREE on-brand artwork (no network). 1536x1024 landscape.

    Nothing is written into this image on purpose. It is the in-page hero, and the
    page already carries the masthead, the edition chip and the headline in HTML
    directly beneath it -- so any text baked in here is read twice and looks like a
    mistake ("Evening Wrap" sitting above a slab that says Evening Wrap). Disclosure
    moved to the credit line under the hero, which now reads "Illustration:" and is
    where a reader looks for provenance anyway.

    Deterministic from the edition id, so every edition gets its own composition and
    the archive does not look like one image repeated ninety times.
    """
    from PIL import Image, ImageDraw, ImageFilter
    import math
    W, H = 1536, 1024
    seed = int(hashlib.sha256(eid.encode()).hexdigest(), 16)

    # --- sky gradient, hue nudged per edition -----------------------------
    shift = seed % 34
    top = (TEAL[0], min(TEAL[1] + shift, 124), min(TEAL[2] + shift, 122))
    bot = (max(TEAL[0] - 5, 0), max(TEAL[1] - 26, 0), max(TEAL[2] - 24, 0))
    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            round(top[0]*(1-t) + bot[0]*t),
            round(top[1]*(1-t) + bot[1]*t),
            round(top[2]*(1-t) + bot[2]*t)))

    # --- sun/moon, placed per edition, sitting BEHIND the ridgelines -------
    cx = int(W * (0.60 + ((seed >> 8) % 28) / 100.0))
    cy = int(H * (0.20 + ((seed >> 12) % 14) / 100.0))
    rr = 62 + (seed >> 16) % 26
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((cx-rr*3, cy-rr*3, cx+rr*3, cy+rr*3), fill=(60, 40, 12))
    img = Image.blend(img, Image.blend(img, glow, 0.0), 0.0)
    d = ImageDraw.Draw(img)
    d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=GOLD)

    # --- four layered ridgelines, back to front, each lighter -------------
    base = int(H * 0.56)
    for i, amp in enumerate((104, 74, 48, 30)):
        off = (seed >> (i * 5)) % 200
        period = 150 + i * 55 + (seed >> (i * 3)) % 60
        col = (min(top[0] + i*3, 255), min(top[1] + 16 + i*13, 255),
               min(top[2] + 14 + i*11, 255))
        pts = [(0, H)]
        for x in range(0, W + 1, 12):
            yv = base + i * 78 + int(amp * math.sin((x + off) / period)) \
                 + int(amp * 0.35 * math.sin((x + off * 2) / (period * 0.42)))
            pts.append((x, yv))
        pts.append((W, H))
        d.polygon(pts, fill=col)

    # a whisper of blur keeps the flat vector look from reading as clip-art
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(EDIMG, exist_ok=True)
    img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=90, optimize=True)


def ai_fallback_pass(replace_cards=False):
    """Generate a rights-free hero for any edition still missing a real picture."""
    try:
        import PIL  # noqa
    except ImportError:
        print("  ai: Pillow missing — skipping"); return
    editions = _load_editions()
    credits  = _load_credits()
    made = skipped = 0
    for e in sorted(editions, key=lambda e: e.get("id","")):
        eid = e["id"]
        if _has_hero(eid, credits, replace_cards):
            continue
        text = _edition_text(e)
        scene = _scene_for(text)
        headline = _headline(e)
        hits = ai_subject_blocked(text)
        if hits:
            # leave it for the data-card pass, which cannot misrepresent anything
            print(f"  ai: skip {eid} — news-event subject ({', '.join(hits[:4])})")
            skipped += 1
            continue
        blob = _api_image(build_ai_prompt(scene))
        try:
            if blob:
                from PIL import Image
                import io
                im = Image.open(io.BytesIO(blob)).convert("RGB")
                if im.width > WIDTH:
                    im = im.resize((WIDTH, round(im.height*WIDTH/im.width)), Image.LANCZOS)
                os.makedirs(EDIMG, exist_ok=True)
                im.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=88, optimize=True)
                kind_src = "AI-generated image"
            else:
                # No generated image. Do NOT draw a gradient -- a real licensed
                # photograph of the market is better than abstract artwork, so
                # leave this edition for assign_edition_photos.py
                # --destination-fallback, which runs next.
                skipped += 1
                continue
        except Exception as ex:
            print(f"  ai: failed for {eid}: {ex}"); continue
        # only reached when generation succeeded -- the no-image path continues above
        credits[eid] = {
            "id": eid,
            "title": "AI-generated image",
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
            # Some publishers block hotlinking without a Referer; send one derived
            # from the article page so a legitimate editorial pull is not refused.
            # A failure here must be LOUD, otherwise the edition silently falls
            # through to an automatic photo of the wrong subject.
            hdrs = {"User-Agent": "Mozilla/5.0 (compatible; EAHospitalityPulse/1.0; "
                                  "+https://eahospitalitypulse.com)",
                    "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*"}
            ref = pick.get("descurl") or url
            if ref:
                hdrs["Referer"] = ref
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=60) as r:
                blob = r.read()
            im = Image.open(io.BytesIO(blob)).convert("RGB")
            if im.width > WIDTH:
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
            os.makedirs(EDIMG, exist_ok=True)
            im.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=88, optimize=True)
        except Exception as ex:
            print(f"::warning::editorial pin FAILED for {eid} <- {url}: {ex} "
                  f"(edition will fall through to an automatic photo — fix the pin)")
            continue
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


# ---------- data-card pass ----------------------------------------------------
def _raw_edition_md(eid):
    """Source markdown for an edition. data.js carries only the Telegram body, and
    _edition_text() lowercases it — neither is usable for pulling a curated figure."""
    p = os.path.join(HERE, "editions-src", eid + ".md")
    try:
        return io.open(p, encoding="utf-8").read()
    except Exception:
        return ""


def _number_of_the_day(md):
    """Pull the edition's own curated headline figure.

    The WhatsApp block already carries NUMBER OF THE DAY — the single most striking
    verified figure of the edition, chosen by hand and traced to a named source. That
    is better hero material than any stock photograph, and it can never be off-topic.
    """
    m = re.search(r"NUMBER OF THE DAY\*?\s*\n+\*?\s*([^\n*]+?)\s*\*?\s*[\u2014-]\s*([^\n]+)", md)
    if not m:
        return None, None
    fig = m.group(1).strip().strip("*").strip()
    cap = m.group(2).strip().rstrip("*").strip()
    return (fig or None), (cap or None)


def _lead_headline(md):
    m = re.search(r"^1\ufe0f\u20e3\s*(.+)$", md, re.M)
    if m:
        return re.sub(r"^[\U0001F000-\U0001FAFF\u2600-\u27BF\s]+", "", m.group(1)).strip()
    return None


def data_card_pass():
    """Default hero: a typographic data card, not scenery.

    Why this is the default. On 28 Aug 2026 an edition arguing Zanzibar package-tour
    yield economics was topped with a photograph of a baby elephant in the Serengeti,
    because the Commons topic-matcher reaches for regional scenery whenever it cannot
    match a subject. For a market-intelligence brief that is decoration, and worse, it
    is decoration that looks like a mismatch to any reader who reads the headline.

    A card carrying 'USD 289 v USD 274' is content. It is always relevant, always
    on-brand, rights-clean, and impossible to get wrong. Photographs are reserved for
    editions with a genuine visual subject and a vetted press-kit image (see
    press_kit_pass) — never reached for merely to fill the slot.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("  data-card: Pillow missing — skipping"); return
    eds, credits = _load_editions(), _load_credits()
    os.makedirs(EDIMG, exist_ok=True)
    made = 0
    for e in eds:
        eid = e.get("id")
        if not eid or _has_hero(eid, credits):
            continue
        md = _raw_edition_md(eid)
        fig, cap = _number_of_the_day(md)
        head = _lead_headline(md) or (e.get("edition") or "")
        if not fig:
            continue                       # nothing verified to show — leave for the chain
        W, H = WIDTH, int(WIDTH * 0.525)
        img = Image.new("RGB", (W, H), TEAL)
        d = ImageDraw.Draw(img)
        for y in range(H):                                   # vertical wash
            t = y / max(H - 1, 1)
            d.line([(0, y), (W, y)],
                   fill=(int(TEAL[0] + (TEAL2[0] - TEAL[0]) * t),
                         int(TEAL[1] + (TEAL2[1] - TEAL[1]) * t),
                         int(TEAL[2] + (TEAL2[2] - TEAL[2]) * t)))
        d.rectangle([0, 0, 14, H], fill=GOLD)
        try:
            f_kick = ImageFont.truetype(FONTB, 30)
            f_fig  = ImageFont.truetype(FONTB, 148)
            f_cap  = ImageFont.truetype(FONT, 34)
            f_head = ImageFont.truetype(FONTB, 40)
        except Exception:
            f_kick = f_fig = f_cap = f_head = ImageFont.load_default()
        pad = 88
        d.text((pad, 66), "EA HOSPITALITY PULSE", font=f_kick, fill=GOLD)
        # figure — shrink to fit rather than overflow
        size, fitted = 148, f_fig
        while size > 54:
            if d.textlength(fig, font=fitted) <= W - 2 * pad:
                break
            size -= 6
            try: fitted = ImageFont.truetype(FONTB, size)
            except Exception: break
        d.text((pad, 156), fig, font=fitted, fill=WHITE)
        y = 156 + size + 30
        for line in _wrap(d, cap or "", f_cap, W - 2 * pad)[:3]:
            d.text((pad, y), line, font=f_cap, fill=SAND); y += 46
        y += 34
        d.line([(pad, y), (pad + 120, y)], fill=GOLD, width=3); y += 26
        for line in _wrap(d, head, f_head, W - 2 * pad)[:2]:
            d.text((pad, y), line, font=f_head, fill=WHITE); y += 50
        # date strip, bottom-left — keeps the card self-dating in a shared image
        try:
            f_dt = ImageFont.truetype(FONT, 26)
            d.text((pad, H - 62), (e.get("dateDisplay") or e.get("edition") or "").strip(),
                   font=f_dt, fill=(150, 190, 182))
        except Exception:
            pass
        img.save(os.path.join(EDIMG, eid + ".jpg"), "JPEG", quality=92)
        credits[eid] = {"id": eid, "title": "Data card — " + (fig or ""),
                        "artist": "EA Hospitality Pulse",
                        "source": "EA Hospitality Pulse", "source_kind": "data-card",
                        "license": "Own work", "licenseurl": "", "descurl": ""}
        made += 1
        print(f"  data-card: {eid}.jpg <- {fig}")
    _save_credits(credits)
    print(f"  data-card: generated {made} card(s)")


def _wrap(d, text, font, maxw):
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--editorial" in args:
        editorial_pass()
    if "--press-kit" in args:
        press_kit_pass()
    if "--data-card" in args:
        data_card_pass()
    if "--openverse" in args:
        openverse_pass()
    if "--check-image-api" in args:
        raise SystemExit(check_image_api())
    if "--ai-fallback" in args:
        ai_fallback_pass(replace_cards="--replace-cards" in args)
    if not args:
        print("usage: hero_extra.py [--editorial] [--press-kit] [--data-card] [--openverse] [--ai-fallback]")
