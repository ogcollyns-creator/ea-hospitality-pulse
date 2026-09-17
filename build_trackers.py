#!/usr/bin/env python3
"""
EA Hospitality Pulse — static tracker pages.

WHY THIS EXISTS
---------------
Search Console, 1 Aug - 13 Sep 2026: the homepage took 1,156 of the site's
1,693 impressions at average position 7.15 and returned ONE click. The cause
is structural. Every live dataset on this site — the rate index, the rules and
fees register, the advisory board, the cost index, connectivity, the pipeline
and the MICE calendar — lived as an anchor section of index.html, rendered
client-side from window.RULES, window.RATE_INDEX and friends.

Two things follow from that, and both cost clicks:

1. A searcher asking "Uganda gorilla permit price" lands on a masthead, not on
   an answer. The page that ranked cannot possibly satisfy the query, so the
   click either never happens or bounces.
2. The content is assembled in JavaScript. Googlebot renders JS, so Google
   mostly sees it; ChatGPT, Perplexity and ClaudeBot mostly do not. The most
   citable, most factual material on the site was invisible to exactly the
   engines the GEO work was aimed at.

This builder fixes both. It evaluates the same data files through Node, then
writes the content into static HTML at a real URL per dataset, each with its
own title, description and Dataset schema. The homepage keeps its interactive
sections; these pages become the canonical home of each dataset.

Run: python3 build_trackers.py   (or let build_site.py call build())
"""
import os, re, json, html, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TDIR = os.path.join(HERE, "trackers")

import build_site as BS          # BASE, ARTICLE_CSS, org_node, ORG_ID, SITE_ID

BASE = BS.BASE
ORG_ID, SITE_ID = BS.ORG_ID, BS.SITE_ID

# Data files are plain `window.X = {...}` assignments. They are JS, not JSON —
# unquoted keys, comments, trailing commas — so evaluate them in a real JS
# engine rather than trying to regex a parser into existence.
_NODE_DUMP = """
const fs=require('fs'), vm=require('vm');
const sandbox={window:{},console:{log(){},warn(){},error(){}}};
sandbox.window.window=sandbox.window;
vm.createContext(sandbox);
for(const f of process.argv.slice(2)){
  try{ vm.runInContext(fs.readFileSync(f,'utf8'),sandbox,{filename:f}); }
  catch(e){ console.error('ERR '+f+': '+e.message); }
}
const out={};
for(const k of Object.keys(sandbox.window)) if(k!=='window') out[k]=sandbox.window[k];
process.stdout.write(JSON.stringify(out));
"""

DATA_FILES = ["rules.js", "advisories.js", "costs.js", "connectivity.js",
              "pipeline.js", "mice.js", "rates.js"]


def load_data():
    """Evaluate the window.* data files and return them as plain dicts."""
    script = os.path.join(HERE, ".trackerdump.js")
    open(script, "w", encoding="utf-8").write(_NODE_DUMP)
    paths = [os.path.join(HERE, f) for f in DATA_FILES if os.path.exists(os.path.join(HERE, f))]
    try:
        r = subprocess.run(["node", script] + paths, capture_output=True, text=True, timeout=90)
        if r.stderr.strip():
            print("  tracker data warnings:", r.stderr.strip()[:200])
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except Exception as ex:
        print("  tracker data load failed:", ex)
        return {}
    finally:
        try: os.remove(script)
        except OSError: pass


# The `updated` fields carry a date followed by a full editorial log of what the
# sweep did and did not find. That log is genuinely useful provenance, but a
# page needs the date, and dateModified needs it in ISO form.
_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August",
     "September","October","November","December"], 1)}


def updated_date(raw):
    """('17 September 2026 (morning — ...)') -> ('17 September 2026', '2026-09-17')."""
    s = re.sub(r"\s+", " ", str(raw or "")).strip()
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m:
        d, mon, y = int(m.group(1)), _MONTHS.get(m.group(2).lower()), int(m.group(3))
        if mon:
            return m.group(0), f"{y:04d}-{mon:02d}-{d:02d}"
    return (s.split("(")[0].strip() or "—"), datetime.date.today().isoformat()


def updated_note(raw):
    """The parenthetical sweep log, if there is one — provenance a reader can audit."""
    s = re.sub(r"\s+", " ", str(raw or "")).strip()
    m = re.search(r"\((.*)\)\s*$", s, re.S)
    if not m:
        return ""
    # The data files use '|' where a comma would sit, to stay inside a JS string.
    return m.group(1).replace("|", ",").strip()


def esc(x):
    return html.escape("" if x is None else str(x))


def strip_emoji(t):
    return re.sub(r"[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF️‍]", "", str(t or "")).strip()


def note_cell(text, limit=200):
    """Long notes stay in the HTML but stop swamping the row.

    <details> content is in the DOM, so Googlebot and answer engines still read
    it; the reader gets a scannable table and opens the detail if they want it."""
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if not t:
        return ""
    if len(t) <= limit:
        return f'<span class="tk-note">{esc(t)}</span>'
    m = re.match(r"(.{60,%d}?[.!?])\s" % limit, t)
    head = (m.group(1) if m else t[:limit].rsplit(" ", 1)[0] + "\u2026")
    return (f'<details class="tk-note"><summary>{esc(head)}</summary>'
            f'<span>{esc(t)}</span></details>')


