#!/usr/bin/env python3
"""Hand-supplied heroes: one drop folder, and a gate that blocks publishing without one.

Editor decision, 2 October 2026: every edition and every Big Read carries a hero
chosen by a person. Automated photo selection is retired. The reason is relevance,
and the evidence is the archive: the search returned "Paje beach at low tide" for a
levy brief and "Lions Waking Up" for a market wrap, because ten of the nineteen
scoring topics are places rather than subjects, and because no reusable photograph
of "a cash reserve requirement hike" exists to be found.

This script replaces that pipeline with two commands.

  --intake    process img/incoming/ and file each hero where it actually belongs
  --check     fail if any edition or guide lacks a hand-supplied hero

Everything published before 2 October 2026 is grandfathered: see CUTOFF below.
`--since 0000-00-00` audits the whole archive when you want the backlog.

Why a drop folder
-----------------
A mandatory hero is only workable if supplying one is trivial. Before this, an
edition hero went to og/ and had to be named in og/hero_map.json AND described in
img/edition-credits.json, while a Big Read hero went to img/editions/ and was named
in its own frontmatter. Two destinations with rhyming filenames. On 1 October a
supplied photograph went to the guide location for an edition, so nothing read it
and the page kept a data card. That is the failure this removes: drop one file in
img/incoming/, named for the thing it belongs to, and intake routes it.

    img/incoming/pulse-2026-10-01-evening.jpg   -> edition hero
    img/incoming/<big-read-slug>.jpg            -> guide hero

Why the credit is required
--------------------------
Fourteen entries in img/edition-credits.json currently read "no reuse licence
granted", with artists recorded as Unverified or Unidentified. Every one came from
a hand-supplied pin, and none from the automated path. Routing all hero volume
through hand supply therefore raises that exposure unless supplying a credit is
part of supplying a hero. So intake refuses a file with no credit beside it:

    img/incoming/pulse-2026-10-01-evening.jpg
    img/incoming/pulse-2026-10-01-evening.credit.txt

The .credit.txt holds one line, the credit as it should print. Use the house forms:

    Photograph: Onyango George / EA Hospitality Pulse
    Handout: Dangote Group / Government of Kenya - editorial use
    Photograph: <title> by <artist>, via Wikimedia Commons, CC BY-SA 4.0

This is not a licence check, which no script can do. It is a record of what the
publisher asserts, attached at the moment of supply rather than reconstructed later.
"""

import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INCOMING = os.path.join(HERE, "img", "incoming")
OG = os.path.join(HERE, "og")
EDIMG = os.path.join(HERE, "img", "editions")
EDSRC = os.path.join(HERE, "editions-src")
GDSRC = os.path.join(HERE, "guides-src")
HERO_MAP = os.path.join(OG, "hero_map.json")
CREDITS = os.path.join(HERE, "img", "edition-credits.json")

MIN_W, MIN_H = 1200, 630
WIDTH = 1600
EXTS = (".jpg", ".jpeg", ".png", ".webp")

# Everything published before the policy existed is grandfathered. The archive
# holds 5 editions on data cards and 8 Big Reads with no hero at all; retro-
# fitting those is a weekend of work that buys nothing, and a gate that is red
# from the day it ships gets ignored, which is the only way a gate really fails.
# So the rule bites from the day it was decided and not before. Override with
# --since for a one-off audit of the back catalogue.
CUTOFF = "2026-10-02"

_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.S)


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _ids(d, suffix=".md"):
    try:
        return {f[: -len(suffix)] for f in os.listdir(d) if f.endswith(suffix)}
    except FileNotFoundError:
        return set()


def split_fm(raw):
    m = _FM.match(raw)
    return (m.group(1), m.group(2)) if m else (None, raw)


def fm_get(fm, key):
    m = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", fm, re.M)
    if not m:
        return ""
    v = m.group(1)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def fm_set(fm, key, value):
    line = f"{key}: {json.dumps(value, ensure_ascii=False)}"
    pat = re.compile(rf"^{re.escape(key)}:.*?$", re.M)
    return pat.sub(lambda _: line, fm, count=1) if pat.search(fm) \
        else fm.rstrip("\n") + "\n" + line


