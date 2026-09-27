#!/usr/bin/env python3
"""
Crawlable directory layer: the part of the site a search engine or an AI answer
engine can read WITHOUT running JavaScript.

Why this exists (27 Sep 2026): the archive page rendered every link client-side,
so a crawler saw an archive with zero edition links; the homepage exposed two.
Google's AI answer for "East Africa hospitality news" rejected the site as
"lacking an indexed historical directory". This script fixes that by writing:

  1. archive.html   - a static, month-by-month index of every edition and guide
                      (between <!--DIR:ARCHIVE--> markers), plus an ItemList of all.
  2. topics/*.html  - one hub per market (Kenya, Uganda, Tanzania, Zanzibar,
                      Rwanda, Ethiopia) and per beat (aviation, advisories, hotel
                      development, MICE, regulation & fees, costs, health, security,
                      conservation, distribution & rates), each answer-first, with
                      CollectionPage / ItemList / Breadcrumb JSON-LD.
  3. topics/index.html - the directory of hubs.
  4. index.html     - a static "Browse by market / Recent editions" block.
  5. sitemap.xml    - hub URLs appended; sitemap-news.xml for the last 48 hours.
  6. robots.txt     - adds the news sitemap.
  7. llms.txt       - a hubs block.
  8. verification meta + IndexNow key file, when configured in site_config.json.

Run after build_site.py (it reads editions/*.html, guides/*.html, search-index.json).
Idempotent: every injection sits between markers and is replaced on each run.
"""
import os, re, sys, json, html, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "site_config.json"), encoding="utf-8"))
BASE = (CFG.get("base") or "https://eahospitalitypulse.com").rstrip("/")
BRAND = CFG.get("brand", "EA Hospitality Pulse")
CH = CFG.get("channels", {})
TODAY = datetime.date.today().isoformat()
ORG_ID, SITE_ID = BASE + "/#org", BASE + "/#website"

