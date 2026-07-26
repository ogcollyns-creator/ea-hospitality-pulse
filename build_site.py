#!/usr/bin/env python3
"""
EA Hospitality Pulse — site builder.
Outputs:
  data.js                         window.EDITIONS + window.INSIGHTS (for the SPA archive)
  editions/<id>.html              one static, SEO-optimised page per edition (indexable)
  sitemap.xml, robots.txt         so search engines discover every edition
Scans editions-src/*.md. Run: python build_site.py
"""
import os, re, json, html, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "editions-src")
EDIR = os.path.join(HERE, "editions")
# Single source of truth for the domain — edit site_config.json, not this file.
_cfg_path = os.path.join(HERE, "site_config.json")
try:
    _CFG = json.load(open(_cfg_path, encoding="utf-8"))
except Exception:
    _CFG = {}
BASE = (_CFG.get("base") or "https://ogcollyns-creator.github.io/ea-hospitality-pulse").rstrip("/")
CNAME = (_CFG.get("cname") or "").strip()
CHANNELS = _CFG.get("channels") or {
    "telegram": "https://t.me/africabusinessriskreview",
    "linkedin": "https://www.linkedin.com/company/ea-hospitality-pulse/",
    "whatsapp": "https://whatsapp.com/channel/0029VbCjul2KmCPTv8Qrh73b",
}

EDITION_LABELS = {
    "morning": "Morning Brief", "midday": "Midday Pulse",
    "evening": "Evening Wrap", "inaugural": "Inaugural Edition",
    "foresight": "Sunday Foresight", "playbook": "Shock Playbook",
}
KEYCAP = re.compile(r"^([0-9]️?⃣)\s*")

def parse_filename(fn):
    base = fn.rsplit(".", 1)[0]
    m = re.search(r"(\d{4}-\d{2}-\d{2})", base)
    date_iso = m.group(1) if m else None
    key = "morning"; low = base.lower()
    for k in EDITION_LABELS:
        if k in low: key = k; break
    if low.startswith("foresight"): key = "foresight"
    return date_iso, key

def extract_telegram(md):
    parts = re.split(r"\n##+\s*", "\n" + md)
    for p in parts:
        if p.strip().split("\n",1)[0].strip().upper().startswith("TELEGRAM"):
            return (p.split("\n",1)[1] if "\n" in p else "").strip()
    return md.strip()

def segments_from_tag(t):
    t = t.lower()
    if "all segment" in t: return ["city","bush","beach"]
    s=[]
    if "city" in t: s.append("city")
    if "bush" in t: s.append("bush")
    if "beach" in t or "coast" in t: s.append("beach")
    return s

def parse_items(tele):
    items, cur = [], None
    for raw in tele.split("\n"):
        l = raw.strip()
        if not l: continue
        if KEYCAP.match(l):
            if cur: items.append(cur)
            cur = {"headline": KEYCAP.sub("", l), "body": [], "sowhat":"", "tags":""}
        elif cur is not None:
            if l.startswith("🎯"): cur["sowhat"]=l
            elif l.startswith("🏷"): cur["tags"]=l.replace("🏷","").strip(); items.append(cur); cur=None
            elif l[0] in "━📡💬📅🏨": items.append(cur); cur=None
            else: cur["body"].append(l)
    if cur: items.append(cur)
    out=[]
    for it in items:
        if not it.get("tags"): continue
        f=[x.strip() for x in it["tags"].split("|")]
        segs=segments_from_tag(f[0] if f else "")
        if not segs: continue
        out.append({"headline":it["headline"],"body":" ".join(it["body"]).strip(),
                    "sowhat":it["sowhat"].strip(),"segments":segs,
                    "countries":f[1] if len(f)>1 else "","confidence":f[2] if len(f)>2 else ""})
    return out

def render_body(text):
    out=[]
    for blk in re.split(r"\n\s*\n", text):
        blk=blk.strip()
        if not blk: continue
        if set(blk) <= set("━—-–_ "): out.append('<hr class="divider">'); continue
        r=[]
        for l in [x.strip() for x in blk.split("\n") if x.strip()]:
            e=html.escape(l)
            if KEYCAP.match(l): e=f'<span class="item-head">{e}</span>'
            elif l.startswith("🎯"): e=f'<span class="sowhat">{e}</span>'
            elif l.startswith("🏷"): e=f'<span class="tagline">{e}</span>'
            elif l[0] in "📡📅💬🏨": e=f'<span class="meta-line">{e}</span>'
            elif l.startswith("▪️"): e=f'<span class="radar-item">{e}</span>'
            r.append(e)
        out.append("<p>"+"<br>".join(r)+"</p>")
    return "\n".join(out)

def summarise(text):
    for l in text.split("\n"):
        l=l.strip()
        if l and not l.startswith(("🏨","📅","━","#")) and len(l)>40:
            return re.sub(r"\s+"," ",l)[:200]
    return "East Africa hospitality intelligence."

