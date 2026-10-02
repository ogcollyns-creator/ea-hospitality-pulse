#!/usr/bin/env python3
"""Assign a licence-verified hero photograph to a Big Read in guides-src/.

Why this exists
---------------
`assign_edition_photos.py` walks `editions-src/` only. So the automated hero
search has always served the evening Wrap and never the morning Big Read, which
is now the flagship. That is the whole reason a Big Read keeps needing a hero
supplied by hand while the Wrap gets one for free.

This script is the guides half. It deliberately does NOT modify
`assign_edition_photos.py`: it imports the topic table, the scorer and the
quality gate from it, so the two stay in step by construction and a change to
the topic list serves both. Nothing here can alter the editions path.

Two differences from the editions pipeline, both forced by the data model:

1. A guide's "lead" is not a numbered item. It is the frontmatter `title` plus
   `description` (the standfirst), which is exactly the argument the hero has to
   agree with. Using the body alone would score the vocabulary of 1,900 words
   and pick a decorative mismatch, which is the failure the LEAD_WEIGHT guard in
   the editions scorer was written to stop.
2. A guide carries its own credit in frontmatter (`image:` / `image_credit:`),
   not in `img/edition-credits.json`. So this writes the two frontmatter lines
   back into the markdown and touches no shared JSON.

Usage
-----
    python3 assign_guide_photos.py --dry-run          # report, write nothing
    python3 assign_guide_photos.py --limit 1          # assign at most one
    python3 assign_guide_photos.py --only <slug>
    python3 assign_guide_photos.py --replace-pool     # also revisit guides whose
                                                      # hero is a generic pool image

A guide that already names a specific hero is left alone. A guide that scores
nothing keeps whatever it has: per the standing rule, a Big Read that scores no
confident subject should fall back to a repo image, never to scenery.
"""

import argparse, io, json, os, re, sys

import image_sources as isrc
import assign_edition_photos as aep

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDES_SRC = os.path.join(HERE, "guides-src")
EDIMG = os.path.join(HERE, "img", "editions")

WIDTH = aep.WIDTH                       # 1600
MIN_TOPIC_SCORE = aep.MIN_TOPIC_SCORE   # same bar as editions; do not loosen

# Everything in TOPICS after the SUBJECTS block is scenery: a place, not a
# subject. Scenery is acceptable on a Wrap, which is a digest of a whole region's
# day. It is a decorative mismatch on a Big Read, which argues one thing.
#
# This is not theoretical. Scored against the current guides-src, the business
# piece on hotel technology stacks returns "beach" at exactly the threshold, and
# the piece on the construction pipeline returns "beach" at 12. Both would have
# taken a shoreline photograph onto an argument about money. So scenery has to
# clear a materially higher bar here than a subject does, and a Big Read that
# clears neither keeps the hero it already has.
SCENERY = {"gorilla", "migration", "beach", "stonetown", "nairobi", "kigali",
           "kampala", "amboseli", "safari", "port"}
SCENERY_MIN_SCORE = 12

# Heroes already in the repo that are generic rather than chosen for the piece.
# Only these are eligible for replacement under --replace-pool.
POOL_PREFIXES = ("img/pool-", "img/hero/")

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.S)


def split_frontmatter(raw):
    """Return (frontmatter_text, body) or (None, raw) when there is none."""
    m = _FM.match(raw)
    if not m:
        return None, raw
    return m.group(1), m.group(2)


def fm_get(fm, key):
    m = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", fm, re.M)
    if not m:
        return ""
    v = m.group(1)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def fm_set(fm, key, value):
    """Replace a frontmatter scalar, or append it if absent. Always quoted,
    because credit lines contain colons and would otherwise break the parse."""
    q = json.dumps(value, ensure_ascii=False)
    line = f"{key}: {q}"
    pat = re.compile(rf"^{re.escape(key)}:.*?$", re.M)
    if pat.search(fm):
        return pat.sub(lambda _: line, fm, count=1)
    return fm.rstrip("\n") + "\n" + line


def guide_lead(fm, body):
    """What the hero must agree with: the headline and the standfirst."""
    return " ".join([fm_get(fm, "title"), fm_get(fm, "description")]).lower()


def credit_line(pick):
    """House format, matching the existing hand-written guide credits:
    'Photograph: <title> by <artist>, via <source>, <licence>'."""
    title = (pick.get("title") or "").strip().rstrip(".")
    artist = (pick.get("artist") or "Unknown").strip()
    source = (pick.get("source") or "Wikimedia Commons").strip()
    lic = (pick.get("licence") or "").strip()
    bits = [b for b in (f"by {artist}" if artist else "",
                        f"via {source}" if source else "",
                        lic) if b]
    return f"Photograph: {title}, " + ", ".join(bits) if title else \
           "Photograph: " + ", ".join(bits)