# ------------------------------------------------------------------ hubs
# Terms are matched case-insensitively against the edition's full text. A
# document joins a hub when the terms appear at least `min` times (or in its
# headline). This is deliberately stricter than the archive's topic chips, which
# tag almost everything with almost everything.
MARKETS = [
    ("kenya", "Kenya", ["kenya", "nairobi", "mombasa", "maasai mara", "masai mara",
                        "diani", "lamu", "jkia", "kws", "tourism fund", "kenyan"], 4,
     "Kenya is East Africa's largest hotel market and its busiest aviation hub. This page collects every "
     "EA Hospitality Pulse brief, Big Read and guide on Kenyan hospitality: Nairobi city hotels, the "
     "Maasai Mara and safari circuit, the Mombasa, Diani, Watamu and Lamu coast, travel advisories, "
     "tourism levies and park fees, JKIA and Kenya Airways connectivity, MICE and the hotel development pipeline."),
    ("uganda", "Uganda", ["uganda", "kampala", "entebbe", "bwindi", "murchison", "ugandan",
                          "ucaa", "uwa"], 4,
     "Coverage of Uganda's hotel and tourism market: Kampala and Entebbe city hotels, gorilla-permit "
     "and national park economics (Bwindi, Murchison Falls, Queen Elizabeth), Entebbe traffic data, "
     "Uganda Airlines, US and UK travel advisories and the Ebola-related entry restrictions, and the "
     "branded pipeline arriving in Kampala."),
    ("tanzania", "Tanzania", ["tanzania", "arusha", "serengeti", "ngorongoro", "kilimanjaro",
                              "dar es salaam", "tanapa", "tanzanian"], 4,
     "Coverage of mainland Tanzania's hospitality market: the northern safari circuit (Serengeti, "
     "Ngorongoro, Tarangire, Arusha), Kilimanjaro and Dar es Salaam, park concession fees and levies, "
     "entry rules including mandatory insurance, airline route changes and lodge openings."),
    ("zanzibar", "Zanzibar", ["zanzibar", "stone town", "nungwi", "paje", "pemba"], 3,
     "Coverage of Zanzibar's beach and heritage hotel market: record arrivals data, the mandatory "
     "inbound insurance and levies, new resort supply, airline capacity into Zanzibar and competition "
     "with rival Indian Ocean destinations."),
    ("rwanda", "Rwanda", ["rwanda", "kigali", "volcanoes national park", "akagera", "rdb",
                          "rwandair", "rwandan"], 4,
     "Coverage of Rwanda's high-value tourism model: Kigali's MICE and conference hotels, gorilla "
     "permits and Volcanoes National Park, Akagera, RwandAir connectivity, RDB regulation and grading, "
     "and advisories linked to the eastern DRC border."),
    ("ethiopia", "Ethiopia", ["ethiopia", "addis ababa", "bole", "ethiopian airlines",
                              "tigray", "amhara", "lalibela"], 4,
     "Ethiopia is tracked as a comparator and transmission market for East African hospitality: "
     "Addis Ababa's hotel construction boom, Ethiopian Airlines' hub and route network into Entebbe, "
     "Kigali, Kilimanjaro and Zanzibar, and the security advisories on the northern regions."),
]
BEATS = [
    ("travel-advisories", "Travel advisories", ["advisory", "advisories", "fcdo", "state department",
                                                "level 2", "level 3", "level 4", "do not travel"], 5,
     "How US, UK, Canadian, German and French travel advisories on Kenya, Uganda, Tanzania, Zanzibar "
     "and Rwanda change, what each level actually does to insurance, groups and corporate travel, and "
     "what properties should tell buyers. Pair with the live advisory board.", "trackers/travel-advisories"),
    ("aviation", "Aviation and air connectivity", ["airline", "route", "flights", "airport", "aviation",
                                                   "kenya airways", "rwandair", "uganda airlines", "seats"], 6,
     "New routes, suspensions, frequencies, airport traffic statistics and airline strategy affecting "
     "hotel demand in East Africa, from Kenya Airways and Ethiopian to Gulf and European carriers.",
     "trackers/airport-traffic-and-routes"),
    ("hotel-development", "Hotel development and openings", ["pipeline", "opening", "opens", "signing",
                                                             "rooms", "marriott", "hilton", "accor",
                                                             "radisson", "ihg", "hyatt", "under construction"], 6,
     "Hotel signings, openings, acquisitions and the branded development pipeline in East Africa: which "
     "brands are entering Nairobi, Kampala, Kigali, Arusha and Zanzibar, how much supply is under "
     "construction, and what it means for existing properties.", "trackers/hotel-development-pipeline"),
    ("mice-and-events", "MICE, conferences and events", ["conference", "congress", "summit", "expo",
                                                         "mice", "delegates", "afcon", "convention"], 5,
     "Conferences, congresses, expos, sporting events (including AFCON 2027) and awards that move room "
     "demand in East Africa, with dates, venues and sourced delegate counts.", "trackers/mice-calendar"),
    ("fees-levies-regulation", "Park fees, levies and regulation", ["levy", "levies", "park fee",
                                                                    "permit", "gazette", "legal notice",
                                                                    "licence", "license", "regulation", "tax"], 6,
     "Park and permit fees, tourism levies, licensing and grading rules, taxes and gazette notices that "
     "change what East African properties pay and charge.", "trackers/park-fees-and-levies"),
    ("costs-and-currency", "Operating costs, energy and currency", ["fuel", "electricity", "tariff",
                                                                    "shilling", "exchange rate", "inflation",
                                                                    "epra", "central bank", "wage"], 5,
     "Fuel, electricity tariffs, exchange rates, wages and inflation: the cost lines that move hotel "
     "and lodge margins in Kenya, Uganda, Tanzania and Rwanda.", "trackers/cost-index"),
    ("health-and-outbreaks", "Health, outbreaks and entry rules", ["ebola", "outbreak", "who ", "mpox",
                                                                   "cholera", "screening", "vaccination",
                                                                   "africa cdc"], 5,
     "Disease outbreaks, WHO and Africa CDC bulletins, screening and entry restrictions, and how they "
     "translate into cancellations, insurance and recovery timelines for East African hospitality.", None),
    ("security", "Security and crisis response", ["security", "attack", "protest", "unrest",
                                                  "terror", "election", "curfew", "fighting"], 5,
     "Security incidents, election risk and unrest, and the operator protocols that limit booking damage "
     "in East Africa.", None),
    ("conservation-and-safari", "Safari, parks and conservation", ["conservancy", "wildlife", "safari",
                                                                  "national park", "gorilla", "migration",
                                                                  "conservation", "lodge"], 6,
     "Safari lodges and camps, conservancies, wildlife events, gorilla trekking and conservation policy "
     "across the East African bush circuit.", None),
    ("distribution-and-rates", "Distribution, rates and demand", ["ota", "booking.com", "expedia",
                                                                 "adr", "revpar", "occupancy", "rate index",
                                                                 "commission", "tour operator"], 5,
     "Room rates, occupancy, OTA commission and distribution strategy, source-market demand and "
     "contracting for East African hotels and lodges.", "trackers/hotel-rate-index"),
]

