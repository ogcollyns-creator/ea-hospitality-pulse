#!/usr/bin/env python3
"""
EA Hospitality Pulse — site builder.
Scans editions-src/*.md and regenerates data.js (window.EDITIONS + window.INSIGHTS).
INSIGHTS are individual 🏷-tagged items pulled out of each edition, so the
homepage segment cards (City / Bush / Beach) can show segment-specific insights.
Run: python build_site.py
"""
import os, re, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "editions-src")

EDITION_LABELS = {
    "morning": "Morning Brief", "midday": "Midday Pulse",
    "evening": "Evening Wrap", "inaugural": "Inaugural Edition",
    "foresight": "Sunday Foresight",
}
KEYCAP = re.compile(r"^([0-9]️?⃣)\s*")

def parse_filename(fn):
    base = fn.rsplit(".", 1)[0]
    m = re.search(r"(\d{4}-\d{2}-\d{2})", base)
    date_iso = m.group(1) if m else None
    key = "morning"
    low = base.lower()
    for k in EDITION_LABELS:
        if k in low:
            key = k; break
    if low.startswith("foresight"):
        key = "foresight"
    return date_iso, key

def extract_telegram(md):
    parts = re.split(r"\n##+\s*", "\n" + md)
    for p in parts:
        head = p.strip().split("\n", 1)[0].strip().upper()
        if head.startswith("TELEGRAM"):
            return (p.split("\n", 1)[1] if "\n" in p else "").strip()
    return md.strip()

def segments_from_tag(tagfield):
    t = tagfield.lower()
    segs = []
    if "all segment" in t:
        return ["city", "bush", "beach"]
    if "city" in t: segs.append("city")
    if "bush" in t: segs.append("bush")
    if "beach" in t or "coast" in t: segs.append("beach")
    return segs

def parse_items(telegram):
    """Return list of insight dicts from the numbered, 🏷-tagged items."""
    items, cur = [], None
    for raw in telegram.split("\n"):
        l = raw.strip()
        if not l:
            continue
        if KEYCAP.match(l):
            if cur:
                items.append(cur)
            cur = {"headline": KEYCAP.sub("", l), "body": [], "sowhat": "", "tags": ""}
        elif cur is not None:
            if l.startswith("🎯"):
                cur["sowhat"] = l
            elif l.startswith("🏷"):
                cur["tags"] = l.replace("🏷", "").strip()
                items.append(cur); cur = None
            elif l[0] in "━📡💬📅🏨":
                items.append(cur); cur = None
            else:
                cur["body"].append(l)
    if cur:
        items.append(cur)
    out = []
    for it in items:
        if not it.get("tags"):
            continue
        fields = [f.strip() for f in it["tags"].split("|")]
        segs = segments_from_tag(fields[0] if fields else "")
        if not segs:
            continue
        out.append({
            "headline": it["headline"],
            "body": " ".join(it["body"]).strip(),
            "sowhat": it["sowhat"].strip(),
            "segments": segs,
            "countries": fields[1] if len(fields) > 1 else "",
            "confidence": fields[2] if len(fields) > 2 else "",
        })
    return out

def render_body(text):
    out = []
    for blk in re.split(r"\n\s*\n", text):
        blk = blk.strip()
        if not blk:
            continue
        if set(blk) <= set("━—-–_ "):
            out.append('<hr class="divider">'); continue
        rendered = []
        for l in [x.strip() for x in blk.split("\n") if x.strip()]:
            e = html.escape(l)
            if KEYCAP.match(l):
                e = f'<span class="item-head">{e}</span>'
            elif l.startswith("🎯"):
                e = f'<span class="sowhat">{e}</span>'
            elif l.startswith("🏷"):
                e = f'<span class="tagline">{e}</span>'
            elif l[0] in "📡📅💬🏨":
                e = f'<span class="meta-line">{e}</span>'
            elif l.startswith("▪️"):
                e = f'<span class="radar-item">{e}</span>'
            rendered.append(e)
        out.append("<p>" + "<br>".join(rendered) + "</p>")
    return "\n".join(out)

def summarise(text):
    for l in text.split("\n"):
        l = l.strip()
        if l and not l.startswith(("🏨", "📅", "━", "#")) and len(l) > 40:
            return re.sub(r"\s+", " ", l)[:200]
    return "East Africa hospitality intelligence."

def load_existing():
    try:
        d = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
        m = re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
        return {e["id"]: e for e in json.loads(m.group(1))} if m else {}
    except Exception:
        return {}

def main():
    existing = load_existing()
    editions, insights = [], []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".md"):
            continue
        date_iso, key = parse_filename(fn)
        if not date_iso:
            continue
        md = open(os.path.join(SRC, fn), encoding="utf-8").read()
        tele = extract_telegram(md)
        try:
            date_disp = datetime.date.fromisoformat(date_iso).strftime("%A, %-d %B %Y")
        except Exception:
            date_disp = date_iso
        eid = fn.rsplit(".", 1)[0]
        editions.append({
            "id": eid, "date": date_iso, "dateDisplay": date_disp,
            "edition": EDITION_LABELS.get(key, "Brief"), "editionKey": key,
            "summary": summarise(tele), "bodyHtml": render_body(tele),
        })
        for it in parse_items(tele):
            it.update({"source": eid, "date": date_iso, "dateDisplay": date_disp,
                       "edition": EDITION_LABELS.get(key, "Brief"), "editionKey": key})
            insights.append(it)
    built_ids = {e["id"] for e in editions}
    for eid, e in existing.items():
        if eid not in built_ids:
            editions.append(e)
    editions.sort(key=lambda e: (e["date"], e["id"]), reverse=True)
    insights.sort(key=lambda i: (i["date"], i["source"]), reverse=True)
    with open(os.path.join(HERE, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.EDITIONS = " + json.dumps(editions, ensure_ascii=False, indent=1) + ";\n")
        f.write("window.INSIGHTS = " + json.dumps(insights, ensure_ascii=False, indent=1) + ";\n")
        f.write("window.BUILT_AT = " + json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + ";\n")
    print(f"Built data.js: {len(editions)} editions, {len(insights)} insights.")

if __name__ == "__main__":
    main()