def eligible(fm, replace_pool):
    img = fm_get(fm, "image")
    if not img:
        return True
    if replace_pool and img.startswith(POOL_PREFIXES):
        return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing")
    ap.add_argument("--limit", type=int, default=3,
                    help="max guides to assign in one run (protects API quota)")
    ap.add_argument("--only", default="", help="comma-separated guide slugs")
    ap.add_argument("--replace-pool", action="store_true",
                    help="also revisit guides whose hero is a generic pool image")
    a = ap.parse_args(argv)

    if not os.path.isdir(GUIDES_SRC):
        print(f"no {GUIDES_SRC}", file=sys.stderr)
        return 1
    os.makedirs(EDIMG, exist_ok=True)

    Image = None
    if not a.dry_run:
        try:
            from PIL import Image as _I
            Image = _I
        except ImportError:
            print("Pillow required: pip install pillow", file=sys.stderr)
            return 1

    slugs = [f[:-3] for f in sorted(os.listdir(GUIDES_SRC)) if f.endswith(".md")]
    if a.only:
        want = {s.strip() for s in a.only.split(",") if s.strip()}
        slugs = [s for s in slugs if s in want]

    # Do not reuse a source page another guide or edition already uses.
    used_pages = set()
    try:
        with open(os.path.join(HERE, "img", "edition-credits.json"), encoding="utf-8") as f:
            used_pages |= {v.get("descurl") for v in json.load(f).values()
                           if isinstance(v, dict)}
    except Exception:
        pass

    print(f"google discovery: {'ON' if isrc.google_configured() else 'OFF (no CSE credentials)'}")

    todo = []
    for slug in slugs:
        raw = open(os.path.join(GUIDES_SRC, slug + ".md"), encoding="utf-8").read()
        fm, body = split_frontmatter(raw)
        if fm is None:
            print(f"  skip       {slug}  (no frontmatter)")
            continue
        if eligible(fm, a.replace_pool):
            todo.append((slug, raw, fm, body))

    print(f"{len(todo)} guide(s) eligible; assigning at most {a.limit}\n")

    assigned = skipped_topic = skipped_nocand = 0
    for slug, raw, fm, body in todo:
        if assigned >= a.limit:
            print("limit reached — stopping")
            break
        text = (fm_get(fm, "title") + " " + fm_get(fm, "description") + " " + body).lower()
        lead = guide_lead(fm, body)
        hit = aep.detect_topic(text, lead)
        if not hit:
            skipped_topic += 1
            print(f"  keep hero  {slug}  (no confident visual subject)")
            continue
        topic, queries, score = hit
        if topic in SCENERY and score < SCENERY_MIN_SCORE:
            skipped_topic += 1
            print(f"  keep hero  {slug}  (only scenery: {topic}/{score} "
                  f"< {SCENERY_MIN_SCORE})")
            continue

        cands = []
        for q in queries:
            cands += isrc.discover(q, per_source=4)
            if len(cands) >= 12:
                break
        good, bad = isrc.verify(cands)
        good = [c for c in good if aep._usable(c) and c.get("page_url") not in used_pages]
        if not good:
            skipped_nocand += 1
            print(f"  keep hero  {slug}  [{topic}] no licence-verified candidate passed quality")
            continue

        pick = good[0]
        rel = f"img/editions/{slug}.jpg"
        out = os.path.join(EDIMG, slug + ".jpg")
        cred = credit_line(pick)

        if not a.dry_run:
            try:
                img = Image.open(io.BytesIO(isrc._get(pick["image_url"]))).convert("RGB")
                if img.width > WIDTH:
                    img = img.resize((WIDTH, round(img.height * WIDTH / img.width)),
                                     Image.LANCZOS)
                img.save(out, "JPEG", quality=88, optimize=True)
            except Exception as e:
                print(f"  FAILED     {slug}: {e}")
                continue
            fm2 = fm_set(fm_set(fm, "image", rel), "image_credit", cred)
            with open(os.path.join(GUIDES_SRC, slug + ".md"), "w", encoding="utf-8") as f:
                f.write(f"---\n{fm2}\n---\n{body}")

        used_pages.add(pick.get("page_url"))
        assigned += 1
        print(f"  PHOTO      {slug}  [{topic}/{score}] {pick.get('licence')} · "
              f"{pick.get('title', '')[:46]}")

    print(f"\nassigned {assigned} hero(es); {skipped_topic} kept their hero for lack of a "
          f"visual subject; {skipped_nocand} found no verified candidate.")
    if a.dry_run:
        print("dry run — nothing written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
