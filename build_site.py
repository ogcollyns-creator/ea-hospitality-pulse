#!/usr/bin/env python3
"""
EA Hospitality Pulse — site builder.
Outputs:
  data.js                         window.EDITIONS + window.INSIGHTS (for the SPA archive)
  editions/<id>.html              one static, SEO-optimised page per edition (indexable)
  sitemap.xml, robots.txt         so search engines discover every edition
Scans editions-src/*.md. Run: python build_site.py
"""
import os, re, json, html, datetime, subprocess
import sys, subprocess

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

# Editions are written with *bold* / _italic_ (the WhatsApp/Telegram convention).
# Render them properly on the web instead of printing literal asterisks.
_BOLD2 = re.compile(r"\*\*([^*\n]+?)\*\*")
_BOLD1 = re.compile(r"(?<!\w)\*([^*\n]+?)\*(?!\w)")
_ITAL  = re.compile(r"(?<![\w/])_([^_\n]+?)_(?![\w/])")

def md_inline(escaped):
    """Apply after html.escape() — converts emphasis markers to real tags."""
    t = _BOLD2.sub(r"<strong>\1</strong>", escaped)
    t = _BOLD1.sub(r"<strong>\1</strong>", t)
    t = _ITAL.sub(r"<em>\1</em>", t)
    return t

def md_strip(text):
    """Remove emphasis markers for plain-text contexts (summaries, share images)."""
    t = _BOLD2.sub(r"\1", text)
    t = _BOLD1.sub(r"\1", t)
    t = _ITAL.sub(r"\1", t)
    return t

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
            e=md_inline(html.escape(l))
            if KEYCAP.match(l): e=f'<span class="item-head">{e}</span>'
            elif l.startswith("🎯"): e=f'<span class="sowhat">{e}</span>'
            elif l.startswith("🏷"): e=f'<span class="tagline">{e}</span>'
            elif l[0] in "📡📅💬🏨": e=f'<span class="meta-line">{e}</span>'
            elif l.startswith("▪️"): e=f'<span class="radar-item">{e}</span>'
            r.append(e)
        out.append("<p>"+"<br>".join(r)+"</p>")
    return "\n".join(out)

# ---- headline hygiene -------------------------------------------------------
# Editions are authored for Telegram, so the lead line arrives carrying a keycap
# ("1\ufe0f\u20e3"), country flag emoji and SHOUTING CAPS. That is right for a chat
# app and wrong for a <title>, a meta description and a schema.org headline:
# answer engines index the noise and Google truncates it. Strip the chat furniture
# and de-shout, so every page carries a clean, topical, quotable headline.
_KEYCAP_ANY = re.compile(r"[0-9#*]\ufe0f?\u20e3")
_FLAGS      = re.compile(r"[\U0001F1E6-\U0001F1FF]{1,2}")
_PICTO      = re.compile(
    r"[\U0001F300-\U0001FAFF\u2190-\u21FF\u2300-\u23FF\u25A0-\u27BF"
    r"\u2B00-\u2BFF\uFE0F\u200D]")
_LOWER_WORDS = {"a","an","the","and","but","or","nor","for","so","yet","at","by",
                "in","of","on","to","up","as","via","from","into","over","with",
                "after","before","than","that","per","vs"}

# Ordinary words that a naive "short token = acronym" rule would leave SHOUTING.
_COMMON = set("""a an the and or but nor for so yet if as at by in of on to up off out
over under with from into onto than then that this these those there here it its is are
was were be been being am do does did done has have had having will would can could
shall should may might must not no now new old more most less least much many few all
any both each every other another same such own only just also very too own more
after before during while since until when where why how what which who whom whose
about across against along among around behind below beneath beside between beyond
down near past through throughout toward towards upon within without
day days week weeks month months year years today tomorrow yesterday night morning
january february march april may june july august september october november december
monday tuesday wednesday thursday friday saturday sunday
first second third last next high low higher lower big small long short early late
good bad best worst top bottom full half open close closed
say says said see sees seen make makes made take takes taken get gets got give gives
given go goes gone come comes came know knows knew think thinks thought want wants
look looks use uses used find finds found tell tells told ask asks work works
call calls try tries need needs feel feels leave leaves put puts mean means keep keeps
let lets begin begins seem seems help helps show shows hear hears play plays run runs
move moves like live lives believe hold holds bring brings happen happens write writes
sit sits stand stands lose loses lost pay pays meet meets set sets learn learns
change changes lead leads understand watch follow stop stops create speak read
allow add adds spend grow grows grew growth open walk win wins offer offers remember
love consider appear buy buys wait serve die send sends build builds stay stays fall
falls cut cuts reach reaches kill remain rise rises rose drop drops jump jumps
gap gaps rate rates cost costs price prices fee fees room rooms bed beds tax taxes
hotel hotels lodge lodges camp camps park parks trip trips tour tours visa visas
per plus via versus amid ahead back down up out
one two three four five six seven eight nine ten
was been has had did got may can will""".split())

