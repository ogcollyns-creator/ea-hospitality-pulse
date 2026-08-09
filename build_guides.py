#!/usr/bin/env python3
"""
Build evergreen guides from guides-src/*.md into guides/*.html + guides.js.

Guides are deliberately NOT editions:
  - schema.org Article, not NewsArticle (no time-sensitivity signal to Google)
  - an "Updated" date, not a "Published" one, so refreshing a guide is a positive
  - stable slugs, so a guide keeps its URL and accumulated ranking across rewrites

Called by build_site.py. Safe to run standalone for testing.
"""
import os, re, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "guides-src")
OUT = os.path.join(HERE, "guides")

_cfg_path = os.path.join(HERE, "site_config.json")
try:
    _CFG = json.load(open(_cfg_path, encoding="utf-8"))
except Exception:
    _CFG = {}
BASE = (_CFG.get("base") or "https://eahospitalitypulse.com").rstrip("/")
CHANNELS = _CFG.get("channels") or {}


# ---------------------------------------------------------------- markdown
def _inline(t):
    """Inline markdown -> HTML. Escapes first, so source text can't inject markup."""
    t = html.escape(t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*([^*\n]+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"`([^`\n]+?)`", r"<code>\1</code>", t)
    return t


def render_md(md):
    """Compact block-level markdown renderer: headings, lists, tables, quotes, rules."""
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if not s:
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}|\*{3,}", s):
            out.append("<hr>")
            i += 1
            continue

        # headings
        m = re.match(r"^(#{2,4})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            text = _inline(m.group(2))
            anchor = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")
            out.append(f'<h{lvl} id="{anchor}">{text}</h{lvl}>')
            i += 1
            continue

        # table (needs a header row then a |---| separator)
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]
            head = cells(s)
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(cells(lines[i]))
                i += 1
            th = "".join(f"<th>{_inline(c)}</th>" for c in head)
            tr = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
            continue

        # blockquote
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + _inline(" ".join(buf)) + "</blockquote>")
            continue

        # lists
        if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
            ordered = bool(re.match(r"^\d+\.\s+", s))
            pat = r"^\d+\.\s+" if ordered else r"^[-*]\s+"
            items = []
            while i < len(lines) and re.match(pat, lines[i].strip()):
                items.append(_inline(re.sub(pat, "", lines[i].strip())))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue

        # paragraph (consume until blank line)
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{2,4}\s|[-*]\s|\d+\.\s|>|\|)", lines[i].strip()) and not re.fullmatch(
                r"-{3,}|\*{3,}", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>" + _inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


# ---------------------------------------------------------------- parsing
def parse_guide(path):
    raw = open(path, encoding="utf-8").read()
    meta, body = {}, raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"').strip("'")
        body = m.group(2)
    slug = meta.get("slug") or os.path.basename(path).rsplit(".", 1)[0]
    return {
        "slug": slug,
        "title": meta.get("title", slug),
        "description": meta.get("description", ""),
        "category": meta.get("category", "Guide"),
        "updated": meta.get("updated", datetime.date.today().isoformat()),
        "author": meta.get("author", ""),          # blank = published under the masthead
        "authorRole": meta.get("author_role", ""),
        "readMins": max(3, round(len(body.split()) / 220)),
        "bodyHtml": render_md(body),
    }


# ---------------------------------------------------------------- page
GUIDE_CSS = """
:root{--sand:#f6f1e7;--ink:#1f2421;--muted:#6b6656;--gold:#c8892f;--gold-d:#a86f1f;--teal:#0f6d63;--teal-d:#0a4f48;--line:#e2d8c4;--sand-2:#efe7d6;--card:#fffdf9}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,Cambria,serif;color:var(--ink);background:var(--sand);line-height:1.65}
.wrap{max-width:780px;margin:0 auto;padding:0 20px}
a{color:var(--teal-d)}
header.s{background:linear-gradient(135deg,var(--teal-d),var(--teal));color:#fff;padding:14px 0;border-bottom:4px solid var(--gold)}
header.s .wrap{display:flex;align-items:center;gap:10px}
header.s .logo{width:34px;height:34px;border-radius:8px;background:var(--gold);display:grid;place-items:center;font-size:18px}
header.s b{font-size:16px}
header.s a{color:#fff;text-decoration:none}
.art{background:var(--card);margin:24px auto;border:1px solid var(--line);border-radius:14px;padding:30px 34px 38px}
.nav{font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;font-weight:600;margin:0 0 10px;display:inline-block}
.cat{font-family:Helvetica Neue,Arial,sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:4px 9px;border-radius:20px;background:var(--sand-2);color:var(--gold-d)}
.upd{font-family:Helvetica Neue,Arial,sans-serif;font-size:13px;color:var(--muted);margin-left:8px}
.art h1{font-size:29px;line-height:1.22;margin:16px 0 14px;border-bottom:2px solid var(--gold);padding-bottom:14px}
.lede{font-size:18px;color:#3a423c;margin:0 0 20px}
.byline{font-family:Helvetica Neue,Arial,sans-serif;font-size:13.5px;color:var(--muted);margin:8px 0 0}
.art h2{font-size:22px;margin:30px 0 10px;line-height:1.3}
.art h3{font-size:18px;margin:22px 0 8px}
.art p{margin:0 0 15px}
.art ul,.art ol{margin:0 0 15px;padding-left:22px}
.art li{margin:0 0 7px}
blockquote{margin:18px 0;background:var(--sand-2);border-left:4px solid var(--gold);padding:12px 16px;border-radius:0 6px 6px 0;font-family:Helvetica Neue,Arial,sans-serif;font-size:15px}
code{background:var(--sand-2);padding:1px 5px;border-radius:4px;font-size:14px}
.tw{overflow-x:auto;margin:0 0 16px}
table{border-collapse:collapse;width:100%;font-family:Helvetica Neue,Arial,sans-serif;font-size:14.5px}
th,td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}
th{background:var(--sand-2);font-weight:700}
hr{border:none;border-top:1px dashed var(--line);margin:26px 0}
.sub{font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;color:var(--muted);margin-top:26px;border-top:1px solid var(--line);padding-top:18px;line-height:1.9}
.sub a{font-weight:600;margin-right:14px}
footer.s{text-align:center;color:var(--muted);font-family:Helvetica Neue,Arial,sans-serif;font-size:12px;padding:22px}
.art h1{letter-spacing:-.005em}
@media(max-width:640px){
  .wrap{padding:0 16px}
  .art{padding:22px 18px 28px;margin:16px auto;border-radius:12px}
  .art h1{font-size:24px}
  .lede{font-size:16.5px}
  .art h2{font-size:20px}
  table{font-size:13.5px}
}
"""


