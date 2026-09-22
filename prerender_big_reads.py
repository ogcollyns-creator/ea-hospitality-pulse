#!/usr/bin/env python3
"""
EA Hospitality Pulse — server-render the Big Reads index.

WHY THIS EXISTS
---------------
big-reads.html used to ship an empty grid plus the line "No Big Reads
published yet", and filled the grid from guides.js in the browser. Anything
that does not run JavaScript — link-preview bots (WhatsApp, LinkedIn, email
clients), RSS readers, and most AI answer engines (ChatGPT, Perplexity,
ClaudeBot) — therefore saw an EMPTY section even when seven Big Reads were
live. Same diagnosis as build_trackers.py, same fix: write the cards into the
static HTML at build time. The in-page script still runs and re-renders the
same cards from guides.js, so nothing changes for a normal browser.

Run: python3 prerender_big_reads.py   (build_site.py calls render() after guides)
"""
import os, re, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "big-reads.html")
BASE = "https://eahospitalitypulse.com"
START, END = "<!--BR_SSR-->", "<!--/BR_SSR-->"


def load_index():
    raw = open(os.path.join(HERE, "guides.js"), encoding="utf-8").read()
    raw = raw.strip()
    raw = raw[raw.index("["): raw.rindex("]") + 1]
    return json.loads(raw)


def big_reads(index=None):
    idx = index if index is not None else load_index()
    br = [g for g in idx if (g.get("category") or "").strip().lower() == "big read"]
    br.sort(key=lambda g: g.get("updated") or "", reverse=True)
    return br


def _date(d):
    try:
        x = datetime.date.fromisoformat(d)
        return f"{x.day} {x.strftime('%b %Y')}"
    except Exception:
        return d or ""


def card(g):
    e = html.escape
    thumb = (f'<img class="thumb" src="{e(g["image"])}" alt="" loading="lazy">'
             if g.get("image") else '<div class="thumb"></div>')
    return (f'<a class="br-card" href="guides/{e(g["slug"])}">{thumb}'
            f'<div class="body"><span class="cat">Big Read</span>'
            f'<h3>{e(g["title"])}</h3><p>{e(g.get("description", ""))}</p>'
            f'<div class="meta">{_date(g.get("updated"))} · {g.get("readMins", "")} min read</div>'
            f'<div class="read">Read the Big Read →</div></div></a>')


def item_list(brs):
    return {"@context": "https://schema.org", "@type": "ItemList",
            "@id": f"{BASE}/big-reads#list", "name": "EA Hospitality Pulse Big Reads",
            "numberOfItems": len(brs),
            "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                 "url": f"{BASE}/guides/{g['slug']}", "name": g["title"]}
                                for i, g in enumerate(brs)]}


def render(index=None):
    brs = big_reads(index)
    s = open(PAGE, encoding="utf-8").read()
    cards = "".join(card(g) for g in brs)
    block = START + cards + END
    if START in s:
        s = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: block, s, count=1, flags=re.S)
    else:
        s = s.replace('<div class="grid" id="grid"></div>', f'<div class="grid" id="grid">{block}</div>', 1)
    n = len(brs)
    count = f"{n} Big Read" + ("" if n == 1 else "s") if n else ""
    s = re.sub(r'(<span class="count-note" id="count">)[^<]*(</span>)', lambda m: m.group(1) + count + m.group(2), s, count=1)
    # When Big Reads exist, ship the empty-state box with NO text: text-only
    # readers (link previews, AI crawlers, markdown converters) ignore
    # display:none and were reporting "No Big Reads published yet".
    empty_txt = "" if n else "No Big Reads published yet \u2014 check back soon."
    s = re.sub(r'<div class="empty" id="empty" style="display:[a-z]+">[^<]*</div>',
               lambda m: f'<div class="empty" id="empty" style="display:{"none" if n else "block"}">{empty_txt}</div>',
               s, count=1)
    ld = '<script type="application/ld+json" id="br-itemlist">' + json.dumps(item_list(brs), ensure_ascii=False) + '</script>'
    if 'id="br-itemlist"' in s:
        s = re.sub(r'<script type="application/ld\+json" id="br-itemlist">.*?</script>', lambda m: ld, s, count=1, flags=re.S)
    else:
        # in <body>, not <head>: build_site.polish_static_heads() only adds its
        # CollectionPage/Breadcrumb schema when the head carries no JSON-LD yet
        s = s.replace("</body>", ld + "\n</body>", 1)
    open(PAGE, "w", encoding="utf-8").write(s)
    print(f"Big Reads pre-rendered: {n}")
    return brs


if __name__ == "__main__":
    render()
