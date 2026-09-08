#!/usr/bin/env python3
"""
Generate branded 1200x630 social share images.
  - og/default.png              site-wide
  - og/<edition-id>.png         one per edition, carrying its headline
  - favicon.png / favicon.ico

Each card composites real photography (from img/) under a brand-teal
gradient (same treatment as the homepage hero) with the masthead/kicker/
headline/footer text drawn on top — no network access needed at build
time, since the photo pool is stored in the repo under img/.

Called automatically by build_site.py.
"""
import os, re, json, hashlib, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OG = os.path.join(HERE, "og")
IMG = os.path.join(HERE, "img")
EDIMG = os.path.join(IMG, "editions")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TEAL=(10,79,72); TEAL2=(15,109,99); GOLD=(200,137,47); SAND=(246,241,231); WHITE=(255,255,255)
W,H = 1200,630

# ---- curated photo pool -----------------------------------------------
# Each photo carries (filename, home markets, distinctive keywords).
#
# WHY THE SCORING BELOW IS DEFENSIVE
# On 8 Sep 2026 this edition -- an Ebola-risk lead plus two Zanzibar resort
# openings -- shipped under a Kigali Convention Centre photo. It had nothing on
# Rwanda. The cause: choose_photo() counted raw substring hits across the WHOLE
# edition and took max(), so a single "MICE" in a Week Ahead footnote (a line
# that explicitly told operators to IGNORE the event) scored 1, beat everything
# else, and picked the hero. There was no minimum bar and no geography check.
#
# assign_edition_photos.py already solved this for its own path -- lead-weighted
# scoring, MIN_TOPIC_SCORE, "no lead hit means no photo at all" -- but that runs
# only on the GitHub runner. When it writes no img/editions/<id>.jpg, the build
# silently falls through to here, which had none of those guards. Ported now.
POOL = [
    ("hero-serengeti.jpg", ["TZ","KE"], ["safari","serengeti","savannah","game drive","game reserve",
        "ngorongoro","tarangire","big five","big cat","leopard","cheetah"]),
    ("city-nairobi.jpg", ["KE"], ["cbd","westlands","upper hill","upperhill","gigiri",
        "nairobi expressway","business district","office space","grade a office"]),
    ("beach-zanzibar.jpg", ["TZ"], ["nungwi","kendwa","pwani mchangani","unguja",
        "dhow","coral reef","snorkel","white sand","beach resort","beach hotel"]),
    ("gorilla-volcanoes.jpg", ["RW","UG"], ["gorilla","gorillas","chimpanzee","chimp","bwindi",
        "volcanoes national park","virunga","nyungwe","golden monkey","gorilla trek",
        "gorilla permit","primate"]),
    ("amboseli-kilimanjaro.jpg", ["KE","TZ"], ["amboseli","elephant","elephants","tusker","tsavo"]),
    ("mara-crossing.jpg", ["KE","TZ"], ["wildebeest","mara river","great migration","river crossing",
        "calving","the migration"]),
    ("stonetown-zanzibar.jpg", ["TZ"], ["stone town","swahili","forodhani","old fort",
        "spice tour","world heritage"]),
    ("kigali-convention.jpg", ["RW"], ["conference","convention","mice","summit","congress",
        "expo","exhibition","delegates","trade show","business events","conferencing",
        "icca","incentive travel","conference tourism"]),
    ("kigali-night.jpg", ["RW"], ["nyarugenge","kigali skyline","rwandan capital","kigali city"]),
    ("kenya-airways-aircraft.jpg", ["KE"], ["airline","aviation","aircraft","jkia","kenya airways",
        "rwandair","air tanzania","new route","direct flight","seat capacity","frequencies",
        "load factor","airlift","aircraft order","route launch","widebody"]),
    ("kyobe-nile-lodge.jpg", ["UG"], ["river nile","murchison","jinja","kabalega",
        "pearl of africa","source of the nile","lake albert"]),
    ("uhuru-kilimanjaro.jpg", ["TZ"], ["kilimanjaro","uhuru","summit push","trekking","mountaineering",
        "machame","marangu","kili","climbers","altitude"]),
    # Subject frames. "*" means the subject is not tied to a market, so the
    # geography veto does not apply -- a laboratory or a fuel pump illustrates
    # the story wherever it happened. Populated by fetch_pool_images.py; absent
    # files are filtered out by available_pool(), so this degrades quietly.
    ("pool-health-1.jpg", ["*"], ["ebola","outbreak","epidemic","pheic","cholera","marburg",
        "mpox","treatment centre","health worker","quarantine","bundibugyo","case fatality"]),
    ("pool-energy-1.jpg", ["*"], ["epra","fuel price","diesel","petrol","kerosene","kwh",
        "electricity","generator","load shedding","pump price","tariff"]),
    ("pool-currency-1.jpg", ["*"], ["shilling","inflation","cpi","central bank","forex",
        "exchange rate","reserves","interest rate","mpc","levy","vat"]),
    ("pool-logistics-1.jpg", ["*"], ["port","harbour","container","freight","customs",
        "supply chain","shipping","border post"]),
    ("pool-build-1.jpg", ["*"], ["construction","groundbreaking","refurbishment",
        "new hotel","rooms opening","inaugurated","pipeline"]),
    ("pool-labour-1.jpg", ["*"], ["strike","union","staffing","wages","recruitment",
        "workforce","hospitality college","chefs","skills"]),
    ("pool-policy-1.jpg", ["*"], ["gazette","regulation","licence","permit fee",
        "parliament","directive","circular","visa","eta","immigration"]),
]
DEFAULT_PHOTO = "hero-serengeti.jpg"   # pan-regional; claims no specific market