def verified_chip(v, flagged=False):
    if flagged:
        return '<span class="chip chip-flag">Flagged</span>'
    return ('<span class="chip chip-ok">Verified</span>' if v
            else '<span class="chip chip-check">Re-check</span>')


def source_cell(src):
    s = str(src or "").strip()
    if not s:
        return "—"
    if s.startswith("http"):
        label = re.sub(r"^https?://(www\.)?", "", s).split("/")[0]
        return f'<a href="{esc(s)}" rel="nofollow noopener" target="_blank">{esc(label)}</a>'
    return esc(s)


TRACKER_CSS = """
.tk-meta{font:600 11px/1.6 var(--mono);letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin:0 0 18px;display:flex;flex-wrap:wrap;gap:6px 14px}
.tk-meta b{color:var(--teal-d);font-weight:700}
.tk-lede{font-size:1.14em;line-height:1.5;color:#3b4340;margin:0 0 22px;padding:0 0 18px;
  border-bottom:1px solid var(--line);text-wrap:pretty}
.tk-country{margin:30px 0 10px;font:700 12px/1 var(--mono);letter-spacing:.1em;
  text-transform:uppercase;color:var(--teal-d);padding-bottom:7px;
  border-bottom:2px solid var(--gold)}
.tk-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 6px}
table.tk{width:100%;min-width:560px;border-collapse:collapse;font-family:var(--sans);
  font-size:14px;display:table;margin:0 0 14px}
table.tk th{font:700 10.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;
  color:var(--teal-d);border-bottom:2px solid var(--gold);padding:9px 12px;text-align:left;
  vertical-align:bottom;white-space:nowrap}
table.tk td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top;
  line-height:1.5;white-space:normal}
table.tk tbody tr:last-child td{border-bottom:none}
table.tk td.num{font-family:var(--mono);font-size:13px;white-space:nowrap}
table.tk td.k{font-weight:600;min-width:170px}
.tk-note{display:block;color:var(--muted);font-size:13px;margin-top:4px;line-height:1.45}
details.tk-note>summary{cursor:pointer;list-style:none;color:var(--muted);
  border-bottom:1px dotted var(--line);padding-bottom:3px}
details.tk-note>summary::-webkit-details-marker{display:none}
details.tk-note>summary::after{content:" more";font:700 9.5px/1 var(--mono);
  letter-spacing:.08em;text-transform:uppercase;color:var(--gold-d);margin-left:5px}
details.tk-note[open]>summary::after{content:" less"}
details.tk-note>summary:hover{color:var(--teal-d)}
details.tk-note>span{display:block;margin-top:7px;padding-left:10px;
  border-left:2px solid var(--line)}
details.tk-note[open]>summary{border-bottom:none}
.chip{display:inline-block;font:700 9.5px/1.5 var(--mono);letter-spacing:.08em;
  text-transform:uppercase;padding:2px 7px;border-radius:var(--r-xs);border:1px solid}
.chip-ok{color:#0a5f3c;border-color:#0a5f3c}
.chip-check{color:var(--gold-d);border-color:var(--gold-d)}
.chip-flag{color:#9a3412;border-color:#9a3412}
.tk-dir-up{color:#0a5f3c;font-weight:700}
.tk-dir-down{color:#9a3412;font-weight:700}
.tk-prov{margin:26px 0 0;padding:16px 20px;background:var(--sand-2);
  border-left:3px solid var(--teal-d);border-radius:0 var(--r-sm) var(--r-sm) 0;
  font-family:var(--sans);font-size:13.5px;line-height:1.6;color:var(--muted)}
.tk-prov b{color:var(--ink);display:block;margin-bottom:5px;
  font:700 10.5px/1 var(--mono);letter-spacing:.1em;text-transform:uppercase}
.tk-sibs{margin:28px 0 0;padding-top:18px;border-top:1px solid var(--line)}
.tk-sibs h2{margin:0 0 10px;font:700 11px/1 var(--mono);letter-spacing:.1em;
  text-transform:uppercase;color:var(--teal-d)}
.tk-sibs ul{list-style:none;margin:0;padding:0;display:grid;gap:0;
  border-top:1px solid var(--line)}
.tk-sibs li{border-bottom:1px solid var(--line)}
.tk-sibs a{display:flex;align-items:baseline;gap:12px;padding:10px;
  font-family:var(--sans);color:var(--ink);border-left:2px solid transparent;
  transition:border-color .18s ease,background-color .18s ease,color .18s ease}
.tk-sibs a:hover{border-left-color:var(--gold);background:var(--sand-2);color:var(--teal-d)}
.tk-sibs .n{font:700 11px/1.6 var(--mono);letter-spacing:.06em;flex:0 0 auto;
  min-width:150px;color:var(--teal-d)}
.tk-sibs .d{font-size:13.5px;color:var(--muted);line-height:1.5}
.tk-api{font-family:var(--sans);font-size:13px;color:var(--muted);margin:16px 0 0}
.tk-api code{font-family:var(--mono);font-size:12.5px;background:var(--sand-2);
  padding:2px 6px;border-radius:var(--r-xs)}
@media(max-width:640px){
  .tk-sibs a{flex-direction:column;gap:2px}
  .tk-sibs .n{min-width:0}
  table.tk{font-size:13px}
}
@media (prefers-color-scheme: dark){
  .tk-lede{color:#b9c2bc}
  .chip-ok{color:#4ade80;border-color:#4ade80}
  .chip-check{color:var(--gold-d);border-color:var(--gold-d)}
  .chip-flag{color:#fb923c;border-color:#fb923c}
  .tk-dir-up{color:#4ade80}
  .tk-dir-down{color:#fb923c}
  .tk-prov{border-left-color:var(--gold)}
  .tk-prov b{color:var(--ink)}
  .tk-sibs .n{color:var(--gold-d)}
  .tk-sibs a{color:var(--ink)}
  .tk-sibs a:hover{background:#1b2521;color:var(--teal-d)}
  table.tk th{color:var(--gold-d)}
}
@media print{
  .tk-sibs,.tk-api{display:none!important}
  details.tk-note>span{display:block!important}
  details.tk-note>summary{display:none}
  table.tk{min-width:0;font-size:9.5pt}
  .tk-prov{background:none;border-left:1pt solid #999}
}
"""


