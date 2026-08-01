#!/usr/bin/env python3
"""
Generate branded 1200x630 social share images.
  - og/default.png              site-wide
  - og/<edition-id>.png         one per edition, carrying its headline
  - favicon.png / favicon.ico
Called automatically by build_site.py.
"""
import os, re, json, textwrap
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OG = os.path.join(HERE, "og")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TEAL=(10,79,72); TEAL2=(15,109,99); GOLD=(200,137,47); SAND=(246,241,231); WHITE=(255,255,255)
W,H = 1200,630

def f(path,size):
    return ImageFont.truetype(path,size)

def gradient(img):
    d=ImageDraw.Draw(img)
    for y in range(H):
        t=y/H
        c=(int(TEAL[0]+(TEAL2[0]-TEAL[0])*t),
           int(TEAL[1]+(TEAL2[1]-TEAL[1])*t),
           int(TEAL[2]+(TEAL2[2]-TEAL[2])*t))
        d.line([(0,y),(W,y)],fill=c)
    return d

def base_card(kicker, headline, footer):
    img=Image.new("RGB",(W,H),TEAL)
    d=gradient(img)
    # gold rule top
    d.rectangle([0,0,W,10],fill=GOLD)
    # masthead
    d.text((70,58),"🏨".encode('ascii','ignore').decode() or "",font=f(FONTB,40),fill=WHITE)
    d.text((70,60),"EA HOSPITALITY PULSE",font=f(FONTB,40),fill=WHITE)
    d.text((72,112),"Daily intelligence for city, bush & beach properties",font=f(FONT,21),fill=(214,228,224))
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
              "Daily market intelligence for East Africa's hospitality leaders.",
              "Three briefs a day · Free on Telegram").save(os.path.join(OG,"default.png"))
    if editions:
        for e in editions:
            head=e["summary"].split(".")[0][:150]
            base_card(e["edition"], head, e["dateDisplay"]).save(os.path.join(OG,e["id"]+".png"))
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