def load_existing():
    try:
        d=open(os.path.join(HERE,"data.js"),encoding="utf-8").read()
        m=re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
        return {e["id"]:e for e in json.loads(m.group(1))} if m else {}
    except Exception:
        return {}

ARTICLE_CSS = """
:root{--sand:#f6f1e7;--ink:#1f2421;--muted:#6b6656;--gold:#c8892f;--gold-d:#a86f1f;--teal:#0f6d63;--teal-d:#0a4f48;--line:#e2d8c4;--sand-2:#efe7d6;--card:#fffdf9}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,Cambria,serif;color:var(--ink);background:var(--sand);line-height:1.6}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
a{color:var(--teal-d)}
header.s{background:linear-gradient(135deg,var(--teal-d),var(--teal));color:#fff;padding:14px 0;border-bottom:4px solid var(--gold)}
header.s .wrap{display:flex;align-items:center;gap:10px}
header.s .logo{width:34px;height:34px;border-radius:8px;background:var(--gold);display:grid;place-items:center;font-size:18px}
header.s b{font-size:16px}
.art{background:var(--card);margin:24px auto;border:1px solid var(--line);border-radius:14px;padding:26px 30px 34px}
.badge{font-family:Helvetica Neue,Arial,sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:4px 9px;border-radius:20px;background:var(--sand-2);color:var(--gold-d)}
.art time{font-family:Helvetica Neue,Arial,sans-serif;font-size:13px;color:var(--muted);margin-left:8px}
.art h1{font-size:23px;line-height:1.25;margin:14px 0 16px;border-bottom:2px solid var(--gold);padding-bottom:12px}
.art p{margin:0 0 14px}
.item-head{font-weight:700;font-size:17px;display:inline-block;margin-top:4px}
.sowhat{display:block;background:var(--sand-2);border-left:4px solid var(--gold);padding:8px 12px;border-radius:0 6px 6px 0;font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;margin-top:4px}
.tagline{display:inline-block;font-family:Helvetica Neue,Arial,sans-serif;font-size:12px;color:var(--muted)}
.radar-item{display:block;font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;margin:2px 0}
.meta-line{display:block;font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;color:var(--muted)}
hr.divider{border:none;border-top:1px dashed var(--line);margin:16px 0}
.nav{font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;font-weight:600;margin:0 0 6px;display:inline-block}
.sub{font-family:Helvetica Neue,Arial,sans-serif;font-size:14px;color:var(--muted);margin-top:20px;border-top:1px solid var(--line);padding-top:16px;line-height:1.9}
.more{font-family:Helvetica Neue,Arial,sans-serif;font-size:13.5px;background:var(--sand-2);border-radius:8px;padding:11px 14px;margin-top:22px}
.more a{margin-right:10px}
.sub a{font-weight:600;margin-right:14px}
footer.s{text-align:center;color:var(--muted);font-family:Helvetica Neue,Arial,sans-serif;font-size:12px;padding:20px}
"""

def edition_page(e, siblings=None):
    title = f"{e['edition']} — {e['dateDisplay']} | EA Hospitality Pulse"
    desc = e["summary"][:157] + ("…" if len(e["summary"])>157 else "")
    url = f"{BASE}/editions/{e['id']}.html"
    sib_html = ""
    if siblings:
        links = " · ".join(
            f'<a href="{s2["id"]}.html">{html.escape(s2["edition"])}</a>' for s2 in siblings)
        sib_html = f'<div class="more"><b>More from {html.escape(e["dateDisplay"])}:</b> {links}</div>'
    ld = {
        "@context":"https://schema.org","@type":"NewsArticle",
        "headline": e["summary"][:110],
        "datePublished": e["date"], "dateModified": e["date"],
        "description": desc, "url": url, "mainEntityOfPage": url,
        "articleSection": e["edition"],
        "author":{"@type":"Organization","name":"EA Hospitality Pulse"},
        "publisher":{"@type":"Organization","name":"EA Hospitality Pulse"},
        "about":["Kenya","Uganda","Tanzania","Zanzibar","Rwanda","hospitality","tourism"]
    }
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="{html.escape(e['edition']+' — '+e['dateDisplay'])}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og/{e['id']}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:image" content="{BASE}/og/{e['id']}.png">
<link rel="icon" href="../favicon.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(e['edition']+' — '+e['dateDisplay'])}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta property="article:published_time" content="{e['date']}">
<script type="application/ld+json">{json.dumps(ld)}</script>
<style>{ARTICLE_CSS}</style></head>
<body>
<header class="s"><div class="wrap"><div class="logo">🏨</div><b>EA Hospitality Pulse</b></div></header>
<div class="wrap">
  <article class="art">
    <a class="nav" href="../index.html#archive">← All editions</a>
    <div><span class="badge">{html.escape(e['edition'])}</span><time>{html.escape(e['dateDisplay'])}</time></div>
    <h1>{html.escape(e['summary'].split('.')[0])[:120]}.</h1>
    {e['bodyHtml']}
    {sib_html}
    <div class="sub">
      <b>Follow the Pulse</b> — three briefs a day across Kenya, Uganda, Tanzania, Zanzibar &amp; Rwanda.<br>
      <a href="{CHANNELS['telegram']}" target="_blank" rel="noopener">📣 Telegram (full editions)</a>
      <a href="{CHANNELS['whatsapp']}" target="_blank" rel="noopener">💬 WhatsApp (daily skim)</a>
      <a href="{CHANNELS['linkedin']}" target="_blank" rel="noopener">💼 LinkedIn (the Big Read)</a>
      <a href="../index.html#archive">🗂 Full archive</a>
    </div>
  </article>