def page_shell(t, body, ld_blocks):
    """One shell for every tracker, inheriting the edition typography and dark mode."""
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(b)}</script>'
                   for b in ld_blocks)
    sibs = "".join(
        f'<li><a href="{s["slug"]}.html"><span class="n">{esc(s["nav"])}</span>'
        f'<span class="d">{esc(s["blurb"])}</span></a></li>'
        for s in TRACKERS if s["slug"] != t["slug"])
    api_html = ""
    if t.get("api"):
        api_html = (f'<p class="tk-api">Machine-readable: '
                    f'<code><a href="../api/v1/{t["api"]}">/api/v1/{t["api"]}</a></code> · '
                    f'free to reuse with attribution, see <a href="../republish.html">syndication</a>.</p>')
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(t['title'])}</title>
<meta name="description" content="{esc(t['desc'])}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="EA Hospitality Pulse">
<link rel="canonical" href="{BASE}/trackers/{t['slug']}.html">
<meta name="theme-color" content="#0a4f48" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0d1512" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="../feed.xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="{esc(t['social'])}">
<meta property="og:description" content="{esc(t['desc'])}">
<meta property="og:url" content="{BASE}/trackers/{t['slug']}.html">
<meta property="og:image" content="{BASE}/og/default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(t['social'])}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(t['social'])}">
<meta name="twitter:description" content="{esc(t['desc'])}">
<meta name="twitter:image" content="{BASE}/og/default.png">
<meta name="twitter:image:alt" content="{esc(t['social'])}">
<link rel="icon" href="../favicon.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
{ld}
<style>{BS.ARTICLE_CSS}{TRACKER_CSS}</style></head>
<body>
<a class="skip" href="#content">Skip to the data</a>
<header class="s"><div class="wrap"><a href="/"><span class="logo" aria-hidden="true">EA</span><b>EA Hospitality Pulse</b></a></div></header>
<main class="wrap" id="content">
  <article class="art">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a>
      <span aria-hidden="true">/</span><a href="./index.html">Trackers</a>
      <span aria-hidden="true">/</span><span aria-current="page">{esc(t['nav'])}</span></nav>
    <h1>{esc(t['h1'])}</h1>
    <p class="tk-lede">{t['lede']}</p>
{body}
{api_html}
    <section class="tk-sibs" aria-label="Other trackers">
      <h2>Other live trackers</h2>
      <ul>{sibs}</ul>
    </section>
    <div class="sub">
      <h2 class="sub-h">Follow the Pulse</h2>
      <p class="sub-note">Every change to this tracker is reported in the daily brief.</p>
      <ul class="chan">
        <li><a href="{BS.CHANNELS['telegram']}" target="_blank" rel="noopener"><span class="chan-n">Telegram</span><span class="chan-d">The full edition, three times a day</span></a></li>
        <li><a href="{BS.CHANNELS['whatsapp']}" target="_blank" rel="noopener"><span class="chan-n">WhatsApp</span><span class="chan-d">The daily skim</span></a></li>
        <li><a href="../archive.html"><span class="chan-n">Archive</span><span class="chan-d">Every edition, searchable</span></a></li>
      </ul>
    </div>
  </article>
