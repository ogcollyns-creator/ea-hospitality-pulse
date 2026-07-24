#!/usr/bin/env python3
"""
EA Hospitality Pulse — site builder.
Scans editions-src/*.md (the pulse-YYYY-MM-DD-*.md and foresight-YYYY-MM-DD.md files
the scheduled task produces) and regenerates data.js, which the website reads.

Run:  python build_site.py
The scheduled task can call this after saving each new edition so the archive
updates itself. No server or database required.
"""
import os, re, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "editions-src")

EDITION_LABELS = {
    "morning": "Morning Brief", "midday": "Midday Pulse",
    "evening": "Evening Wrap", "inaugural": "Inaugural Edition",
    "foresight": "Sunday Foresight",
}

def parse_filename(fn):
    """Return (date_iso, edition_key) from a filename, or (None, None)."""
    base = fn.rsplit(".", 1)[0]
    m = re.search(r"(\d{4}-\d{2}-\d{2})", base)
    date_iso = m.group(1) if m else None
    key = "morning"
    low = base.lower()
    for k in EDITION_LABELS:
        if k in low:
            key = k
            break
    if low.startswith("foresight"):
        key = "foresight"
    return date_iso, key

def extract_telegram(md):
    """Pull the TELEGRAM section (the full flagship brief) as the web article source."""
    # sections separated by lines like '## TELEGRAM'
    parts = re.split(r"\n##+\s*", "\n" + md)
    tele = None
    for p in parts:
        head = p.strip().split("\n", 1)[0].strip().upper()
        if head.startswith("TELEGRAM"):
            tele = p.split("\n", 1)[1] if "\n" in p else ""
            break
    if tele is None:
        # fall back to whole doc minus front matter
        tele = md
    return tele.strip()

def render_body(text):
    """Convert the Telegram-formatted brief into clean, styled HTML."""
    out = []
    # normalise divider lines
    blocks = re.split(r"\n\s*\n", text)
    for blk in blocks:
        blk = blk.strip()
        if not blk:
            continue
        if set(blk) <= set("━—-–_ "):  # divider row
            out.append('<hr class="divider">')
            continue
        lines = [l.strip() for l in blk.split("\n") if l.strip()]
        rendered = []
        for l in lines:
            e = html.escape(l)
            # numbered item headline: starts with a keycap digit emoji
            if re.match(r"^[0-9]️?⃣", l) or re.match(r"^[1-9][️⃣]", l):
                e = f'<span class="item-head">{e}</span>'
            elif l.startswith("🎯"):
                e = f'<span class="sowhat">{e}</span>'
            elif l.startswith("🏷"):
                e = f'<span class="tagline">{e}</span>'
            elif l.startswith("📡") or l.startswith("📅") or l.startswith("💬") or l.startswith("🏨"):
                e = f'<span class="meta-line">{e}</span>'
            elif l.startswith("▪️"):
                e = f'<span class="radar-item">{e}</span>'
            rendered.append(e)
        out.append("<p>" + "<br>".join(rendered) + "</p>")
    return "\n".join(out)

def summarise(text):
    """First substantive sentence for the archive teaser."""
    for l in text.split("\n"):
        l = l.strip()
        if l and not l.startswith(("🏨", "📅", "━", "#")) and len(l) > 40:
            return re.sub(r"\s+", " ", l)[:200]
    return "East Africa hospitality intelligence."

def main():
    editions = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".md"):
            continue
        date_iso, key = parse_filename(fn)
        if not date_iso:
            continue
        with open(os.path.join(SRC, fn), encoding="utf-8") as f:
            md = f.read()
        tele = extract_telegram(md)
        try:
            d = datetime.date.fromisoformat(date_iso)
            date_disp = d.strftime("%A, %-d %B %Y")
        except Exception:
            date_disp = date_iso
        editions.append({
            "id": fn.rsplit(".", 1)[0],
            "date": date_iso,
            "dateDisplay": date_disp,
            "edition": EDITION_LABELS.get(key, "Brief"),
            "editionKey": key,
            "summary": summarise(tele),
            "bodyHtml": render_body(tele),
        })
    # newest first
    editions.sort(key=lambda e: (e["date"], e["id"]), reverse=True)
    data = "window.EDITIONS = " + json.dumps(editions, ensure_ascii=False, indent=1) + ";\n"
    data += "window.BUILT_AT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n"
    with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
        f.write(data)
    print(f"Built data.js with {len(editions)} edition(s).")

if __name__ == "__main__":
    main()