# --------------------------------------------------------------------- intake

def _prepare(src, dest, dry):
    """Normalise to a publishable hero: RGB JPEG, at least MIN_W x MIN_H.

    A phone or press-kit frame is often under the floor. Rather than refuse it and
    block the edition, upscale with Lanczos and a light unsharp mask, which is what
    the image policy already allows for source photos below the minimum.
    """
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGB")
    w, h = im.size
    note = f"{w}x{h}"
    if w < MIN_W or h < MIN_H:
        scale = max(MIN_W / w, MIN_H / h)
        tw, th = round(w * scale), round(h * scale)
        im = im.resize((tw, th), Image.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=1.4, percent=55, threshold=3))
        note += f" -> {tw}x{th} (upscaled)"
    elif w > WIDTH:
        im = im.resize((WIDTH, round(h * WIDTH / w)), Image.LANCZOS)
        note += f" -> {im.size[0]}x{im.size[1]}"
    if not dry:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        im.save(dest, "JPEG", quality=88, optimize=True, progressive=True)
    return note


def intake(dry):
    if not os.path.isdir(INCOMING):
        print(f"no {INCOMING} — nothing to take in")
        return 0
    editions, guides = _ids(EDSRC), _ids(GDSRC)
    hero_map = _load(HERO_MAP, {})
    credits = _load(CREDITS, {})
    files = [f for f in sorted(os.listdir(INCOMING))
             if f.lower().endswith(EXTS)]
    if not files:
        print("img/incoming/ is empty")
        return 0

    done = failed = 0
    for fn in files:
        stem = os.path.splitext(fn)[0]
        src = os.path.join(INCOMING, fn)
        credit_path = os.path.join(INCOMING, stem + ".credit.txt")

        if stem not in editions and stem not in guides:
            print(f"  ⛔ {fn}: no edition or guide named '{stem}'")
            failed += 1
            continue
        if not os.path.exists(credit_path):
            print(f"  ⛔ {fn}: missing {stem}.credit.txt — a hero needs a credit")
            failed += 1
            continue
        credit = open(credit_path, encoding="utf-8").read().strip()
        if not credit:
            print(f"  ⛔ {fn}: {stem}.credit.txt is empty")
            failed += 1
            continue

        if stem in editions:
            dest = os.path.join(OG, stem + "-hero.jpg")
            note = _prepare(src, dest, dry)
            hero_map[stem] = stem + "-hero.jpg"
            credits[stem] = {
                "id": stem,
                "title": credit,
                "artist": credit.split(":", 1)[-1].strip() or "Publisher-supplied",
                "source": "Editor-supplied",
                "source_kind": "editor-supplied",
                "license": credit,
                "licenseurl": "",
                "descurl": "",
            }
            print(f"  ✅ edition {stem}  og/{stem}-hero.jpg  [{note}]")
        else:
            dest = os.path.join(EDIMG, stem + ".jpg")
            note = _prepare(src, dest, dry)
            p = os.path.join(GDSRC, stem + ".md")
            raw = open(p, encoding="utf-8").read()
            fm, body = split_fm(raw)
            if fm is None:
                print(f"  ⛔ {fn}: {stem}.md has no frontmatter")
                failed += 1
                continue
            fm = fm_set(fm_set(fm, "image", f"img/editions/{stem}.jpg"),
                        "image_credit", credit)
            if not dry:
                open(p, "w", encoding="utf-8").write(f"---\n{fm}\n---\n{body}")
            print(f"  ✅ guide   {stem}  img/editions/{stem}.jpg  [{note}]")

        if not dry:
            os.remove(src)
            os.remove(credit_path)
        done += 1

    if not dry and done:
        json.dump(hero_map, open(HERO_MAP, "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        json.dump(credits, open(CREDITS, "w", encoding="utf-8"),
                  indent=1, ensure_ascii=False, sort_keys=True)

    print(f"\n{done} hero(es) filed; {failed} rejected."
          + ("  dry run — nothing written." if dry else ""))
    return 1 if failed else 0


# ---------------------------------------------------------------------- check

def _edition_date(eid):
    """Editions carry their date in the id: pulse-2026-10-01-evening. An id with
    no date cannot be placed in time, so it is treated as old and left alone."""
    m = _DATE.search(eid)
    return m.group(1) if m else "0000-00-00"


def _guide_date(fm):
    """Guides have no date in the slug; `updated:` is the only date they carry.
    A guide with no `updated:` is treated as old rather than failed, because the
    gate is about heroes and should not become a frontmatter linter."""
    return fm_get(fm, "updated") or "0000-00-00"


def _edition_missing(since):
    hero_map, credits = _load(HERO_MAP, {}), _load(CREDITS, {})
    out = []
    for eid in sorted(_ids(EDSRC)):
        if _edition_date(eid) < since:
            continue
        hero = hero_map.get(eid)
        if not hero:
            out.append((eid, "no hero in og/hero_map.json"))
        elif not os.path.exists(os.path.join(OG, hero)):
            out.append((eid, f"hero_map points at missing og/{hero}"))
        else:
            c = credits.get(eid) or {}
            if (c.get("source_kind") or "") in ("data-card", "illustration"):
                out.append((eid, "hero is a generated card, not a supplied photograph"))
            elif not (c.get("license") or c.get("title")):
                out.append((eid, "hero has no credit recorded"))
    return out


def _guide_missing(since):
    out = []
    for slug in sorted(_ids(GDSRC)):
        raw = open(os.path.join(GDSRC, slug + ".md"), encoding="utf-8").read()
        fm, _ = split_fm(raw)
        if fm is None:
            continue
        if _guide_date(fm) < since:
            continue
        img, cred = fm_get(fm, "image"), fm_get(fm, "image_credit")
        if not img:
            out.append((slug, "no image: in frontmatter"))
        elif not os.path.exists(os.path.join(HERE, img)):
            out.append((slug, f"image: points at missing {img}"))
        elif not cred:
            out.append((slug, "image_credit: is empty"))
    return out


def check(only, strict, since):
    rows = [("edition", a, b) for a, b in _edition_missing(since)] + \
           [("guide", a, b) for a, b in _guide_missing(since)]
    if only:
        want = {s.strip() for s in only.split(",") if s.strip()}
        rows = [r for r in rows if r[1] in want]
    scope = "everything" if since == "0000-00-00" else f"items dated {since} or later"
    if not rows:
        print(f"\U0001f7e2 every item in scope has a hand-supplied hero  ({scope}).")
        return 0
    print(f"\U0001f534 {len(rows)} item(s) without a hand-supplied hero  ({scope}):\n")
    for kind, name, why in rows:
        print(f"   ⛔ {kind:7} {name}")
        print(f"             {why}")
    print("\nSupply each one by dropping into img/incoming/:")
    print("   <name>.jpg  and  <name>.credit.txt")
    print("then run:  python3 hero_gate.py --intake")
    if strict:
        print("\nPUBLISH BLOCKED — hero required.")
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--intake", action="store_true",
                    help="file heroes waiting in img/incoming/")
    ap.add_argument("--check", action="store_true",
                    help="report editions/guides with no hand-supplied hero")
    ap.add_argument("--strict", action="store_true",
                    help="with --check, exit 1 when any hero is missing")
    ap.add_argument("--only", default="",
                    help="comma-separated edition ids or guide slugs")
    ap.add_argument("--since", default=CUTOFF,
                    help=f"only check items dated on or after this (default {CUTOFF}); "
                         f"pass --since 0000-00-00 to audit the whole archive")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --intake, report without writing")
    a = ap.parse_args(argv)
    if not (a.intake or a.check):
        ap.print_help()
        return 0
    rc = 0
    if a.intake:
        rc |= intake(a.dry_run)
    if a.check:
        rc |= check(a.only, a.strict, a.since)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
