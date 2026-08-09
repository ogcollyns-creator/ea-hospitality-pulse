#!/usr/bin/env python3
"""
Build filtered RSS feeds from search-index.json.

Personalisation without accounts: a reader who only cares about Zanzibar beach
subscribes to feeds/znz.xml in whatever reader they already use. No login, no
stored preference on our side, no personal data.

Emits one feed per country and one per segment, plus an index page listing them.
"""
import os, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "site_config.json")))
BASE = CFG["base"]
IDX = json.load(open(os.path.join(HERE, "search-index.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "feeds")
os.makedirs(OUT, exist_ok=True)

NAMES = IDX["countryNames"]
now = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def rfc822(d):
    try:
        return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 08:00:00 GMT")
    except Exception:
        return now

def feed(fname, title, desc, records):
    items = []
    for r in records[:40]:
        link = f"{BASE}/{r['url']}"
        tags = ", ".join(r["countries"] + r["segments"] + r["topics"][:3])
        items.append(
            "  <item>\n"
            f"    <title>{html.escape(r['title'])}</title>\n"
            f"    <link>{html.escape(link)}</link>\n"
            f"    <guid isPermaLink=\"true\">{html.escape(link)}</guid>\n"
            f"    <pubDate>{rfc822(r['date'])}</pubDate>\n"
            f"    <category>{html.escape(r['kind'])}</category>\n"
            f"    <description>{html.escape(r['text'][:400] + '…')} [{html.escape(tags)}]</description>\n"
            "  </item>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        f"  <title>{html.escape(title)}</title>\n"
        f"  <link>{BASE}/archive.html</link>\n"
        f"  <description>{html.escape(desc)}</description>\n"
        "  <language>en</language>\n"
        f"  <lastBuildDate>{now}</lastBuildDate>\n"
        f'  <atom:link href="{BASE}/feeds/{fname}" rel="self" type="application/rss+xml"/>\n'
        + "\n".join(items) + "\n</channel>\n</rss>\n"
    )
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(xml)
    return len(items)

built = []
for cc, name in NAMES.items():
    recs = [r for r in IDX["records"] if cc in r["countries"]]
    if recs:
        n = feed(f"{cc.lower()}.xml", f"EA Hospitality Pulse — {name}",
                 f"Every EA Hospitality Pulse item touching {name}.", recs)
        built.append((f"{cc.lower()}.xml", name, n))

for seg in ["Bush", "City", "Beach", "Trade"]:
    recs = [r for r in IDX["records"] if seg in r["segments"]]
    if recs:
        n = feed(f"{seg.lower()}.xml", f"EA Hospitality Pulse — {seg}",
                 f"Every EA Hospitality Pulse item tagged {seg}.", recs)
        built.append((f"{seg.lower()}.xml", seg, n))

rows = "\n".join(
    f'<tr><td><a href="feeds/{f}">{f}</a></td><td>{n}</td><td>{c} items</td></tr>'
    for f, n, c in built)
print(f"feeds built: {len(built)}")
for f, n, c in built:
    print(f"  feeds/{f:<12} {n:<12} {c} items")