STYLE = """<style>
:root{--sand:#f6f1e7;--ink:#1f2421;--muted:#6b6656;--gold:#c8892f;--teal-d:#0a4f48;--line:#e2d8c4;--card:#fffdf9;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,Cambria,serif;color:var(--ink);background:var(--sand);line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}a{color:var(--teal-d)}
header.s{background:var(--teal-d);color:#fff;padding:14px 0;border-bottom:3px solid var(--gold)}header.s a{color:#fff;text-decoration:none;font-weight:700}
main{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:22px auto;padding:26px 30px}
h1{font-size:clamp(24px,3.4vw,31px);line-height:1.2;margin:6px 0 12px;border-bottom:2px solid var(--gold);padding-bottom:12px}
h2{font-size:20px;margin:28px 0 8px}.lede{font-size:17px}
.crumbs{font:13px var(--sans);color:var(--muted)}.crumbs a{color:var(--muted)}
ul.idx{list-style:none;padding:0;margin:0}ul.idx li{padding:9px 0;border-bottom:1px dashed var(--line)}
ul.idx time{font:12px var(--sans);color:var(--muted);display:inline-block;min-width:92px}
ul.idx .k{font:11px var(--sans);text-transform:uppercase;letter-spacing:.06em;color:#a86f1f;margin-left:6px}
.chips a{display:inline-block;margin:0 6px 8px 0;padding:5px 11px;border:1px solid var(--line);border-radius:18px;font:13px var(--sans);text-decoration:none;background:#fff}
footer.s{text-align:center;color:var(--muted);font:12px var(--sans);padding:22px}
@media (prefers-color-scheme:dark){:root{--sand:#0d1512;--ink:#e6e3d8;--muted:#98a29c;--teal-d:#5fc9b8;--line:#26302c;--card:#121a17}header.s{background:#0a100e}.chips a{background:#18211e}}
</style>"""


def esc(s):
    return html.escape(s or "", quote=True)


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def page_meta(path):
    """Headline + description straight from the built page, which is what a
    reader and a crawler actually see."""
    try:
        t = open(path, encoding="utf-8").read()
    except OSError:
        return None, None, ""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    ds = re.search(r'<meta name="description" content="([^"]*)"', t)
    dt = re.search(r'<meta property="article:(?:modified|published)_time" content="(\d{4}-\d{2}-\d{2})', t)
    return (strip_tags(h1.group(1)) if h1 else None,
            html.unescape(ds.group(1)) if ds else None,
            dt.group(1) if dt else "")