_ACRONYM_HINT = {"USD","KES","UGX","TZS","RWF","EUR","GBP","VAT","GDP","ADR","OTA",
                 "ETA","EAC","KWS","UWA","RDB","TANAPA","ZATI","KAHC","MICE","IATA",
                 "ICAO","KCAA","TCAA","UCAA","RSSB","EPRA","WHO","CDC","ESG","API",
                 "PMS","CRS","RFP","YoY","MoM","NBO","MBA","JRO","ZNZ","EBB","KGL","IMF",
                 "UNWTO","IATA","AFRAA","KTB","UTB","TTB","RwandAir","KQ","AU",
                 "SGR","LPG","FX","CPI","GOP","F&B","RFPs","B2B","B2C","DMC","DMCs",
                 "US","UK","UAE","EU","UN","USA","NGO","VIP","CEO","COO","CFO"}

def _detitle(word):
    """Title-case one SHOUTED word, leaving genuine acronyms (KWS, USD, OTA) and
    anything numeric alone. Short *ordinary* words still get de-shouted."""
    core = re.sub(r"[^A-Za-z]", "", word)
    if not core: return word
    if any(ch.isdigit() for ch in word): return word        # Q3, 2026, KES1.2BN
    if core.upper() in _ACRONYM_HINT: return word           # known domain acronym
    if not set(core.upper()) & set("AEIOUY"): return word   # KWS, MTN — no vowels
    # Default is to de-shout. Leaving unknown short tokens capitalised produced
    # "YOU Got SH5 Off Diesel" — worse than the shouting it was meant to fix.
    return word[:1].upper() + word[1:].lower()