# A hero must match the LEAD, not vocabulary that happens to appear somewhere in
# 3,000 words. Same constants as assign_edition_photos.py, same reasoning.
LEAD_WEIGHT = 3
SENSITIVE_LEAD = ["ebola","outbreak","epidemic","cholera","marburg","pheic",
                  "do not travel","level 4","advisory","terror","attack","kidnap",
                  "unrest","protest","evacuation","crash","fatal","quarantine"]
WILDLIFE_FRAMES = {"gorilla-volcanoes.jpg", "mara-crossing.jpg",
                   "amboseli-kilimanjaro.jpg", "hero-serengeti.jpg"}
MIN_TOPIC_SCORE = 3        # >=1 lead hit, or >=3 body hits, before we trust a topic

# Which market is the edition actually about? Used to veto a geographically
# wrong photo even when a topic scores, and to steer the no-match fallback.
COUNTRY_MARKERS = {
    "KE": ["kenya","nairobi","mombasa","diani","knbs","kws","epra","jkia","kenyan"],
    "UG": ["uganda","kampala","entebbe","ubos","bwindi","ugandan"],
    "TZ": ["tanzania","zanzibar","dar es salaam","arusha","serengeti","unguja",
           "pemba","stone town","tanzanian","zanzibari"],
    "RW": ["rwanda","kigali","musanze","rdb","rwandan"],
}

def available_pool():
    """Only offer photos that are actually present, so the build never breaks
    before fetch_images.py has been run. Falls back to the full list."""
    present = [(fn, mk, kws) for fn, mk, kws in POOL if os.path.exists(os.path.join(IMG, fn))]
    return present or POOL

# Item markers like "1\ufe0f\u20e3" and section emoji render as tofu boxes in the
# card fonts -- they have no glyph in Inter/Source Sans. Strip them from headline
# text rather than shipping a broken square next to the masthead.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF"
    "\uFE0F\u20E3\u2600-\u26FF]+")

def _strip_emoji(s):
    s = _EMOJI.sub("", s or "")
    # "1\ufe0f\u20e3 HEADLINE" leaves a bare "1 " once the keycap is removed
    s = re.sub(r"^\s*\d{1,2}\s+(?=[A-Z])", "", s)
    return re.sub(r"\s{2,}", " ", s).strip(" -\u2014\u00b7")


