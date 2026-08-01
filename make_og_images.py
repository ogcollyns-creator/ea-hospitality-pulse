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
    ("hero-serengeti.jpg", ["safari","bush","serengeti","mara","migration",
        "wildlife","savannah","game drive","conservancy","national park","lodge"]),
    ("city-nairobi.jpg", ["nairobi","kampala","dar es salaam","kigali","city",
        "urban","cbd","capital","skyline","business district"]),
    ("beach-zanzibar.jpg", ["beach","coast","zanzibar","dhow","indian ocean",
        "diani","lamu","mombasa","pemba","stone town","dar-es-salaam coast"]),
]
DEFAULT_PHOTO = "hero-serengeti.jpg"   # site-wide default card

def choose_photo(eid, text):
    text_low = (text or "").lower()
    scores = [sum(text_low.count(kw) for kw in kws) for _, kws in POOL]
    best = max(scores)
    if best > 0:
        idx = scores.index(best)
    else:
        idx = int(hashlib.md5(eid.encode()).hexdigest(), 16) % len(POOL)
    return POOL[idx][0]

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
    if editions:
        for e in editions:
            head=e["summary"].split(".")[0][:150]
            match_text = e["summary"] + " " + re.sub(r"<[^>]+>", " ", e.get("bodyHtml",""))
            photo = choose_photo(e["id"], match_text)
            base_card(e["edition"], head, e["dateDisplay"], photo).save(os.path.join(OG,e["id"]+".png"))
    make_favicon()
    print(f"OG images written: {1+(len(editions) if editions else 0)} + favicon")

if __name__=="__main__":
    eds=None
    try:
        d=open(os.path.join(HERE,"data.js"),encoding="utf-8").read()
        m=re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n",d,re.S)
        eds=json.loads(m.group(1)) if m else None
    except Exception as ex:
        print("no editions:",ex)
    main(eds)