def load_docs():
    idx = json.load(open(os.path.join(HERE, "search-index.json"), encoding="utf-8"))
    docs = []
    for r in idx.get("records", []):
        url = r["url"].strip("/")
        path = os.path.join(HERE, url + ".html")
        title, desc, pdate = page_meta(path)
        if not os.path.exists(path):
            continue
        kind = r.get("kind", "")
        if url.startswith("guides/"):
            kind = "Big Read" if "Big Read" in (open(path, encoding="utf-8").read()[:20000]) else "Guide"
        label = (r.get("slot") + " " if r.get("slot") and kind == "Daily brief" else "") + \
                ("brief" if kind == "Daily brief" else kind)
        docs.append({
            "url": url, "date": r.get("date") or pdate or TODAY, "kind": kind,
            "label": {"Morning brief": "Morning Brief", "Midday brief": "Midday Pulse",
                      "Evening brief": "Evening Wrap", "brief": "Daily brief"}.get(label, label),
            "title": title or r.get("title") or url,
            "desc": desc or "",
            "text": (r.get("text") or "").lower(),
            "countries": r.get("countries", []),
        })
    docs.sort(key=lambda d: (d["date"], d["url"]), reverse=True)
    return docs


def matches(doc, terms, minimum):
    n = sum(doc["text"].count(t) for t in terms)
    in_title = any(t in doc["title"].lower() for t in terms)
    return in_title or n >= minimum, n + (10 if in_title else 0)


def li(d):
    return (f'<li><time datetime="{d["date"]}">{d["date"]}</time> '
            f'<a href="/{d["url"]}">{esc(d["title"])}</a><span class="k">{esc(d["label"])}</span></li>')


def itemlist(name, docs):
    return {"@type": "ItemList", "name": name, "numberOfItems": len(docs),
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "itemListElement": [{"@type": "ListItem", "position": i + 1,
                                 "url": f'{BASE}/{d["url"]}', "name": d["title"]}
                                for i, d in enumerate(docs)]}


def hub_page(slug, name, heading, lede, docs, tracker, related):
    url = f"{BASE}/topics/{slug}"
    top = sorted(docs, key=lambda d: -d["score"])[:5]
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": url, "url": url,
          "name": heading, "description": lede, "inLanguage": "en-GB",
          "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": ORG_ID},
          "dateModified": docs[0]["date"] if docs else TODAY,
          "about": {"@type": "Thing", "name": name},
          "mainEntity": itemlist(heading, docs)}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Topics", "item": BASE + "/topics/"},
        {"@type": "ListItem", "position": 3, "name": name, "item": url}]}
    latest = docs[0]["date"] if docs else TODAY
    parts = [f"""<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(heading)} | {esc(BRAND)}</title>
<meta name="description" content="{esc(lede[:300])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(BRAND)}">
<meta property="og:title" content="{esc(heading)}"><meta property="og:description" content="{esc(lede[:300])}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/og/default.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{esc(BRAND)}" href="/feed.xml">
<link rel="icon" href="/favicon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumbs, ensure_ascii=False)}</script>
{STYLE}</head><body>
<header class="s"><div class="wrap"><a href="/">{esc(BRAND)}</a></div></header>
<main class="wrap">
<nav class="crumbs"><a href="/">Home</a> / <a href="/topics/">Topics</a> / {esc(name)}</nav>
<h1>{esc(heading)}</h1>
<p class="lede">{esc(lede)}</p>
<p class="crumbs">{len(docs)} briefs, Big Reads and guides · latest update {latest} · every figure traced to a named, dated source.</p>"""]
    if tracker:
        parts.append(f'<p><a href="/{tracker}"><strong>Live dataset →</strong> the tracker behind this page</a>, updated as sources change.</p>')
    if top:
        parts.append("<h2>Most substantial coverage</h2><ul class=\"idx\">" + "".join(li(d) for d in top) + "</ul>")
    parts.append(f"<h2>Every {esc(name)} item, newest first</h2><ul class=\"idx\">" + "".join(li(d) for d in docs) + "</ul>")
    parts.append("<h2>Related</h2><div class=\"chips\">" +
                 "".join(f'<a href="/topics/{s}">{esc(n)}</a>' for s, n in related) +
                 '<a href="/archive">Full archive</a><a href="/big-reads">Big Reads</a><a href="/trackers/">Live trackers</a></div>')
    parts.append(f"""</main>
<footer class="s">{esc(BRAND)} — daily, source-verified hospitality intelligence for Kenya, Uganda, Tanzania, Zanzibar and Rwanda.<br>
<a href="/">Home</a> · <a href="/archive">Archive</a> · <a href="/topics/">Topics</a> · <a href="/methodology">Methodology</a> · <a href="{esc(CH.get('telegram','#'))}">Telegram</a> · <a href="{esc(CH.get('linkedin','#'))}">LinkedIn</a></footer>
</body></html>""")
    return "\n".join(parts)