def clean_headline(text):
    """Chat-formatted lead line -> clean editorial headline."""
    t = _KEYCAP_ANY.sub(" ", text or "")
    t = _FLAGS.sub(" ", t)
    t = _PICTO.sub(" ", t)
    t = re.sub(r"^[\s\-\u2013\u2014\u2022:.|]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    letters = [c for c in t if c.isalpha()]
    # De-shout only when the line is genuinely shouting (>70% caps, 3+ words).
    if letters and len(t.split()) >= 3:
        if sum(1 for c in letters if c.isupper()) / len(letters) > 0.70:
            out, start = [], True
            for w in t.split(" "):
                d = _detitle(w)
                bare = d.lower().strip(".,;:!?'\u2019\u201c\u201d")
                if not start and d != w and bare in _LOWER_WORDS:
                    d = d.lower()
                if start and d[:1].isalpha():
                    d = d[:1].upper() + d[1:]
                    start = False
                # a new sentence (or a colon/dash break) re-capitalises
                if d.endswith((".", "!", "?", ":")):
                    start = True
                out.append(d)
            if out and out[-1].islower() and out[-1].isalpha():
                out[-1] = out[-1][:1].upper() + out[-1][1:]
            t = " ".join(out)
    return t.strip(" \u2013\u2014-|")

def load_guide_links():
    """Evergreen guides, read from front matter, so every edition page links into
    the reference hubs — a real internal link graph rather than a leaf page."""
    out = []
    gsrc = os.path.join(HERE, "guides-src")
    if not os.path.isdir(gsrc): return out
    for fn in sorted(os.listdir(gsrc)):
        if not fn.endswith(".md"): continue
        try: head = open(os.path.join(gsrc, fn), encoding="utf-8").read().split("---", 2)[1]
        except Exception: continue
        meta = {}
        for line in head.splitlines():
            if ":" in line:
                k, v = line.split(":", 1); meta[k.strip()] = v.strip()
        slug = meta.get("slug") or fn.rsplit(".", 1)[0]
        title = meta.get("title") or slug
        if title: out.append({"slug": slug, "title": title})
    return out

def intro_headline(md):
    """The deliberate one-line summary headline: the **bold** line that sits
    between the '### <date>' heading and the first '## SECTION' header. This is
    what the card title and H1 should show — the lead of the brief, not the
    masthead. Returns None if the edition has no such line (e.g. evening wraps)."""
    head = re.split(r"\n##\s", "\n" + md, 1)[0]
    for l in head.split("\n"):
        l = l.strip()
        if l.startswith("**") and l.endswith("**") and len(l) > 8:
            cand = md_strip(re.sub(r"\s+", " ", l))
            probe = re.sub(r"^[^0-9A-Za-z]+", "", cand)
            if _DATELINE.match(probe) or _DATELINE2.match(probe):
                continue  # a bold date line is masthead furniture, not the headline
            return cand[:220]
    return None

# A line that is essentially just a date (optionally with a short kicker after
# a "|") is masthead furniture, not the story. Skip it so the title/OG land on
# the real headline. Requires a 4-digit year so real headlines mentioning a day
# ("Kampala said 28 July") are not caught.
_DATELINE = re.compile(r"^(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}", re.I)
_DATELINE2 = re.compile(r"^\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+\d{4}", re.I)

def summarise(text):
    for l in text.split("\n"):
        l=l.strip()
        low=l.lower()
        # skip the masthead (any slot), the flag/date line, the italic subtitle,
        # dividers and headers — land on the first real story line.
        if not l: continue
        if l[0] in "🏨📅🗓📆🌅🕛🌆🌇🌄🌙🌃" or l.startswith(("━","#","_")): continue
        if "hospitality pulse" in low: continue
        probe = re.sub(r"^[^0-9A-Za-z]+", "", md_strip(l))   # drop leading emoji/flags
        if _DATELINE.match(probe) or _DATELINE2.match(probe): continue
        if len(l) > 40:
            return md_strip(re.sub(r"\s+"," ",l))[:200]
    return "East Africa hospitality intelligence."

# Editions must sort by when they were actually PUBLISHED. Filenames don't do this:
# reverse-alphabetically "morning" > "midday" > "foresight", so the morning brief
# would masquerade as the latest edition all day.
# Sort by (date, slot) FIRST and use git commit time only as a tiebreaker. The build
# runs BEFORE the commit, so a brand-new edition has no git time yet — keying on git
# time first would send today's edition to the bottom of the archive.
SLOT_RANK = {"morning": 1, "midday": 2, "foresight": 3, "evening": 4,
             "playbook": 5, "inaugural": 0}

def git_add_times():
    """Map edition filename -> unix time it was first committed."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=@%ct", "--name-only", "--", "editions-src/"],
            capture_output=True, text=True, check=True, cwd=HERE).stdout
    except Exception:
        return {}
    times, cur = {}, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("@"):
            try: cur = int(line[1:])
            except ValueError: cur = None
        elif line.endswith(".md") and cur:
            times.setdefault(os.path.basename(line), cur)
    return times

def load_existing():
    try:
        d=open(os.path.join(HERE,"data.js"),encoding="utf-8").read()
        m=re.search(r"window\.EDITIONS = (\[.*?\]);\s*\n", d, re.S)
        return {e["id"]:e for e in json.loads(m.group(1))} if m else {}
    except Exception:
        return {}

ARTICLE_CSS = """
:root{--sand:#f6f1e7;--ink:#1f2421;--muted:#6b6656;--gold:#c8892f;--gold-d:#a86f1f;--teal:#0f6d63;--teal-d:#0a4f48;--line:#e2d8c4;--sand-2:#efe7d6;--card:#fffdf9;--sans:"Helvetica Neue",Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
*{box-sizing:border-box}body{margin:0;font-family:Georgia,"Times New Roman",serif;color:var(--ink);background:var(--sand);line-height:1.68;font-size:18px;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:var(--gold);color:#231a06}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
a{color:var(--teal-d);text-decoration:none}
a:focus-visible{outline:2px solid var(--gold);outline-offset:2px;border-radius:2px}
.art p a{text-decoration:underline;text-decoration-color:rgba(15,109,99,.35);text-underline-offset:2px;text-decoration-thickness:1px}
.art p a:hover{text-decoration-color:var(--teal-d)}
header.s{background:var(--teal-d);color:#fff;padding:13px 0;border-bottom:3px solid var(--gold)}
header.s .wrap{display:flex;align-items:center;gap:10px}
header.s .wrap>a{display:flex;align-items:center;gap:10px;color:#fff}
header.s .logo{width:32px;height:32px;border-radius:4px;background:var(--gold);color:#231a06;display:grid;place-items:center;font:700 13px/1 var(--mono);letter-spacing:.5px}
header.s b{letter-spacing:-.01em}
header.s b{font-size:16px}
.art{background:var(--card);margin:24px auto;border:1px solid var(--line);border-radius:14px;padding:26px 30px 34px;overflow:hidden}
.art .hero{display:block;width:calc(100% + 60px);margin:-26px -30px 20px -30px;aspect-ratio:1200/630;object-fit:cover;background:var(--teal-d)}
.badge{font-family:Helvetica Neue,Arial,sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:4px 9px;border-radius:20px;background:var(--sand-2);color:var(--gold-d)}
.art time{font-family:Helvetica Neue,Arial,sans-serif;font-size:13px;color:var(--muted);margin-left:8px}
.art h1{font-size:clamp(25px,3.6vw,31px);line-height:1.22;margin:12px 0 18px;border-bottom:2px solid var(--gold);padding-bottom:14px;font-weight:700}
.kicker{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:2px}
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
.art h1{letter-spacing:-.005em}
.pnrow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:22px;border-top:1px solid var(--line);padding-top:16px}
.pn{font-family:Helvetica Neue,Arial,sans-serif;font-size:13.5px;font-weight:600;color:var(--teal-d);text-decoration:none;max-width:48%}
.pn:hover{text-decoration:underline}
.pn.next{margin-left:auto;text-align:right}
@media(max-width:640px){
  .wrap{padding:0 16px}
  .art{padding:20px 18px 26px;margin:16px auto;border-radius:12px}
  .art .hero{width:calc(100% + 36px);margin:-20px -18px 18px -18px}
  .art h1{font-size:22px}
  .pn{max-width:100%}
  .pn.next{margin-left:0;text-align:left}
  .crumbs{font-size:10.5px}
  .refs{padding:16px 18px}
}

/* --- editorial refinements ------------------------------------------------ */
.art h1{text-wrap:balance}
.art p{text-wrap:pretty;hyphens:auto}
/* Metadata reads as instrument panel, not body copy: mono, tracked, quiet. */
.crumbs{font:600 11px/1 var(--mono);letter-spacing:.06em;text-transform:uppercase;
  color:var(--muted);display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:0 0 14px}
.crumbs a{color:var(--muted);text-decoration:none;border-bottom:1px solid transparent;
  transition:border-color .18s ease,color .18s ease}
.crumbs a:hover{color:var(--teal-d);border-bottom-color:var(--gold)}
.crumbs span[aria-hidden]{opacity:.45}
.crumbs [aria-current]{color:var(--ink)}
.badge{font-family:var(--mono);letter-spacing:.08em;font-size:10.5px;border-radius:3px;
  background:transparent;border:1px solid var(--gold);color:var(--gold-d);padding:4px 8px}
.art time{font-family:var(--mono);font-size:11.5px;letter-spacing:.04em}
/* Reference rail — the internal link graph, given a shape of its own. */
.refs{margin:26px 0 0;padding:18px 22px;background:var(--sand-2);
  border-left:3px solid var(--teal-d);border-radius:0 8px 8px 0}
.refs h2{margin:0 0 9px;font:700 11px/1 var(--mono);letter-spacing:.1em;
  text-transform:uppercase;color:var(--teal-d)}
.refs ul{margin:0;padding:0;list-style:none}
.refs li{margin:0 0 6px;font-family:var(--sans);font-size:14px;line-height:1.45}
.refs li:last-child{margin-bottom:0}
.refs a{border-bottom:1px solid rgba(15,109,99,.28);transition:border-color .18s ease}
.refs a:hover{border-bottom-color:var(--teal-d)}
@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important}
}
/* Operators print these briefs and take them into rate meetings. */
@media print{
  body{background:#fff;font-size:11.5pt;line-height:1.45}
  header.s,footer.s,.crumbs,.pnrow,.sub,.more,.art .hero,.hcredit{display:none!important}
  .wrap{max-width:none;padding:0}
  .art{border:none;border-radius:0;margin:0;padding:0;background:#fff}
  .art h1{font-size:19pt;border-bottom:1.5pt solid #000;page-break-after:avoid}
  .item-head{page-break-after:avoid}
  .sowhat{background:#f2f2f2;border-left:2pt solid #666;page-break-inside:avoid}
  .refs{background:none;border-left:1pt solid #999;page-break-inside:avoid}
  a{color:#000;text-decoration:none}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:8.5pt;color:#555}
}
"""

def edition_page(e, siblings=None, prev=None, nxt=None, hero=None, credit=None):
    # One clean headline drives <title>, description, OG/Twitter, JSON-LD and H1.
    lead = clean_headline(e["summary"]) or e["edition"]
    short_date = e["dateDisplay"].split(", ", 1)[-1] if ", " in e["dateDisplay"] else e["dateDisplay"]
    _t = lead if len(lead) <= 62 else lead[:62].rsplit(" ", 1)[0] + "…"
    title = f"{_t} | {e['edition']}, {short_date} — EA Hospitality Pulse"
    desc = lead[:157] + ("…" if len(lead) > 157 else "")
    social_title = f"{_t} — {e['edition']}, {short_date}"
    url = f"{BASE}/editions/{e['id']}.html"
    img = f"{BASE}/og/{e['id']}.png"          # share card (OG/Twitter meta)
    hero_src = f"../og/{hero}" if hero else f"../og/{e['id']}.png"   # clean in-page photo
    # Clean, word-boundary headline (<=110 chars — Google's NewsArticle limit).
    headline = lead.split(".")[0].strip() or lead
    if len(headline) > 110:
        headline = headline[:110].rsplit(" ", 1)[0] + "…"
    h1text = headline if headline.endswith(("…", ".", "?", "!")) else headline + "."
    _plain = re.sub(r"<[^>]+>", " ", e["bodyHtml"])
    wordcount = len(_plain.split())
    news_kw = html.escape("East Africa hospitality, " + e["edition"] + ", Kenya, Uganda, Tanzania, Zanzibar, Rwanda, travel advisories, hotel demand, tourism")
    sib_html = ""
    if siblings:
        links = " · ".join(
            f'<a href="{s2["id"]}.html">{html.escape(s2["edition"])}</a>' for s2 in siblings)
        sib_html = f'<div class="more"><b>More from {html.escape(e["dateDisplay"])}:</b> {links}</div>'
    # Chronological prev/next — a real internal link graph for crawlers and readers.
    pn = []
    if prev: pn.append(f'<a class="pn prev" href="{prev["id"]}.html" rel="prev">← {html.escape(prev["edition"])} · {html.escape(prev["dateDisplay"])}</a>')
    if nxt: pn.append(f'<a class="pn next" href="{nxt["id"]}.html" rel="next">{html.escape(nxt["edition"])} · {html.escape(nxt["dateDisplay"])} →</a>')
    pn_html = f'<nav class="pnrow">{"".join(pn)}</nav>' if pn else ""
    ld = {
        "@context":"https://schema.org","@type":"NewsArticle",
        "headline": headline,
        "datePublished": e["date"], "dateModified": e["date"],
        "description": desc, "url": url, "mainEntityOfPage": url,
        "image": [img], "inLanguage": "en", "isAccessibleForFree": True,
        "articleSection": e["edition"],
        "author":{"@type":"Organization","name":"EA Hospitality Pulse","url":BASE+"/"},
        "publisher":{"@type":"Organization","name":"EA Hospitality Pulse","url":BASE+"/",
                     "logo":{"@type":"ImageObject","url":BASE+"/apple-touch-icon.png"}},
        "isPartOf":{"@type":"WebSite","name":"EA Hospitality Pulse","url":BASE+"/"},
        "keywords":"East Africa hospitality, "+e["edition"]+", Kenya, Uganda, Tanzania, Zanzibar, Rwanda, travel advisories, hotel demand, tourism",
        "wordCount": wordcount,
        "speakable":{"@type":"SpeakableSpecification","cssSelector":["h1",".sowhat"]},
        "about":["Kenya","Uganda","Tanzania","Zanzibar","Rwanda","hospitality","tourism"]
    }
    crumbs = {
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":BASE+"/"},
            {"@type":"ListItem","position":2,"name":"Editions","item":BASE+"/#archive"},
            {"@type":"ListItem","position":3,"name":e["edition"]+" — "+e["dateDisplay"],"item":url},
        ]}
    credit_html = ""
    if credit:
        _art = html.escape(credit.get("artist") or "Unknown")
        _lic = html.escape(credit.get("license") or "See source")
        _src = html.escape(credit.get("descurl") or "")
        _licurl = html.escape(credit.get("licenseurl") or "")
        _lictag = (f'<a href="{_licurl}" target="_blank" rel="noopener nofollow">{_lic}</a>' if _licurl else _lic)
        credit_html = (f'<p class="hcredit">Photo: {_art} \u00b7 '
                       f'<a href="{_src}" target="_blank" rel="noopener nofollow">Wikimedia Commons</a> \u00b7 {_lictag}</p>')
    _guides = load_guide_links()[:5]
    guides_html = ""
    if _guides:
        _gl = "".join(
            f'<li><a href="../guides/{g["slug"]}.html">{html.escape(g["title"])}</a></li>'
            for g in _guides)
        guides_html = (f'<aside class="refs" aria-label="Reference guides">'
                       f'<h2>Reference</h2><ul>{_gl}</ul></aside>')
    crumb_html = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a>'
                  f'<span aria-hidden="true">/</span><a href="../index.html#archive">Editions</a>'
                  f'<span aria-hidden="true">/</span>'
                  f'<span aria-current="page">{html.escape(e["edition"])}, {html.escape(e["dateDisplay"])}</span></nav>')
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="author" content="EA Hospitality Pulse">
<meta name="news_keywords" content="{news_kw}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="../feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="{html.escape(social_title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:image" content="{img}">
<link rel="icon" href="../favicon.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(social_title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta property="article:published_time" content="{e['date']}">
<meta property="article:modified_time" content="{e['date']}">
<meta property="article:section" content="{html.escape(e['edition'])}">
<meta property="og:locale" content="en_GB">
<meta name="twitter:site" content="@eapulse">
<script type="application/ld+json">{json.dumps(ld)}</script>
<script type="application/ld+json">{json.dumps(crumbs)}</script>
<style>{ARTICLE_CSS}
.hcredit{{margin:-8px 0 18px;font:12px/1.5 Helvetica Neue,Arial,sans-serif;color:#7c8a86}}
.hcredit a{{color:#5566a3;text-decoration:none}}</style></head>
<body>
<header class="s"><div class="wrap"><a href="/"><span class="logo" aria-hidden="true">EA</span><b>EA Hospitality Pulse</b></a></div></header>
<div class="wrap">
  <article class="art">
    <img class="hero" src="{hero_src}" alt="{html.escape(e['edition']+' — '+e['dateDisplay'])}" loading="eager">
    {credit_html}
    {crumb_html}
    <div class="kicker"><span class="badge">{html.escape(e['edition'])}</span><time datetime="{e['date']}">{html.escape(e['dateDisplay'])}</time></div>
    <h1>{html.escape(h1text)}</h1>
    {e['bodyHtml']}
    {sib_html}
    {guides_html}
    {pn_html}
    <div class="sub">
      <b>Follow the Pulse</b> — three briefs a day across Kenya, Uganda, Tanzania, Zanzibar &amp; Rwanda.<br>
      <a href="{CHANNELS['telegram']}" target="_blank" rel="noopener">📣 Telegram (full editions)</a>
      <a href="{CHANNELS['whatsapp']}" target="_blank" rel="noopener">💬 WhatsApp (daily skim)</a>
      <a href="{CHANNELS['linkedin']}" target="_blank" rel="noopener">💼 LinkedIn (the Big Read)</a>
      <a href="../index.html#archive">🗂 Every edition</a>
    </div>
  </article>
</div>
<footer class="s">EA Hospitality Pulse — Daily intelligence for city, bush &amp; beach properties across East Africa.<br>
<a href="../index.html">Home</a> · <a href="../credits.html">Image credits</a> · Kenya · Uganda · Tanzania · Zanzibar · Rwanda</footer>
</body></html>"""


# ---- image credits (attribution page for CC-BY / CC-BY-SA photography) -------
CREDIT_SEED = [
    {"slug":"gorilla-volcanoes","desc":"Mountain gorilla — Volcanoes NP, Rwanda",
     "title":"Mountain gorilla (Gorilla beringei beringei) yawn",
     "url":"https://commons.wikimedia.org/wiki/File:Mountain_gorilla_(Gorilla_beringei_beringei)_yawn.jpg","license":"CC BY-SA, see source"},
    {"slug":"amboseli-kilimanjaro","desc":"Elephants against Mount Kilimanjaro — Amboseli",
     "title":"Elephants at Amboseli national park against Mount Kilimanjaro",
     "url":"https://commons.wikimedia.org/wiki/File:Elephants_at_Amboseli_national_park_against_Mount_Kilimanjaro.jpg","license":"CC BY-SA 3.0"},
    {"slug":"mara-crossing","desc":"Wildebeest crossing the Mara River",
     "title":"Wildebeest Jumping Into the Mara River",
     "url":"https://commons.wikimedia.org/wiki/File:Wildebeest_Jumping_Into_the_Mara_River.jpg","license":"See source"},
    {"slug":"stonetown-zanzibar","desc":"Stone Town waterfront — Zanzibar",
     "title":"Stone Town-2",
     "url":"https://commons.wikimedia.org/wiki/File:Stone_Town-2.jpg","license":"See source"},
    {"slug":"kigali-convention","desc":"Kigali Convention Centre — Rwanda",
     "title":"An aerial of Kigali Convention Center (Emmanuel Kwizera)",
     "url":"https://commons.wikimedia.org/wiki/File:An_aerial_of_Kigali_Convention_Center_on_June_19,_2019._Photo_by_Emmanuel_Kwizera.jpg","license":"See source"},
    {"slug":"kigali-night","desc":"Kigali skyline at night — Rwanda",
     "title":"Panoramic view of Kigali (Rwanda) at night 01",
     "url":"https://commons.wikimedia.org/wiki/File:Panoramic_view_of_Kigali_(Rwanda)_at_night_01.jpg","license":"See source"},
    {"slug":"kenya-airways-aircraft","desc":"Kenya Airways aircraft — Nairobi",
     "title":"Kenya Airways Boeing 737-300 5Y-KQB NBO 2010-6-18",
     "url":"https://commons.wikimedia.org/wiki/File:Kenya_Airways_Boeing_737-300_5Y-KQB_NBO_2010-6-18.png","license":"See source"},
    {"slug":"kyobe-nile-lodge","desc":"River Nile lodge view — Murchison Falls, Uganda",
     "title":"View of the River Nile from Kyobe Safari Lodge, Murchison Falls NP, Uganda 03",
     "url":"https://commons.wikimedia.org/wiki/File:View_of_the_River_Nile_from_Kyobe_Safari_Lodge_%E2%80%93_Murchison_Falls_National_Park,_Uganda_03.jpg","license":"CC BY-SA 4.0"},
    {"slug":"uhuru-kilimanjaro","desc":"Uhuru Peak — Mount Kilimanjaro summit",
     "title":"Uhuru Peak Mt. Kilimanjaro 1",
     "url":"https://commons.wikimedia.org/wiki/File:Uhuru_Peak_Mt._Kilimanjaro_1.JPG","license":"GFDL / CC BY-SA 3.0"},
]

def build_credits_page():
    """Public attribution page. Seeded from the Wikimedia Commons sources and
    enriched with exact author/licence from img/credits.json once fetch_images.py
    has run — so the page is meaningful before fetch and precise after."""
    acc = {}
    try:
        acc = {c["slug"]: c for c in json.load(open(os.path.join(HERE,"img","credits.json"),encoding="utf-8"))}
    except Exception:
        pass
    rows = []
    for seed in CREDIT_SEED:
        a = acc.get(seed["slug"], {})
        src = a.get("descurl") or seed["url"]
        title = a.get("title") or seed["title"]
        artist = a.get("artist") or ""
        lic = a.get("license") or seed.get("license") or "See source"
        licurl = a.get("licenseurl") or ""
        lic_html = f'<a href="{html.escape(licurl)}" target="_blank" rel="noopener">{html.escape(lic)}</a>' if licurl else html.escape(lic)
        by = f' — {html.escape(artist)}' if artist else ''
        rows.append(f'<tr><td>{html.escape(seed["desc"])}</td>'
                    f'<td><a href="{html.escape(src)}" target="_blank" rel="noopener">{html.escape(title)}</a>{by}</td>'
                    f'<td>{lic_html}</td></tr>')
    try:
        _ec = json.load(open(os.path.join(HERE, "img", "edition-credits.json"), encoding="utf-8"))
    except Exception:
        _ec = {}
    for _eid, _a in sorted(_ec.items()):
        _src = _a.get("descurl") or ""
        _title = _a.get("title") or ""
        _artist = _a.get("artist") or ""
        _lic = _a.get("license") or "See source"
        _licurl = _a.get("licenseurl") or ""
        _lic_html = (f'<a href="{html.escape(_licurl)}" target="_blank" rel="noopener">{html.escape(_lic)}</a>'
                     if _licurl else html.escape(_lic))
        _by = f' — {html.escape(_artist)}' if _artist else ''
        rows.append(f'<tr><td>Edition {html.escape(_eid)}</td>'
                    f'<td><a href="{html.escape(_src)}" target="_blank" rel="noopener">{html.escape(_title)}</a>{_by}</td>'
                    f'<td>{_lic_html}</td></tr>')
    body = "\n".join(rows)
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Image credits | EA Hospitality Pulse</title>
<meta name="description" content="Attribution for photography used across EA Hospitality Pulse — sourced from Wikimedia Commons under Creative Commons / public-domain licences.">
<link rel="canonical" href="{BASE}/credits.html">
<meta name="robots" content="index,follow">
<style>{ARTICLE_CSS}
.art table{{width:100%;border-collapse:collapse;font-family:Helvetica Neue,Arial,sans-serif;font-size:14px}}
.art th,.art td{{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}}
.art th{{background:var(--sand-2)}}
.tw{{overflow-x:auto}}
</style></head>
<body>
<header class="s"><div class="wrap"><a href="/"><div class="logo">🏨</div><b>EA Hospitality Pulse</b></a></div></header>
<div class="wrap"><article class="art">
<a class="nav" href="./index.html">← Home</a>
<h1>Image credits</h1>
<p>Photography across this site is sourced from <a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">Wikimedia Commons</a> under Creative Commons or public-domain licences, and is cropped and tinted for layout. Each image remains under its original licence; the source and licence for every photo are listed below.</p>
<div class="tw"><table><thead><tr><th>Used for</th><th>Source (Wikimedia Commons)</th><th>Licence</th></tr></thead>
<tbody>
{body}
</tbody></table></div>
<p class="meta-line">Base illustrations (savannah, Nairobi skyline, Zanzibar beach) are licensed stock held in the repository. Questions about attribution: ceo@eahospitalitypulse.com.</p>
</article></div>
<footer class="s">EA Hospitality Pulse — Daily intelligence for city, bush &amp; beach properties across East Africa.<br>
<a href="./index.html">Home</a> · Kenya · Uganda · Tanzania · Zanzibar · Rwanda</footer>
</body></html>"""
    open(os.path.join(HERE,"credits.html"),"w",encoding="utf-8").write(page)

def main():
    existing = load_existing()
    pubtimes = git_add_times()
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
             "editionKey":key,"summary":(intro_headline(md) or summarise(tele)),"bodyHtml":render_body(tele)}
        e["_key"] = (date_iso, SLOT_RANK.get(key, 3), pubtimes.get(fn, 0))
        editions.append(e)
        for it in parse_items(tele):
            it.update({"source":eid,"date":date_iso,"dateDisplay":dd,
                       "edition":EDITION_LABELS.get(key,"Brief"),"editionKey":key})
            insights.append(it)
    built = {e["id"] for e in editions}
    for eid,e in existing.items():
        if eid not in built: editions.append(e)
    editions.sort(key=lambda e: e.get("_key", (e["date"], 3, 0)), reverse=True)
    for e in editions:
        e.pop("_key", None)
    insights.sort(key=lambda i:(i["date"],i["source"]), reverse=True)

    # data.js
    with open(os.path.join(HERE,"data.js"),"w",encoding="utf-8") as f:
        f.write("window.EDITIONS = "+json.dumps(editions,ensure_ascii=False,indent=1)+";\n")
        f.write("window.INSIGHTS = "+json.dumps(insights,ensure_ascii=False,indent=1)+";\n")
        f.write("window.BUILT_AT = "+json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))+";\n")

    # stamp index.html with the build time so the deployed shell is always identifiable
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    idx_path = os.path.join(HERE, "index.html")
    try:
        idx = open(idx_path, encoding="utf-8").read()
        idx = re.sub(r"<!--BUILD_STAMP:[^>]*-->", "", idx)
        idx = idx.replace("</head>", f"<!--BUILD_STAMP:{stamp}--></head>", 1)
        # keep the head's absolute URLs in sync with site_config.json "base"
        def _sub(pattern, value, text):
            return re.sub(pattern, lambda m: m.group(1) + value + m.group(2), text)
        idx = _sub(r'(<link rel="canonical" href=")[^"]*(")', BASE + "/", idx)
        idx = _sub(r'(<meta property="og:url" content=")[^"]*(")', BASE + "/", idx)
        idx = _sub(r'(<meta property="og:image" content=")[^"]*(")', BASE + "/og/default.png", idx)
        idx = _sub(r'(<meta name="twitter:image" content=")[^"]*(")', BASE + "/og/default.png", idx)
        idx = _sub(r'("@type":"Organization".*?"url":")[^"]*(")', BASE + "/", idx)
        idx = _sub(r'("@type":"Organization".*?"logo":")[^"]*(")', BASE + "/apple-touch-icon.png", idx)
        # Entity consistency: a stale sameAs (an old Telegram handle) teaches answer
        # engines the wrong identity. Drive it from site_config.json like everything else.
        _same = json.dumps([CHANNELS[k] for k in ("telegram", "linkedin", "whatsapp") if CHANNELS.get(k)])
        idx = re.sub(r'("sameAs":)\[[^\]]*\]', lambda m: m.group(1) + _same, idx, count=1)
        open(idx_path, "w", encoding="utf-8").write(idx)
    except Exception as e:
        print("build stamp skipped:", e)

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
    try:
        hero_map = json.load(open(os.path.join(HERE, "og", "hero_map.json"), encoding="utf-8"))
    except Exception:
        hero_map = {}
    try:
        edcred = json.load(open(os.path.join(HERE, "img", "edition-credits.json"), encoding="utf-8"))
    except Exception:
        edcred = {}
    order = editions  # already sorted newest-first
    pos = {ed["id"]: i for i, ed in enumerate(order)}
    for e in editions:
        sibs = [x for x in by_date.get(e["date"], []) if x["id"] != e["id"]]
        i = pos[e["id"]]
        nxt = order[i-1] if i > 0 else None                 # newer edition
        prv = order[i+1] if i+1 < len(order) else None      # older edition
        with open(os.path.join(EDIR, e["id"]+".html"),"w",encoding="utf-8") as f:
            f.write(edition_page(e, sibs, prev=prv, nxt=nxt, hero=hero_map.get(e["id"]), credit=edcred.get(e["id"])))

    # evergreen guides
    try:
        import build_guides
        guides = build_guides.build()
    except Exception as ex:
        print("guides skipped:", ex)
        guides = []
    build_credits_page()

    # feed.xml — RSS 2.0, so associations / aggregators / newsletter tools can
    # auto-pull editions instead of needing a manual republish each time.
    today = datetime.date.today().isoformat()
    import xml.sax.saxutils as sx
    def rfc822(date_iso):
        try:
            d = datetime.date.fromisoformat(date_iso)
            return datetime.datetime(d.year, d.month, d.day, 7, 0, 0).strftime("%a, %d %b %Y %H:%M:%S +0300")
        except Exception:
            return datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0300")
    feed_items = editions[:30]
    rss = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
           '<channel>',
           f'<title>EA Hospitality Pulse</title>',
           f'<link>{BASE}/</link>',
           f'<atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>',
           '<description>Daily market intelligence for East Africa\'s hospitality and travel trade — Kenya, Uganda, Tanzania, Zanzibar, Rwanda. Free to republish with attribution; see /republish.html.</description>',
           '<language>en-us</language>',
           f'<lastBuildDate>{rfc822(today)}</lastBuildDate>']
    for e in feed_items:
        url = f"{BASE}/editions/{e['id']}.html"
        title = sx.escape(f"{e['edition']} — {e['dateDisplay']}")
        desc = sx.escape(e['summary'][:400])
        rss.append('<item>')
        rss.append(f'<title>{title}</title>')
        rss.append(f'<link>{url}</link>')
        rss.append(f'<guid isPermaLink="true">{url}</guid>')
        rss.append(f'<pubDate>{rfc822(e["date"])}</pubDate>')
        rss.append(f'<description>{desc}</description>')
        rss.append('</item>')
    rss.append('</channel></rss>')
    open(os.path.join(HERE, "feed.xml"), "w", encoding="utf-8").write("\n".join(rss))

    # sitemap.xml
    urls = [(BASE+"/", today, "daily"), (BASE+"/republish.html", today, "monthly"), (BASE+"/methodology.html", today, "monthly"), (BASE+"/faq.html", today, "monthly"), (BASE+"/start-here.html", today, "monthly"), (BASE+"/survey.html", today, "monthly"), (BASE+"/survey-pay.html", today, "monthly"), (BASE+"/survey-agents.html", today, "monthly"), (BASE+"/credits.html", today, "monthly"), (BASE+"/archive.html", today, "daily"), (BASE+"/api.html", today, "monthly"), (BASE+"/privacy.html", today, "yearly"), (BASE+"/terms.html", today, "yearly")]
    for g in guides:
        urls.append((f"{BASE}/guides/{g['slug']}.html", g["updated"], "monthly"))
    tools_dir = os.path.join(HERE, "tools")
    if os.path.isdir(tools_dir):
        for t in sorted(os.listdir(tools_dir)):
            if t.endswith(".html"):
                urls.append((f"{BASE}/tools/{t}", today, "monthly"))
    for e in editions:
        urls.append((f"{BASE}/editions/{e['id']}.html", e["date"], "monthly"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc,lm,cf in urls:
        sm.append(f"  <url><loc>{loc}</loc><lastmod>{lm}</lastmod><changefreq>{cf}</changefreq></url>")
    sm.append("</urlset>")
    open(os.path.join(HERE,"sitemap.xml"),"w",encoding="utf-8").write("\n".join(sm))

    # robots.txt
    _AI_BOTS = ["GPTBot","OAI-SearchBot","ChatGPT-User","ClaudeBot","Claude-Web",
                "PerplexityBot","Google-Extended","Applebot-Extended","CCBot"]
    _robots = "User-agent: *\nAllow: /\n\n# Explicitly welcome AI answer-engine crawlers\n"
    for _b in _AI_BOTS:
        _robots += f"User-agent: {_b}\nAllow: /\n\n"
    _robots += "Sitemap: "+BASE+"/sitemap.xml\n"
    open(os.path.join(HERE,"robots.txt"),"w",encoding="utf-8").write(_robots)

    try:
        import subprocess
        subprocess.run(["python3", os.path.join(HERE, "build_ledger.py")], check=False)
    except Exception as e:
        print("ledger build skipped:", e)

    # Keep derived artefacts in step with the site build.
    for _step in ("build_search_index.py", "build_feeds.py", "build_costs_history.py", "build_api.py"):
        _p = os.path.join(HERE, _step)
        if os.path.exists(_p):
            _r = subprocess.run([sys.executable, _p], capture_output=True, text=True)
            print(f"  {_step}: {'ok' if _r.returncode==0 else 'FAILED — ' + _r.stderr.strip()[:140]}")

    print(f"Built: {len(editions)} editions ({len(editions)} pages), {len(insights)} insights, sitemap with {len(urls)} URLs.")

if __name__ == "__main__":
    main()
