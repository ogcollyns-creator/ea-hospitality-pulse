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
import os, re, json, hashlib
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OG = os.path.join(HERE, "og")
IMG = os.path.join(HERE, "img")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TEAL=(10,79,72); TEAL2=(15,109,99); GOLD=(200,137,47); SAND=(246,241,231); WHITE=(255,255,255)
W,H = 1200,630

# ---- curated photo pool -----------------------------------------------
# Each photo is tagged with keywords; the edition's own text is scanned
# for a category match so the picture fits the story. No match -> a
# deterministic hash of the edition id picks one, so the same edition
# always renders the same photo (stable across rebuilds).
POOL = [
    # These are pan-East-Africa briefs that name every country every day, so
    # country and hub-city names are NOT discriminative. Keys below are rare,
    # distinctive signals only; an edition with no strong theme falls back to an
    # even hash spread, which keeps the visible photography varied.
    ("hero-serengeti.jpg", ["safari","serengeti","savannah","game drive","game reserve",
        "ngorongoro","tarangire","big five","big cat","leopard","cheetah"]),
    ("city-nairobi.jpg", ["cbd","westlands","upper hill","upperhill","gigiri",
        "nairobi expressway","business district","office space","grade a office"]),
    ("beach-zanzibar.jpg", ["diani","nungwi","kendwa","watamu","kilifi","malindi",
        "dhow","coral reef","snorkel","white sand","beach resort"]),
    ("gorilla-volcanoes.jpg", ["gorilla","gorillas","chimpanzee","chimp","bwindi",
        "volcanoes national park","virunga","nyungwe","golden monkey","gorilla trek",
        "gorilla permit","primate"]),
    ("amboseli-kilimanjaro.jpg", ["amboseli","elephant","elephants","tusker","tsavo"]),
    ("mara-crossing.jpg", ["wildebeest","mara river","great migration","river crossing",
        "calving","the migration"]),
    ("stonetown-zanzibar.jpg", ["stone town","swahili","forodhani","old fort",
        "spice tour","world heritage"]),
    ("kigali-convention.jpg", ["conference","convention","mice","summit","congress",
        "expo","exhibition","delegates","trade show","business events","conferencing",
        "icca","incentive travel","conference tourism"]),
    ("kigali-night.jpg", ["nyarugenge","kigali skyline","rwandan capital","kigali city"]),
    ("kenya-airways-aircraft.jpg", ["airline","aviation","aircraft","jkia","kenya airways",
        "rwandair","air tanzania","new route","direct flight","seat capacity","frequencies",
        "load factor","airlift","aircraft order","route launch","widebody"]),
    ("kyobe-nile-lodge.jpg", ["river nile","murchison","jinja","kabalega",
        "pearl of africa","source of the nile","lake albert"]),
    ("uhuru-kilimanjaro.jpg", ["kilimanjaro","uhuru","summit push","trekking","mountaineering",
        "machame","marangu","kili","climbers","altitude"]),
]
DEFAULT_PHOTO = "hero-serengeti.jpg"   # site-wide default card

def available_pool():
    """Only offer photos that are actually present, so the build never breaks
    before fetch_images.py has been run. Falls back to the full list."""
    present = [(fn, kws) for fn, kws in POOL if os.path.exists(os.path.join(IMG, fn))]
    return present or POOL

def choose_photo(eid, text):
    pool = available_pool()
    text_low = (text or "").lower()
    scores = [sum(text_low.count(kw) for kw in kws) for _, kws in pool]
    best = max(scores) if scores else 0
    if best > 0:
        idx = scores.index(best)
    else:
        idx = int(hashlib.md5(eid.encode()).hexdigest(), 16) % len(pool)
    return pool[idx][0]

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
    path = os.path.join(IMG, photo_file)
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
    base = cover_resize(Image.open(os.path.join(IMG, photo_file)).convert("RGB"), W, H)
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
    for photo_file, _ in available_pool():
        out = "clean-" + os.path.splitext(photo_file)[0] + ".png"
        if not os.path.exists(os.path.join(OG, out)):
            light_hero(photo_file).save(os.path.join(OG, out))
        hero_for[photo_file] = out
    light_hero(DEFAULT_PHOTO).save(os.path.join(OG, "clean-default.png"))
    hero_map = {}
    if editions:
        for e in editions:
            head=e["summary"].split(".")[0][:150]
            match_text = e["summary"] + " " + re.sub(r"<[^>]+>", " ", e.get("bodyHtml",""))
            photo = choose_photo(e["id"], match_text)
            base_card(e["edition"], head, e["dateDisplay"], photo).save(os.path.join(OG,e["id"]+".png"))
            hero_map[e["id"]] = hero_for.get(photo, "clean-default.png")
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