def replace_block(text, tag, block, anchor=None, before=True):
    start, end = f"<!--DIR:{tag}-->", f"<!--/DIR:{tag}-->"
    full = f"{start}\n{block}\n{end}"
    if start in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: full, text, flags=re.S)
    if anchor and anchor in text:
        return text.replace(anchor, (full + "\n" + anchor) if before else (anchor + "\n" + full), 1)
    return text


def main():
    docs = load_docs()
    os.makedirs(os.path.join(HERE, "topics"), exist_ok=True)
    hubs = []  # (slug, name, heading, count, latest)

    all_hubs = [(s, n, f"{n} hospitality news and analysis", t, m, l, None) for s, n, t, m, l in MARKETS] + \
               [(s, n, f"{n} in East African hospitality", t, m, l, tr) for s, n, t, m, l, tr in BEATS]
    related_pool = [(h[0], h[1]) for h in all_hubs]
    for slug, name, heading, terms, minimum, lede, tracker in all_hubs:
        sel = []
        for d in docs:
            ok, score = matches(d, terms, minimum)
            if ok:
                sel.append(dict(d, score=score))
        if not sel:
            continue
        related = [r for r in related_pool if r[0] != slug][:8]
        open(os.path.join(HERE, "topics", slug + ".html"), "w", encoding="utf-8").write(
            hub_page(slug, name, heading, lede, sel, tracker, related))
        hubs.append((slug, name, heading, len(sel), sel[0]["date"]))

    # topics/index.html
    idx_url = BASE + "/topics/"
    idx_ld = {"@context": "https://schema.org", "@type": "CollectionPage", "@id": idx_url, "url": idx_url,
              "name": "East African hospitality topics and markets", "isPartOf": {"@id": SITE_ID},
              "publisher": {"@id": ORG_ID},
              "mainEntity": {"@type": "ItemList", "numberOfItems": len(hubs), "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": f"{BASE}/topics/{h[0]}", "name": h[2]}
                  for i, h in enumerate(hubs)]}}
    rows = "".join(f'<li><a href="/topics/{h[0]}">{esc(h[2])}</a> <span class="k">{h[3]} items · updated {h[4]}</span></li>' for h in hubs)
    open(os.path.join(HERE, "topics", "index.html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>East African hospitality news by market and topic | {esc(BRAND)}</title>
<meta name="description" content="Directory of {esc(BRAND)} coverage by market (Kenya, Uganda, Tanzania, Zanzibar, Rwanda, Ethiopia) and by beat: advisories, aviation, hotel development, MICE, fees and levies, costs, health, security, safari and rates.">
<link rel="canonical" href="{idx_url}"><meta name="robots" content="index,follow">
<link rel="icon" href="/favicon.png">
<script type="application/ld+json">{json.dumps(idx_ld, ensure_ascii=False)}</script>
{STYLE}</head><body>
<header class="s"><div class="wrap"><a href="/">{esc(BRAND)}</a></div></header>
<main class="wrap"><nav class="crumbs"><a href="/">Home</a> / Topics</nav>
<h1>East African hospitality news by market and topic</h1>
<p class="lede">{esc(BRAND)} publishes daily, source-verified intelligence for hotels, lodges, camps and resorts in Kenya, Uganda, Tanzania, Zanzibar and Rwanda, with Ethiopia tracked as a comparator market. Every brief, Big Read and guide since July 2026 is indexed below by market and by beat.</p>
<ul class="idx">{rows}</ul>
<p class="chips"><a href="/archive">Full archive by month</a><a href="/big-reads">Big Reads</a><a href="/trackers/">Live trackers</a><a href="/feed.xml">RSS</a></p>
</main><footer class="s"><a href="/">Home</a> · <a href="/archive">Archive</a> · <a href="/methodology">Methodology</a></footer></body></html>""")

    # archive.html static directory (months)
    arc_path = os.path.join(HERE, "archive.html")
    if os.path.exists(arc_path):
        arc = open(arc_path, encoding="utf-8").read()
        by_month = {}
        for d in docs:
            by_month.setdefault(d["date"][:7], []).append(d)
        blocks = []
        for ym in sorted(by_month, reverse=True):
            label = datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
            blocks.append(f'<h3 id="m-{ym}">{label} <span class="k">({len(by_month[ym])})</span></h3>'
                          f'<ul class="idx">' + "".join(li(d) for d in by_month[ym]) + "</ul>")
        hub_links = "".join(f'<a class="chip" href="/topics/{h[0]}">{esc(h[1])}</a>' for h in hubs)
        block = (f'<section id="directory" class="panel" style="padding:18px 22px">'
                 f'<h2 style="margin-top:0">Full index: all {len(docs)} editions, Big Reads and guides</h2>'
                 f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:13.5px;color:var(--muted)">Browse by market or topic: </p>'
                 f'<div class="chips">{hub_links}</div>'
                 f'<style>#directory ul.idx{{list-style:none;padding:0}}#directory li{{padding:6px 0;border-bottom:1px dashed #e2d8c4;font-size:15px}}'
                 f'#directory time{{font:12px Helvetica,Arial,sans-serif;color:#6b6656;display:inline-block;min-width:92px}}'
                 f'#directory .k{{font:11px Helvetica,Arial,sans-serif;text-transform:uppercase;color:#a86f1f;margin-left:6px}}</style>'
                 + "".join(blocks) + "</section>")
        arc = replace_block(arc, "ARCHIVE", block, anchor="</div>\n<footer>")
        open(arc_path, "w", encoding="utf-8").write(arc)

    # index.html: static browse block + verification meta
    home = os.path.join(HERE, "index.html")
    if os.path.exists(home):
        h = open(home, encoding="utf-8").read()
        recent = [d for d in docs if not d["url"].startswith("guides/")][:20]
        block = ('<section id="browse" class="wrap" style="padding:30px 0 6px">'
                 '<div class="section-head"><div><div class="kicker">Browse the record</div>'
                 '<h2>East African hospitality news by market and topic</h2></div></div>'
                 '<p class="chips">' + "".join(f'<a class="chip" href="topics/{x[0]}" style="margin:0 6px 8px 0;display:inline-block">{esc(x[1])}</a>' for x in hubs) +
                 '<a class="chip" href="archive" style="display:inline-block">Full archive →</a></p>'
                 '<h3 style="margin:18px 0 8px">Recent editions</h3><ul style="padding-left:18px;line-height:1.7">' +
                 "".join(f'<li><a href="{d["url"]}">{esc(d["title"])}</a> <small>({d["date"]}, {esc(d["label"])})</small></li>' for d in recent) +
                 '</ul></section>')
        h = replace_block(h, "BROWSE", block, anchor='<section id="about"')
        meta = ""
        if CFG.get("google_site_verification"):
            meta += f'<meta name="google-site-verification" content="{esc(CFG["google_site_verification"])}">\n'
        if CFG.get("bing_site_verification"):
            meta += f'<meta name="msvalidate.01" content="{esc(CFG["bing_site_verification"])}">\n'
        if meta:
            h = replace_block(h, "VERIFY", meta.strip(), anchor="</head>")
        open(home, "w", encoding="utf-8").write(h)

    # sitemap.xml: add hubs; sitemap-news.xml: last 48h
    sm_path = os.path.join(HERE, "sitemap.xml")
    if os.path.exists(sm_path):
        sm = open(sm_path, encoding="utf-8").read()
        sm = re.sub(r"\s*<url><loc>[^<]*/topics/[^<]*</loc>.*?</url>", "", sm)
        add = [f"  <url><loc>{BASE}/topics/</loc><lastmod>{TODAY}</lastmod><changefreq>daily</changefreq></url>"]
        add += [f"  <url><loc>{BASE}/topics/{x[0]}</loc><lastmod>{x[4]}</lastmod><changefreq>daily</changefreq></url>" for x in hubs]
        sm = sm.replace("</urlset>", "\n".join(add) + "\n</urlset>")
        open(sm_path, "w", encoding="utf-8").write(sm)
    cutoff = (datetime.date.today() - datetime.timedelta(days=2)).isoformat()
    news = [d for d in docs if d["date"] >= cutoff and not d["url"].startswith("guides/")]
    nx = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    for d in news:
        nx.append(f'  <url><loc>{BASE}/{d["url"]}</loc><news:news><news:publication><news:name>{esc(BRAND)}</news:name>'
                  f'<news:language>en</news:language></news:publication><news:publication_date>{d["date"]}</news:publication_date>'
                  f'<news:title>{esc(d["title"])}</news:title></news:news></url>')
    nx.append("</urlset>")
    open(os.path.join(HERE, "sitemap-news.xml"), "w", encoding="utf-8").write("\n".join(nx))
    rb_path = os.path.join(HERE, "robots.txt")
    if os.path.exists(rb_path):
        rb = open(rb_path, encoding="utf-8").read()
        if "sitemap-news.xml" not in rb:
            rb = rb.rstrip("\n") + f"\nSitemap: {BASE}/sitemap-news.xml\n"
            open(rb_path, "w", encoding="utf-8").write(rb)

    # llms.txt hubs block
    ll_path = os.path.join(HERE, "llms.txt")
    if os.path.exists(ll_path):
        ll = open(ll_path, encoding="utf-8").read()
        blk = ("## Coverage by market and topic (auto-updated " + TODAY + ")\n" +
               "\n".join(f"- [{x[2]}]({BASE}/topics/{x[0]}): {x[3]} items, latest {x[4]}" for x in hubs) +
               f"\n- [Full archive, every edition by month]({BASE}/archive)")
        if "<!--DIR:HUBS-->" in ll:
            ll = re.sub(r"<!--DIR:HUBS-->.*?<!--/DIR:HUBS-->", lambda m: f"<!--DIR:HUBS-->\n{blk}\n<!--/DIR:HUBS-->", ll, flags=re.S)
        else:
            ll = ll.replace("## Editions", f"<!--DIR:HUBS-->\n{blk}\n<!--/DIR:HUBS-->\n\n## Editions", 1)
        open(ll_path, "w", encoding="utf-8").write(ll)

    # IndexNow key file (Bing, Yandex, Seznam, Naver; Bing feeds ChatGPT search and Copilot)
    key = CFG.get("indexnow_key")
    if key and re.fullmatch(r"[A-Za-z0-9-]{8,128}", key):
        open(os.path.join(HERE, key + ".txt"), "w").write(key)

    print(f"directory: {len(docs)} docs indexed, {len(hubs)} hubs, {len(news)} in news sitemap")

    # The build workflow commits an explicit file list that predates these outputs
    # and omits archive.html, big-reads.html, feeds/, llms.txt, robots.txt,
    # search-index.json, api/ and trackers/, so those went stale between manual
    # pushes. Stage everything the build produced; the workflow's
    # `git diff --staged` then commits it. (__pycache__ is gitignored.)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        import subprocess
        subprocess.run(["git", "add", "-A"], cwd=HERE, check=False)
        subprocess.run([sys.executable, os.path.join(HERE, "ping_indexnow.py")], check=False)


if __name__ == "__main__":
    main()