</main>
<footer class="s"><div class="wrap">
<p class="f-line">EA Hospitality Pulse — daily intelligence for city, bush and beach properties across East Africa. Free to read, free to republish with attribution.</p>
<p class="f-nav"><a href="../index.html">Home</a><a href="./index.html">Trackers</a><a href="../archive.html">Archive</a><a href="../methodology.html">Methodology</a><a href="../faq.html">FAQ</a><a href="../republish.html">Republish</a></p>
<p class="f-geo">Kenya &middot; Uganda &middot; Tanzania &middot; Zanzibar &middot; Rwanda</p>
</div></footer>
</body></html>"""


def dataset_ld(t, updated_iso, n_items, variables):
    node = {
        "@context": "https://schema.org", "@type": "Dataset",
        "@id": f"{BASE}/trackers/{t['slug']}.html#dataset",
        "name": t["dataset_name"], "description": t["dataset_desc"],
        "url": f"{BASE}/trackers/{t['slug']}.html",
        "creator": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
        "isPartOf": {"@id": SITE_ID},
        "license": f"{BASE}/republish.html",
        "isAccessibleForFree": True, "inLanguage": "en",
        "dateModified": updated_iso,
        "spatialCoverage": [a for a in BS.ABOUT_ENTITIES if a["@type"] == "Place"],
        "variableMeasured": variables,
        "creativeWorkStatus": "Published",
    }
    if n_items:
        node["size"] = f"{n_items} records"
    if t.get("api"):
        node["distribution"] = [{
            "@type": "DataDownload", "encodingFormat": "application/json",
            "contentUrl": f"{BASE}/api/v1/{t['api']}"}]
    return node


def crumbs_ld(t):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Trackers",
                 "item": f"{BASE}/trackers/index.html"},
                {"@type": "ListItem", "position": 3, "name": t["nav"],
                 "item": f"{BASE}/trackers/{t['slug']}.html"}]}


def meta_line(shown, extra=None):
    bits = [f'Updated <b>{esc(shown)}</b>']
    for e in (extra or []):
        bits.append(esc(e))
    bits.append('Free to republish with attribution')
    return '<p class="tk-meta">' + "".join(f"<span>{b}</span>" for b in bits) + "</p>"


def provenance(raw, standing):
    note = updated_note(raw)
    body = esc(note) if note else esc(standing)
    return f'<aside class="tk-prov"><b>How this is maintained</b>{body}</aside>'


# ---------------------------------------------------------------- renderers --
def r_rules(d, t):
    R = d.get("RULES") or {}
    shown, iso = updated_date(R.get("updated"))
    n = sum(len(g.get("items") or []) for g in R.get("groups") or [])
    out = [meta_line(shown, [f"{n} entries", f"{len(R.get('groups') or [])} jurisdictions"])]
    for g in R.get("groups") or []:
        items = g.get("items") or []
        if not items:
            continue
        out.append(f'<h2 class="tk-country" id="{re.sub(r"[^a-z0-9]+","-",strip_emoji(g.get("country","")).lower()).strip("-")}">'
                   f'{esc(strip_emoji(g.get("country")))}</h2>')
        rows = []
        for it in items:
            note = note_cell(it.get("note"))
            rows.append(
                f'<tr><td class="k">{esc(it.get("rule"))}{note}</td>'
                f'<td class="num">{esc(it.get("amount"))}</td>'
                f'<td>{esc(it.get("who"))}</td>'
                f'<td>{esc(it.get("effective"))}</td>'
                f'<td>{source_cell(it.get("source"))} {verified_chip(it.get("verified"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr>'
                   '<th>Rule, fee or levy</th><th>Amount</th><th>Who it applies to</th>'
                   '<th>Effective</th><th>Source</th></tr></thead><tbody>'
                   + "".join(rows) + "</tbody></table></div>")
    out.append(provenance(R.get("updated"),
        "Every entry is checked against the issuing authority — gazette, regulator notice or "
        "park authority tariff — and carries the source it was read from. Entries we have not "
        "re-confirmed inside the review window are marked Re-check rather than left looking current."))
    return "\n".join(out), iso, n


def r_advisories(d, t):
    A = d.get("ADVISORIES") or {}
    rows_in = A.get("rows") or []
    shown, iso = updated_date(A.get("updated"))
    out = [meta_line(shown, [f"{len(rows_in)} markets", "US State Dept + UK FCDO"])]
    rows = []
    for r in rows_in:
        us, uk = r.get("us") or {}, r.get("uk") or {}
        us_note = note_cell(us.get("note"), 240) or "\u2014"
        uk_note = note_cell(uk.get("note"), 240) or "\u2014"
        uk_level = uk.get("level") or uk.get("summary") or "See note"
        rows.append(
            f'<tr><td class="k">{esc(r.get("name"))}</td>'
            f'<td class="num">Level {esc(us.get("level"))}</td>'
            f'<td>{us_note}</td>'
            f'<td class="num">{esc(uk_level)}</td>'
            f'<td>{uk_note}</td></tr>')
    out.append('<div class="tk-wrap"><table class="tk"><thead><tr>'
               '<th>Country</th><th>US level</th><th>US position</th>'
               '<th>UK level</th><th>UK position</th></tr></thead><tbody>'
               + "".join(rows) + "</tbody></table></div>")
    links = A.get("links") or {}
    if isinstance(links, dict) and links:
        ls = " · ".join(f'<a href="{esc(v)}" rel="nofollow noopener" target="_blank">{esc(k)}</a>'
                        for k, v in links.items() if isinstance(v, str) and v.startswith("http"))
        if ls:
            out.append(f'<p class="tk-api">Official sources: {ls}</p>')
    out.append(provenance(A.get("updated"),
        "Levels are read directly from the US State Department and UK FCDO pages rather than "
        "from press reports, and reflect the main tourist areas — regional exceptions are stated "
        "in the notes. Verify against the official source before advising a guest."))
    return "\n".join(out), iso, len(rows_in)


def r_rates(d, t):
    RI = d.get("RATE_INDEX") or {}
    markets = RI.get("markets") or {}
    shown, iso = updated_date(RI.get("updated"))
    conv = RI.get("convention") or {}
    extra = [f"{RI.get('basketSize') or len(markets)} properties",
             f"{len(markets)} markets",
             f"{RI.get('totalObservations') or 0} observations"]
    out = [meta_line(shown, extra)]
    out.append(
        '<p class="tk-api">Booking convention held constant so movement reflects rate change, '
        f'not sample change: <b>{esc(conv.get("los"))}-night stay, {esc(conv.get("lead_days"))}-day lead time, '
        f'{esc(conv.get("occupancy"))}, {esc(conv.get("currency"))}</b>.</p>')
    rows = []
    for key, m in markets.items():
        series = [s for s in (m.get("series") or []) if s.get("median") is not None]
        if not series:
            continue
        last = series[-1]
        prev = series[-2] if len(series) > 1 else None
        mv = "—"
        if prev and prev.get("median"):
            pct = (last["median"] - prev["median"]) / prev["median"] * 100
            cls = "tk-dir-up" if pct >= 0 else "tk-dir-down"
            mv = f'<span class="{cls}">{pct:+.1f}%</span>'
        conf = ('<span class="chip chip-ok">Confident</span>' if last.get("confident")
                else '<span class="chip chip-check">Thin sample</span>')
        rows.append(
            f'<tr><td class="k">{esc(m.get("label"))}</td>'
            f'<td>{esc(str(m.get("segment") or "").title())}</td>'
            f'<td class="num">US${last["median"]:,.0f}</td>'
            f'<td class="num">{mv}</td>'
            f'<td class="num">{esc(last.get("n"))} of {esc(m.get("basketSize"))}</td>'
            f'<td class="num">{esc(last.get("week"))} {conf}</td></tr>')
    out.append('<div class="tk-wrap"><table class="tk"><thead><tr>'
               '<th>Market</th><th>Segment</th><th>Median lead-in rate</th>'
               '<th>Week on week</th><th>Sample</th><th>Week</th></tr></thead><tbody>'
               + "".join(rows) + "</tbody></table></div>")
    if RI.get("methodNote"):
        out.append(f'<p class="tk-api">{esc(RI["methodNote"])}</p>')
    out.append(provenance(RI.get("updated"),
        "A fixed basket, chain-linked property by property against its own previous observation, "
        "so a change in the index is a change in rate rather than a change in what was sampled. "
        "A market week below the minimum observation count is marked thin rather than hidden. "
        "Full detail on the Methodology page."))
    return "\n".join(out), iso, len(rows)


def r_costs(d, t):
    C = d.get("COSTS") or {}
    items = C.get("items") or []
    shown, iso = updated_date(C.get("updated"))
    out = [meta_line(shown, [f"{len(items)} indicators"])]
    by = {}
    for it in items:
        by.setdefault(it.get("group") or "Other", []).append(it)
    for grp, rows_in in by.items():
        out.append(f'<h2 class="tk-country">{esc(strip_emoji(grp))}</h2>')
        rows = []
        for it in rows_in:
            d_cls = {"up": "tk-dir-up", "down": "tk-dir-down"}.get(it.get("dir"), "")
            note = note_cell(it.get("note"))
            rows.append(
                f'<tr><td class="k">{esc(it.get("metric"))}{note}</td>'
                f'<td class="num">{esc(it.get("value"))}</td>'
                f'<td class="num"><span class="{d_cls}">{esc(it.get("change"))}</span></td>'
                f'<td class="num">{esc(it.get("period"))}</td>'
                f'<td>{source_cell(it.get("source"))} {verified_chip(it.get("verified"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr>'
                   '<th>Indicator</th><th>Latest</th><th>Change</th><th>Period</th>'
                   '<th>Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    out.append(provenance(C.get("updated"),
        "Every figure is attributed to a named official source and dated. Where a series is "
        "published on a lag, the period shown is the period the figure covers, not the date we read it."))
    return "\n".join(out), iso, len(items)


def r_connect(d, t):
    C = d.get("CONNECT") or {}
    traffic, routes = C.get("traffic") or [], C.get("routes") or []
    shown, iso = updated_date(C.get("updated"))
    out = [meta_line(shown, [f"{len(traffic)} airports", f"{len(routes)} route events"])]
    if traffic:
        out.append('<h2 class="tk-country">Official airport traffic</h2>')
        rows = []
        for a in traffic:
            d_cls = {"up": "tk-dir-up", "down": "tk-dir-down"}.get(a.get("dir"), "")
            note = note_cell(a.get("note"))
            rows.append(
                f'<tr><td class="k">{esc(strip_emoji(a.get("airport")))} ({esc(a.get("code"))}){note}</td>'
                f'<td>{esc(a.get("metric"))}</td><td class="num">{esc(a.get("value"))}</td>'
                f'<td class="num"><span class="{d_cls}">{esc(a.get("change"))}</span></td>'
                f'<td class="num">{esc(a.get("period"))}</td>'
                f'<td>{source_cell(a.get("source"))} {verified_chip(a.get("verified"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr><th>Airport</th>'
                   '<th>Metric</th><th>Latest</th><th>Change</th><th>Period</th>'
                   '<th>Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    if routes:
        out.append('<h2 class="tk-country">Confirmed route events</h2>')
        rows = []
        for r in routes:
            note = note_cell(r.get("impact"))
            rows.append(
                f'<tr><td class="k">{esc(r.get("route"))}{note}</td>'
                f'<td>{esc(r.get("carrier"))}</td><td>{esc(r.get("status"))}</td>'
                f'<td class="num">{esc(r.get("effective"))}</td>'
                f'<td>{esc(r.get("segment"))}</td><td>{source_cell(r.get("source"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr><th>Route</th>'
                   '<th>Carrier</th><th>Status</th><th>Effective</th><th>Segment</th>'
                   '<th>Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    out.append(provenance(C.get("updated"),
        "True seats-per-week data sits behind commercial aviation databases, so no seat count is "
        "published here that cannot be verified. What is tracked instead is official airport "
        "traffic, which is authoritative but lagging, and confirmed route events, which are "
        "forward-looking and actionable."))
    return "\n".join(out), iso, len(traffic) + len(routes)


def r_pipeline(d, t):
    P = d.get("PIPELINE") or {}
    markets, projects = P.get("markets") or [], P.get("projects") or []
    shown, iso = updated_date(P.get("updated"))
    out = [meta_line(shown, [f"{len(markets)} markets", f"{len(projects)} tracked projects"])]
    if markets:
        out.append('<h2 class="tk-country">Pipeline by market</h2>')
        rows = []
        for m in markets:
            note = note_cell(m.get("note"))
            rows.append(
                f'<tr><td class="k">{esc(m.get("country"))}{note}</td>'
                f'<td class="num">{esc(m.get("hotels"))}</td>'
                f'<td class="num">{esc(m.get("rooms"))}</td>'
                f'<td class="num">{esc(m.get("underConstruction"))}</td>'
                f'<td class="num">{esc(m.get("ucPct"))}%</td>'
                f'<td>{source_cell(m.get("source"))} {verified_chip(m.get("verified"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr><th>Market</th>'
                   '<th>Hotels</th><th>Rooms</th><th>Rooms under construction</th>'
                   '<th>Share building</th><th>Source</th></tr></thead><tbody>'
                   + "".join(rows) + "</tbody></table></div>")
    if projects:
        out.append('<h2 class="tk-country">Individually verified projects</h2>')
        rows = []
        for p in projects:
            note = note_cell(p.get("detail"))
            rows.append(
                f'<tr><td class="k">{esc(p.get("property"))}{note}</td>'
                f'<td>{esc(p.get("brand"))}</td><td>{esc(p.get("country"))}</td>'
                f'<td class="num">{esc(p.get("rooms"))}</td><td>{esc(p.get("status"))}</td>'
                f'<td class="num">{esc(p.get("opening"))}</td>'
                f'<td>{source_cell(p.get("source"))} {verified_chip(p.get("verified"), p.get("flagged"))}</td></tr>')
        out.append('<div class="tk-wrap"><table class="tk"><thead><tr><th>Property</th>'
                   '<th>Brand</th><th>Market</th><th>Rooms</th><th>Status</th>'
                   '<th>Opening</th><th>Source</th></tr></thead><tbody>'
                   + "".join(rows) + "</tbody></table></div>")
    if P.get("caveat"):
        out.append(f'<p class="tk-api">{esc(P["caveat"])}</p>')
    out.append(provenance(P.get("updated"),
        "Market totals come from the W Hospitality Group branded chain-pipeline benchmark; "
        "individual projects are separately sourced and verified. An announced project is not "
        "a built one, which is why rooms under construction is tracked separately from rooms announced."))
    return "\n".join(out), iso, len(markets) + len(projects)


def r_mice(d, t):
    M = d.get("MICE") or {}
    events = M.get("events") or []
    shown, iso = updated_date(M.get("updated"))
    out = [meta_line(shown, [f"{len(events)} tracked events"])]
    rows = []
    for e in events:
        note = note_cell(e.get("detail"))
        rows.append(
            f'<tr><td class="k">{esc(e.get("event"))}{note}</td>'
            f'<td>{esc(e.get("city"))}, {esc(e.get("country"))}</td>'
            f'<td class="num">{esc(e.get("dates"))}</td>'
            f'<td class="num">{esc(e.get("delegates") or "—")}</td>'
            f'<td>{esc(e.get("status"))} {verified_chip(e.get("verified"), e.get("flagged"))}</td>'
            f'<td>{source_cell(e.get("source"))}</td></tr>')
    out.append('<div class="tk-wrap"><table class="tk"><thead><tr><th>Event</th>'
               '<th>Host city</th><th>Dates</th><th>Delegates</th><th>Status</th>'
               '<th>Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    if M.get("caveat"):
        out.append(f'<p class="tk-api">{esc(M["caveat"])}</p>')
    out.append(provenance(M.get("updated"),
        "Not an exhaustive events calendar: every event here has been verified against an official "
        "host, convention bureau or organiser source. Delegate counts appear only where a named "
        "source states one — none are estimated."))
    return "\n".join(out), iso, len(events)


# ---------------------------------------------------------------- registry ---
# Titles and descriptions are written against queries the site is ALREADY being
# shown for. Search Console surfaced "lewa conservancy fees", "safari permit",
# "permit rates", "ota commission rates" and "hospitality trends east africa" —
# all of them landing on a homepage that could not answer them.
TRACKERS = [
    {"slug": "park-fees-and-levies", "render": r_rules, "api": "rules-and-fees.json",
     "nav": "Park fees & levies", "blurb": "Park, permit, visa and levy prices by country",
     "title": "East Africa park fees, permits & levies 2026 | EA Pulse",
     "social": "East Africa park fees, permits and levies — live tracker",
     "h1": "Park fees, permits, visas and levies across East Africa",
     "desc": "Park entry fees, gorilla and chimp permit prices, visa and ETA charges, bed "
             "levies and surcharges for Kenya, Uganda, Tanzania, Zanzibar and Rwanda.",
     "lede": "Every park entry fee, permit price, visa charge, bed levy and tourism surcharge we "
             "track across the five markets, with the authority it came from and the date it takes "
             "effect. Prices change by gazette notice and rarely with much warning, so anything we "
             "have not re-confirmed inside the review window is marked for re-checking rather than "
             "left looking current.",
     "dataset_name": "EA Pulse Rules, Fees & Levies Tracker",
     "dataset_desc": "A living register of entry rules, visa and ETA fees, park and permit prices, "
                     "levies and surcharges across Kenya, Uganda, Tanzania, Zanzibar and Rwanda, "
                     "each entry marked verified or flagged for re-confirmation against its official source.",
     "vars": ["Fee amount", "Effective date", "Who it applies to", "Verification status", "Applicable market"]},

    {"slug": "travel-advisories", "render": r_advisories, "api": "advisories.json",
     "nav": "Travel advisories", "blurb": "US and UK advisory levels, side by side",
     "title": "Kenya, Tanzania & Uganda travel advisory levels | EA Pulse",
     "social": "US & UK travel advisory levels for East Africa",
     "h1": "US and UK travel advisory levels for East Africa",
     "desc": "US State Department and UK FCDO advisory levels for Kenya, Uganda, Tanzania, "
             "Zanzibar and Rwanda, side by side, with the regional exceptions.",
     "lede": "The two advisories that actually move bookings, compared directly. Levels here reflect "
             "the main tourist areas; the regional exceptions are where the detail lives, and the two "
             "governments frequently disagree. Read the note before you answer a guest or a trade "
             "partner, and verify against the official source before advising on travel.",
     "dataset_name": "EA Pulse Travel Advisory Status Board",
     "dataset_desc": "US State Department and UK FCDO travel advisory levels for Kenya, Uganda, "
                     "Tanzania, Zanzibar and Rwanda, tracked with regional exceptions and revision dates.",
     "vars": ["US advisory level", "UK advisory position", "Regional exceptions", "Revision date"]},

    {"slug": "hotel-rate-index", "render": r_rates, "api": "rate-index.json",
     "nav": "Hotel rate index", "blurb": "Median lead-in rates across eleven markets",
     "title": "East Africa hotel rate index by market | EA Pulse",
     "social": "EA Pulse Rate Index — median hotel rates by market",
     "h1": "East Africa hotel rate index",
     "desc": "Median lead-in hotel, lodge and resort rates across eleven East African "
             "markets, tracked at a fixed booking convention. Updated weekly.",
     "lede": "A fixed basket of properties across eleven markets in Kenya, Uganda, Tanzania, "
             "Zanzibar and Rwanda, priced at an identical booking convention every time. Each "
             "property is chain-linked only against its own previous observation, which is what "
             "separates a genuine rate movement from a different set of hotels happening to be "
             "in the sample this week.",
     "dataset_name": "EA Pulse Rate Index",
     "dataset_desc": "A fixed basket of East African hotel, lodge and resort properties tracked at "
                     "a constant booking convention (2-night stay, 30-day lead time, 2 adults, USD), "
                     "chain-linked per property so index movement reflects genuine rate change.",
     "vars": ["Weekly median lead-in rate (USD)", "Sample coverage", "Week-on-week movement", "Confidence flag"]},

    {"slug": "cost-index", "render": r_costs, "api": "cost-index.json",
     "nav": "Cost index", "blurb": "Fuel, currency, energy and inflation pressure",
     "title": "East Africa hospitality cost index: fuel, FX | EA Pulse",
     "social": "EA Pulse Cost-Side Index — the margin pressure tracker",
     "h1": "The cost side: fuel, currency, energy and inflation",
     "desc": "Fuel prices, currency movements, energy tariffs and inflation across Kenya, "
             "Uganda, Tanzania, Zanzibar and Rwanda — the costs that decide a margin.",
     "lede": "Rate is only half of a margin. These are the input costs that decide the other half — "
             "fuel and diesel, the shilling and the franc, energy tariffs and the inflation running "
             "underneath them. Every figure carries the official source it came from and the period "
             "it covers, because several of these series publish on a long lag.",
     "dataset_name": "EA Pulse Cost-Side Index",
     "dataset_desc": "Weekly-tracked cost inputs affecting East African hospitality margins — fuel, "
                     "currency, energy and inflation across five markets, each figure attributed to "
                     "a named source and date.",
     "vars": ["Fuel price", "Currency rate", "Energy cost", "Inflation rate", "Reporting period"]},

    {"slug": "airport-traffic-and-routes", "render": r_connect, "api": None,
     "nav": "Connectivity", "blurb": "Airport traffic and confirmed route changes",
     "title": "East Africa airport traffic & route changes | EA Pulse",
     "social": "EA Pulse Connectivity Tracker — traffic and route events",
     "h1": "Airport traffic and airline route events",
     "desc": "Official passenger traffic for Nairobi, Entebbe, Kilimanjaro and Zanzibar plus "
             "confirmed airline route additions, cuts and suspensions across East Africa.",
     "lede": "Seats decide arrivals, and arrivals decide occupancy. True seats-per-week data sits "
             "behind commercial aviation databases, so nothing is published here that cannot be "
             "verified. What is tracked instead is official airport traffic, which is authoritative "
             "but lagging, and confirmed route events, which are forward-looking and actionable.",
     "dataset_name": "EA Pulse Connectivity Tracker",
     "dataset_desc": "Official airport traffic figures and confirmed airline route events across "
                     "East Africa's five markets.",
     "vars": ["Airport passenger traffic", "Reporting period", "Route event", "Effective date"]},

    {"slug": "hotel-development-pipeline", "render": r_pipeline, "api": "pipeline.json",
     "nav": "Development pipeline", "blurb": "Signings, openings and rooms under construction",
     "title": "East Africa hotel development pipeline | EA Pulse",
     "social": "EA Pulse Development Pipeline — new supply tracker",
     "h1": "East Africa hotel development pipeline",
     "desc": "Hotel signings, brand entries, rooms under construction and confirmed "
             "openings across Kenya, Uganda, Tanzania, Zanzibar and Rwanda.",
     "lede": "New supply is the slowest-moving threat to a rate strategy and the easiest to see "
             "coming. Market totals come from the branded chain-pipeline benchmark; individual "
             "projects are separately sourced. An announced project is not a built one, which is "
             "why rooms under construction is tracked apart from rooms announced.",
     "dataset_name": "EA Pulse Development Pipeline Tracker",
     "dataset_desc": "Hotel signings, brand entries, construction progress and openings across "
                     "Kenya, Uganda, Tanzania, Zanzibar and Rwanda.",
     "vars": ["Pipeline rooms", "Rooms under construction", "Share under construction",
              "Project status", "Anticipated opening year", "Operating brand"]},

    {"slug": "mice-calendar", "render": r_mice, "api": "mice.json",
     "nav": "MICE calendar", "blurb": "Conferences and expos that compress room stock",
     "title": "East Africa conference & MICE calendar 2026 | EA Pulse",
     "social": "EA Pulse MICE Calendar — the compression events",
     "h1": "East Africa conference and MICE calendar",
     "desc": "Confirmed conferences, congresses and trade expos across Nairobi, Kigali, "
             "Kampala, Dar es Salaam and Zanzibar, with dates and delegate counts.",
     "lede": "The compression events — the conferences and congresses that take a city's or an "
             "island's room stock for several nights at a time. This is not an exhaustive calendar: "
             "every event here has been verified against an official host, convention bureau or "
             "organiser. Delegate counts appear only where a named source states one.",
     "dataset_name": "EA Pulse MICE Events Tracker",
     "dataset_desc": "Confirmed conferences, congresses, trade expos and awards ceremonies across "
                     "Kenya, Uganda, Tanzania, Zanzibar and Rwanda, with dates, venue, delegate "
                     "counts where sourced, and status.",
     "vars": ["Event name", "Host city and country", "Dates", "Expected delegates", "Status"]},
]


def hub_page(built):
    rows = "".join(
        f'<li><a href="{b["slug"]}.html"><span class="n">{esc(b["nav"])}</span>'
        f'<span class="d">{esc(b["desc"])}</span></a></li>' for b in built)
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage",
           "@id": f"{BASE}/trackers/index.html", "url": f"{BASE}/trackers/index.html",
           "name": "EA Hospitality Pulse live trackers",
           "description": "Live datasets for East African hospitality: park and permit fees, "
                          "travel advisory levels, hotel rate index, cost-side index, airport "
                          "traffic, development pipeline and the MICE calendar.",
           "inLanguage": "en", "isPartOf": {"@id": SITE_ID}, "publisher": {"@id": ORG_ID},
           "about": BS.ABOUT_ENTITIES,
           "mainEntity": {"@type": "ItemList", "numberOfItems": len(built),
                          "itemListElement": [
                              {"@type": "ListItem", "position": i + 1, "name": b["nav"],
                               "url": f"{BASE}/trackers/{b['slug']}.html"}
                              for i, b in enumerate(built)]}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
               {"@type": "ListItem", "position": 2, "name": "Trackers",
                "item": f"{BASE}/trackers/index.html"}]}]
    t = {"slug": "index", "nav": "Trackers",
         "title": "Live East Africa hospitality data trackers | EA Pulse",
         "social": "EA Hospitality Pulse — live data trackers",
         "h1": "Live trackers",
         "desc": "Seven live datasets for East African hospitality: park and permit fees, "
                 "travel advisories, hotel rates, costs, air traffic, pipeline and MICE.",
         "lede": "Seven datasets, maintained daily, each with its own page, its own sources and a "
                 "free JSON endpoint. Every figure carries the authority it was read from and the "
                 "date it was confirmed.",
         "api": None}
    body = f'<section class="tk-sibs" style="border-top:none;padding-top:0"><ul>{rows}</ul></section>'
    page = page_shell(t, body, ld)
    # the hub lists every tracker, so drop the redundant sibling rail
    page = re.sub(r'<section class="tk-sibs" aria-label="Other trackers">.*?</section>',
                  "", page, flags=re.S)
    return page


def build():
    d = load_data()
    if not d:
        print("trackers skipped: no data")
        return []
    os.makedirs(TDIR, exist_ok=True)
    built = []
    for t in TRACKERS:
        try:
            body, iso, n = t["render"](d, t)
        except Exception as ex:
            print(f"  tracker {t['slug']} skipped: {ex}")
            continue
        ld = [dataset_ld(t, iso, n, t["vars"]), crumbs_ld(t)]
        open(os.path.join(TDIR, t["slug"] + ".html"), "w", encoding="utf-8").write(
            page_shell(t, body, ld))
        built.append({"slug": t["slug"], "nav": t["nav"], "desc": t["blurb"],
                      "updated": iso, "records": n})
    if built:
        open(os.path.join(TDIR, "index.html"), "w", encoding="utf-8").write(hub_page(built))
    print(f"Trackers built: {len(built)} pages + hub "
          f"({sum(b['records'] for b in built)} records rendered into static HTML)")
    return built


if __name__ == "__main__":
    build()
