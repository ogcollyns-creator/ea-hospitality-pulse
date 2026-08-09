#!/usr/bin/env python3
"""
Populate img/ with license-clear photography for the edition heroes & share cards.

Why this is a separate step: the images are pulled from Wikimedia Commons at
build-your-own-assets time, normalised to a consistent 1600px-wide JPEG, and
credited automatically. Run it once (and whenever you add entries below):

    python3 fetch_images.py        # downloads into img/, writes img/CREDITS.md
    python3 build_site.py          # heroes + cards regenerate from the new pool

Everything is CC-BY / CC-BY-SA / public-domain from Wikimedia Commons; the
required attribution (author + licence + source) is written to img/CREDITS.md
straight from the Commons API, so the credits are correct by construction.
Link CREDITS publicly (e.g. from the footer) to satisfy the attribution terms.
"""
import os, io, json, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
API = "https://commons.wikimedia.org/w/api.php"
UA = "EAHospitalityPulse-image-fetch/1.0 (https://eahospitalitypulse.com; ceo@eahospitalitypulse.com)"
WIDTH = 1600

# slug (local filename stem)  ->  exact Wikimedia Commons File title
MANIFEST = [
    ("gorilla-volcanoes",     "Mountain gorilla (Gorilla beringei beringei) yawn.jpg"),
    ("amboseli-kilimanjaro",  "Elephants at Amboseli national park against Mount Kilimanjaro.jpg"),
    ("mara-crossing",         "Wildebeest Jumping Into the Mara River.jpg"),
    ("stonetown-zanzibar",    "Stone Town-2.jpg"),
    ("kigali-convention",     "An aerial of Kigali Convention Center on June 19, 2019. Photo by Emmanuel Kwizera.jpg"),
    ("kigali-night",          "Panoramic view of Kigali (Rwanda) at night 01.jpg"),
    ("kenya-airways-aircraft","Kenya Airways Boeing 737-300 5Y-KQB NBO 2010-6-18.png"),
    ("kyobe-nile-lodge",      "View of the River Nile from Kyobe Safari Lodge – Murchison Falls National Park, Uganda 03.jpg"),
    ("uhuru-kilimanjaro",     "Uhuru Peak Mt. Kilimanjaro 1.JPG"),
]

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def _strip_html(s):
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()

def imageinfo(title):
    q = {"action": "query", "titles": "File:" + title, "prop": "imageinfo",
         "iiprop": "url|extmetadata", "iiurlwidth": str(WIDTH), "format": "json"}
    data = json.loads(_get(API + "?" + urllib.parse.urlencode(q)))
    page = next(iter(data["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise RuntimeError("not found: " + title)
    ii = page["imageinfo"][0]
    em = ii.get("extmetadata", {})
    return {
        "thumb": ii.get("thumburl") or ii["url"],
        "descurl": ii.get("descriptionurl", "https://commons.wikimedia.org/wiki/File:" + title),
        "artist": _strip_html(em.get("Artist", {}).get("value", "")) or "Unknown",
        "license": _strip_html(em.get("LicenseShortName", {}).get("value", "")) or "See source",
        "licenseurl": em.get("LicenseUrl", {}).get("value", ""),
    }

def main():
    os.makedirs(IMG, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow required: pip install pillow")
    credits, ok = [], 0
    for slug, title in MANIFEST:
        out = os.path.join(IMG, slug + ".jpg")
        try:
            info = imageinfo(title)
            img = Image.open(io.BytesIO(_get(info["thumb"]))).convert("RGB")
            # normalise to <=1600px wide, save a clean JPEG
            if img.width > WIDTH:
                img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
            img.save(out, "JPEG", quality=85, optimize=True)
            credits.append((slug, title, info))
            ok += 1
            print(f"  ok  {slug}.jpg  <- {title}  [{info['license']}]")
        except Exception as ex:
            print(f"  FAIL {slug}: {ex}")
        time.sleep(0.5)   # be polite to the Commons API
    # attribution file (required for CC-BY / CC-BY-SA)
    lines = ["# Image credits\n",
             "Hero and share-card photography, sourced from Wikimedia Commons and",
             "cropped/tinted for layout. Each image remains under its original licence.\n"]
    for slug, title, info in credits:
        lic = f"[{info['license']}]({info['licenseurl']})" if info["licenseurl"] else info["license"]
        lines.append(f"- **{slug}.jpg** — {info['artist']}, {lic}. "
                     f"Source: [{title}]({info['descurl']}).")
    open(os.path.join(IMG, "CREDITS.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\n{ok}/{len(MANIFEST)} downloaded. Credits -> img/CREDITS.md")
    print("Next: python3 build_site.py  (heroes + cards will pick up the new pool)")

if __name__ == "__main__":
    main()