</div>
<footer class="s">EA Hospitality Pulse — Daily intelligence for city, bush &amp; beach properties across East Africa.<br>
<a href="../index.html">Home</a> · Kenya · Uganda · Tanzania · Zanzibar · Rwanda</footer>
</body></html>"""

def main():
    existing = load_existing()
    editions, insights = [], []
    for fn in sorted(os.listdir(SRC)):
        if not fn.lower().endswith(".md"): continue
        date_iso, key = parse_filename(fn)
        if not date_iso: continue
        md = open(os.path.join(SRC, fn), encoding="utf-8").read()
        tele = extract_telegram(md)
        try: dd = datetime.date.fromisoformat(date_iso).strftime("%A, %-d %B %Y")
        except Exception: dd = date_iso
        eid = fn.rsplit(".",1)[0]
        e = {"id":eid,"date":date_iso,"dateDisplay":dd,"edition":EDITION_LABELS.get(key,"Brief"),
             "editionKey":key,"summary":summarise(tele),"bodyHtml":render_body(tele)}
        editions.append(e)
        for it in parse_items(tele):
            it.update({"source":eid,"date":date_iso,"dateDisplay":dd,
                       "edition":EDITION_LABELS.get(key,"Brief"),"editionKey":key})
            insights.append(it)
    built = {e["id"] for e in editions}
    for eid,e in existing.items():
        if eid not in built: editions.append(e)
    editions.sort(key=lambda e:(e["date"],e["id"]), reverse=True)
    insights.sort(key=lambda i:(i["date"],i["source"]), reverse=True)

    # data.js
    with open(os.path.join(HERE,"data.js"),"w",encoding="utf-8") as f:
        f.write("window.EDITIONS = "+json.dumps(editions,ensure_ascii=False,indent=1)+";\n")
        f.write("window.INSIGHTS = "+json.dumps(insights,ensure_ascii=False,indent=1)+";\n")
        f.write("window.BUILT_AT = "+json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))+";\n")

    # branded social share images (uses the data.js just written)
    try:
        import subprocess
        subprocess.run(["python3", os.path.join(HERE, "make_og_images.py")], check=False)
    except Exception as e:
        print("og image generation skipped:", e)

    # CNAME for a custom domain
    if CNAME:
        open(os.path.join(HERE, "CNAME"), "w", encoding="utf-8").write(CNAME + "\n")

    # per-edition static pages
    os.makedirs(EDIR, exist_ok=True)
    by_date = {}
    for e in editions:
        by_date.setdefault(e["date"], []).append(e)
    for e in editions:
        sibs = [x for x in by_date.get(e["date"], []) if x["id"] != e["id"]]
        with open(os.path.join(EDIR, e["id"]+".html"),"w",encoding="utf-8") as f:
            f.write(edition_page(e, sibs))

    # sitemap.xml
    today = datetime.date.today().isoformat()
    urls = [(BASE+"/", today, "daily")]
    for e in editions:
        urls.append((f"{BASE}/editions/{e['id']}.html", e["date"], "monthly"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc,lm,cf in urls:
        sm.append(f"  <url><loc>{loc}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq></url>")
    sm.append("</urlset>")
    open(os.path.join(HERE,"sitemap.xml"),"w",encoding="utf-8").write("\n".join(sm))

    # robots.txt
    open(os.path.join(HERE,"robots.txt"),"w",encoding="utf-8").write(
        "User-agent: *\nAllow: /\nSitemap: "+BASE+"/sitemap.xml\n")

    try:
        import subprocess
        subprocess.run(["python3", os.path.join(HERE, "build_ledger.py")], check=False)
    except Exception as e:
        print("ledger build skipped:", e)

    print(f"Built: {len(editions)} editions ({len(editions)} pages), {len(insights)} insights, sitemap with {len(urls)} URLs.")

if __name__ == "__main__":
    main()