def guide_page(g):
    url = f"{BASE}/guides/{g['slug']}.html"
    author_obj = ({"@type": "Person", "name": g["author"]} if g.get("author")
                  else {"@type": "Organization", "name": "EA Hospitality Pulse", "url": BASE + "/"})
    ld = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": g["title"][:110], "description": g["description"],
        "datePublished": g["updated"], "dateModified": g["updated"],
        "url": url, "mainEntityOfPage": url,
        "image": [f"{BASE}/og/default.png"], "inLanguage": "en", "isAccessibleForFree": True,
        "author": author_obj,
        "publisher": {"@type": "Organization", "name": "EA Hospitality Pulse",
                      "logo": {"@type": "ImageObject", "url": BASE + "/apple-touch-icon.png"}},
        "about": ["Kenya", "Uganda", "Tanzania", "Zanzibar", "Rwanda", "hospitality", "tourism"],
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Guides", "item": BASE + "/#guides"},
            {"@type": "ListItem", "position": 3, "name": g["title"], "item": url},
        ]}
    upd = g["updated"]
    try:
        upd = datetime.date.fromisoformat(g["updated"]).strftime("%-d %B %Y")
    except Exception:
        pass
    byline_html = ""
    if g.get("author"):
        role = (", " + html.escape(g["authorRole"])) if g.get("authorRole") else ""
        byline_html = ('\n    <p class="byline">By <b>' + html.escape(g["author"]) + '</b>'
                       + role + ' — guest contributor</p>')
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(g['title'])} | EA Hospitality Pulse</title>
<meta name="description" content="{html.escape(g['description'])}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="../feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="{html.escape(g['title'])}">
<meta property="og:description" content="{html.escape(g['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og/default.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(g['title'])}">
<meta name="twitter:description" content="{html.escape(g['description'])}">
<meta name="twitter:image" content="{BASE}/og/default.png">
<link rel="icon" href="../favicon.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld)}</script>
<script type="application/ld+json">{json.dumps(crumbs)}</script>
<style>{GUIDE_CSS}</style></head>
<body>
<header class="s"><div class="wrap"><div class="logo">🏨</div><a href="../index.html"><b>EA Hospitality Pulse</b></a></div></header>
<div class="wrap">
  <article class="art">
    <a class="nav" href="../index.html#guides">← All guides</a>
    <div><span class="cat">{html.escape(g['category'])}</span><span class="upd">Updated {upd} · {g['readMins']} min read</span></div>
    <h1>{html.escape(g['title'])}</h1>{byline_html}
    <p class="lede">{html.escape(g['description'])}</p>
    {g['bodyHtml']}
    <div class="sub">
      <b>Get this daily</b> — three briefs a day across Kenya, Uganda, Tanzania, Zanzibar &amp; Rwanda.<br>
      <a href="{CHANNELS.get('telegram','#')}" target="_blank" rel="noopener">📣 Telegram</a>
      <a href="{CHANNELS.get('whatsapp','#')}" target="_blank" rel="noopener">💬 WhatsApp</a>
      <a href="{CHANNELS.get('linkedin','#')}" target="_blank" rel="noopener">💼 LinkedIn</a>
      <a href="../index.html#guides">📚 All guides</a>
    </div>
  </article>
</div>
<footer class="s">EA Hospitality Pulse — Daily market intelligence for East Africa's hospitality and travel trade.<br>
<a href="../index.html">Home</a> · Kenya · Uganda · Tanzania · Zanzibar · Rwanda</footer>
</body></html>"""


# ---------------------------------------------------------------- main
def build():
    if not os.path.isdir(SRC):
        os.makedirs(SRC, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    guides = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".md"):
            continue
        g = parse_guide(os.path.join(SRC, fn))
        open(os.path.join(OUT, g["slug"] + ".html"), "w", encoding="utf-8").write(guide_page(g))
        guides.append(g)
    guides.sort(key=lambda x: x["updated"], reverse=True)
    index = [{k: g[k] for k in ("slug", "title", "description", "category", "updated", "readMins")}
             for g in guides]
    with open(os.path.join(HERE, "guides.js"), "w", encoding="utf-8") as f:
        f.write("window.GUIDES = " + json.dumps(index, ensure_ascii=False, indent=1) + ";\n")
    print(f"Guides built: {len(guides)}")
    return guides


if __name__ == "__main__":
    build()