_CREDITS_CACHE = {}

def _is_data_card(eid):
    """True when hero_extra.py generated a typographic data card for this edition."""
    if not _CREDITS_CACHE:
        try:
            with open(os.path.join(IMG, "edition-credits.json"), encoding="utf-8") as fh:
                _CREDITS_CACHE.update(json.load(fh))
        except Exception:
            _CREDITS_CACHE["__none__"] = {}
    rec = _CREDITS_CACHE.get(eid) or {}
    return rec.get("source_kind") == "data-card"


def _hits(text, kws):
    """Word-boundary matches. Substring counting was part of the old bug."""
    n = 0
    for kw in kws:
        n += len(re.findall(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", text))
    return n


def focus_countries(lead_low, body_low):
    """Markets the edition genuinely COVERS.

    Deliberately NOT lead-weighted. This set is a veto list, and its only job is
    to exclude countries the edition does not discuss -- the 8 Sep Kigali error.
    Weighting it by the lead made it a one-country filter, which then pushed an
    Ebola-risk lead towards a gorilla photo because that was the only frame left
    standing. Coverage decides eligibility; the topic score below decides which.
    """
    sc = {c: _hits(body_low, m) for c, m in COUNTRY_MARKERS.items()}
    top = max(sc.values()) if sc else 0
    if top == 0:
        return set()
    return {c for c, v in sc.items() if v >= 2 and v >= top * 0.2}


def choose_photo(eid, text, lead=""):
    """Pick a hero that matches the LEAD and the edition's actual geography.

    Returns DEFAULT_PHOTO rather than guessing: a pan-regional savannah frame
    claims no market, which is the honest failure mode. A confident-looking
    photo of the wrong country is not.
    """
    pool = available_pool()
    body_low = (text or "").lower()
    lead_low = (lead or "").lower()
    focus = focus_countries(lead_low, body_low)

    # A lead about an outbreak, advisory or security shock must not be
    # illustrated with a wildlife trophy frame -- that reads as tone-deaf even
    # when the geography is right.
    sensitive = _hits(lead_low, SENSITIVE_LEAD) > 0

    scored = []
    for fn, markets, kws in pool:
        if "*" not in markets and focus and not (set(markets) & focus):
            continue                                   # geography veto
        if sensitive and fn in WILDLIFE_FRAMES:
            continue                                   # tone veto
        s = _hits(lead_low, kws) * LEAD_WEIGHT + _hits(body_low, kws)
        scored.append((s, fn))

    if scored:
        best = max(scored)
        if best[0] >= MIN_TOPIC_SCORE:
            return best[1]
        # No confident subject. Stay inside the edition's geography and spread
        # deterministically so the site does not repeat one frame all week.
        eligible = sorted(fn for _, fn in scored)
        if eligible:
            return eligible[int(hashlib.md5(eid.encode()).hexdigest(), 16) % len(eligible)]
    return DEFAULT_PHOTO

def f(path,size):
    return ImageFont.truetype(path,size)

def cover_resize(img, tw, th):
    """Resize+crop an image to exactly (tw,th), preserving aspect ratio, cropping the overflow (like CSS background-size:cover)."""
    sw, sh = img.size
    scale = max(tw/sw, th/sh)
    nw, nh = max(tw,int(sw*scale)+1), max(th,int(sh*scale)+1)
    img = img.resize((nw,nh), Image.LANCZOS)
    left = (nw-tw)//2
    top = (nh-th)//2
    return img.crop((left,top,left+tw,top+th))

def photo_background(photo_file):
    """Load a pool photo, cover-crop to card size, and lay the brand
    gradient over it (same 135deg teal treatment as the site hero) so
    text stays legible regardless of the source image."""
    path = photo_file if (os.path.isabs(photo_file) or os.path.exists(photo_file)) else os.path.join(IMG, photo_file)
    base = Image.open(path).convert("RGB")
    base = cover_resize(base, W, H)

    # diagonal (135deg) teal gradient, alpha ~0.88 -> ~0.80
    import numpy as np
    xs = np.linspace(0,1,W)
    ys = np.linspace(0,1,H)
    gx, gy = np.meshgrid(xs, ys)
    t = (gx+gy)/2.0
    r = (TEAL[0] + (TEAL2[0]-TEAL[0])*t)
    g = (TEAL[1] + (TEAL2[1]-TEAL[1])*t)
    b = (TEAL[2] + (TEAL2[2]-TEAL[2])*t)
    a = (0.88 + (0.80-0.88)*t) * 255
    overlay_arr = np.dstack([r,g,b,a]).astype("uint8")
    overlay = Image.fromarray(overlay_arr, "RGBA")

    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")

def light_hero(photo_file):
    """Text-free in-page hero: the real photograph, only lightly treated for
    depth and brand cohesion — no masthead/kicker/headline baked on. Used by
    the article <img>; the text-heavy card above is kept for social sharing."""
    import numpy as np
    src = photo_file if (os.path.isabs(photo_file) or os.path.exists(photo_file)) else os.path.join(IMG, photo_file)
    base = cover_resize(Image.open(src).convert("RGB"), W, H)
    ys = np.linspace(0, 1, H)[:, None]
    a = (0.06 + (0.34 - 0.06) * (ys ** 1.6)) * 255     # clear at top, gentle teal grounding at base
    a = np.repeat(a, W, axis=1)
    r = np.full((H, W), TEAL[0]); g = np.full((H, W), TEAL[1]); b = np.full((H, W), TEAL[2])
    overlay = Image.fromarray(np.dstack([r, g, b, a]).astype("uint8"), "RGBA")
    img = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    ImageDraw.Draw(img).rectangle([0, 0, W, 8], fill=GOLD)   # slim brand rule
    return img

def base_card(kicker, headline, footer, photo_file):
    img = photo_background(photo_file)
    d=ImageDraw.Draw(img)
    # gold rule top
    d.rectangle([0,0,W,10],fill=GOLD)
    # masthead
    d.text((70,58),"🏨".encode('ascii','ignore').decode() or "",font=f(FONTB,40),fill=WHITE)
    d.text((70,60),"EA HOSPITALITY PULSE",font=f(FONTB,40),fill=WHITE)
    d.text((72,112),"For hotels, lodges, resorts, tour operators & DMCs",font=f(FONT,21),fill=(214,228,224))
    # kicker
    if kicker:
        kw=d.textlength(kicker.upper(),font=f(FONTB,19))
        d.rounded_rectangle([70,178,70+kw+34,220],14,fill=GOLD)
        d.text((87,187),kicker.upper(),font=f(FONTB,19),fill=(35,26,6))
    # headline — wrap by MEASURED pixel width so it never overflows
    maxw = W - 140                      # 70px margins both sides
    def wrap_px(text, font):
        words, lines, cur = text.split(), [], ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if d.textlength(trial, font=font) <= maxw:
                cur = trial
            else:
                if cur: lines.append(cur)
                cur = w_
        if cur: lines.append(cur)
        return lines
    size = 46
    wrapped = wrap_px(headline, f(FONTB, size))
    while len(wrapped) > 4 and size > 30:      # shrink until it fits in 4 lines
        size -= 4
        wrapped = wrap_px(headline, f(FONTB, size))
    wrapped = wrapped[:4]
    block=len(wrapped)*(size+12)
    y=250+max(0,(H-95-250-block)//2-20)
    for line in wrapped:
        d.text((70,y),line,font=f(FONTB,size),fill=WHITE); y+=size+12
    # footer
    d.line([(70,H-95),(W-70,H-95)],fill=(70,120,113),width=2)
    d.text((70,H-72),footer,font=f(FONT,22),fill=(196,214,210))
    cty="KE · UG · TZ · ZNZ · RW"
    d.text((W-70-d.textlength(cty,font=f(FONT,22)),H-72),cty,font=f(FONT,22),fill=GOLD)
    return img

def make_favicon():
    for sz in (180,32):
        i=Image.new("RGB",(sz,sz),TEAL)
        d=ImageDraw.Draw(i)
        d.rounded_rectangle([0,0,sz-1,sz-1],int(sz*0.22),fill=TEAL)
        fs=int(sz*0.62)
        t="P"
        tw=d.textlength(t,font=f(FONTB,fs))
        d.text(((sz-tw)/2, sz*0.16), t, font=f(FONTB,fs), fill=GOLD)
        i.save(os.path.join(HERE, "apple-touch-icon.png" if sz==180 else "favicon.png"))
    Image.open(os.path.join(HERE,"favicon.png")).save(os.path.join(HERE,"favicon.ico"),sizes=[(32,32)])

def main(editions=None):
    os.makedirs(OG,exist_ok=True)
    base_card("Daily intelligence",
              "Daily market intelligence for East Africa's hospitality and travel trade.",
              "Three briefs a day · Free on Telegram",
              DEFAULT_PHOTO).save(os.path.join(OG,"default.png"))
    # text-free in-page heroes — one per source photo (small, reused across editions)
    hero_for = {}
    for photo_file, _, _ in available_pool():
        out = "clean-" + os.path.splitext(photo_file)[0] + ".png"
        if not os.path.exists(os.path.join(OG, out)):
            light_hero(photo_file).save(os.path.join(OG, out))
        hero_for[photo_file] = out
    light_hero(DEFAULT_PHOTO).save(os.path.join(OG, "clean-default.png"))
    hero_map = {}
    if editions:
        for e in editions:
            head=_strip_emoji(e["summary"].split(".")[0])[:150]
            plain = re.sub(r"<[^>]+>", " ", e.get("bodyHtml",""))
            match_text = e["summary"] + " " + plain
            # LEAD = headline + first story. Anything after it (Week Ahead,
            # radar block, footnotes) must not be able to pick the hero.
            lead_text = e["summary"] + " " + plain[:1200]
            ed_photo = os.path.join(EDIMG, e["id"] + ".jpg")   # per-edition photo or data card
            if os.path.exists(ed_photo) and _is_data_card(e["id"]):
                # Already a finished, self-dating card carrying the edition's own
                # figure and headline. Compositing base_card() on top of it printed
                # the masthead, headline and date twice, ghosted over each other.
                card = Image.open(ed_photo).convert("RGB")
                cover_resize(card, W, H).save(os.path.join(OG, e["id"] + ".png"))
                cover_resize(card, W, H).save(os.path.join(OG, e["id"] + "-clean.png"))
            elif os.path.exists(ed_photo):
                base_card(e["edition"], head, e["dateDisplay"], ed_photo).save(os.path.join(OG,e["id"]+".png"))
                light_hero(ed_photo).save(os.path.join(OG, e["id"]+"-clean.png"))
            else:
                photo = choose_photo(e["id"], match_text, lead_text)          # curated-pool fallback
                base_card(e["edition"], head, e["dateDisplay"], photo).save(os.path.join(OG,e["id"]+".png"))
                clean_name = hero_for.get(photo, "clean-default.png")
                shutil.copyfile(os.path.join(OG, clean_name), os.path.join(OG, e["id"]+"-clean.png"))
            # Homepage cards AND the article hero use e.id-clean.png (text-free);
            # the text card e.id.png stays as the social-share og:image only.
            hero_map[e["id"]] = e["id"] + "-clean.png"
    json.dump(hero_map, open(os.path.join(OG, "hero_map.json"), "w", encoding="utf-8"))
    make_favicon()
    print(f"OG images written: {1+(len(editions) if editions else 0)} cards + {len(hero_for)+1} clean heroes + favicon")

if __name__=="__main__":
    eds=None
    try:
        d=open(os.path.join(HERE,"data.js"),encoding="utf-8").read()
        m=re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n",d,re.S)
        eds=json.loads(m.group(1)) if m else None
    except Exception as ex:
        print("no editions:",ex)
    main(eds)
