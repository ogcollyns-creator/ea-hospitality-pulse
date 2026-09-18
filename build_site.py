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
from urllib.parse import quote

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

# Editions are authored for chat, where a bare URL is a live link. Pasted onto
# the web it becomes dead text — and a lost edge in the internal link graph that
# crawlers and answer engines walk. Turn bare URLs into real anchors.
_URL_RE = re.compile(r"https?://[^\s<]+")

def linkify(escaped):
    """Apply after md_inline() — the only tags present are <strong>/<em>, so a
    match can never land inside an existing href."""
    def _a(m):
        raw = m.group(0)
        url = raw.rstrip(".,;:)\u00b7")
        tail = raw[len(url):]
        label = re.sub(r"^https?://(www\.)?", "", url)
        if len(label) > 58:
            label = label[:55] + "\u2026"
        return f'<a href="{url}" rel="noopener">{label}</a>{tail}'
    return _URL_RE.sub(_a, escaped)


_SHARE_TEMPLATE = """<div class="share-wrap">
  <button type="button" class="share-btn" id="shareBtn" aria-haspopup="true" aria-expanded="false">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7a3.02 3.02 0 0 0 0-1.4l7.05-4.11a2.99 2.99 0 1 0-.99-2.19c0 .24.03.47.09.7L8 9.81a3 3 0 1 0 0 4.38l7.12 4.15c-.06.23-.09.46-.09.7a3 3 0 1 0 3-3.96z"/></svg>
    Share
  </button>
  <span class="share-toast" id="shareToast" hidden>Link copied</span>
  <div class="share-menu" id="shareMenu" hidden>
    <button type="button" id="shareCopy">🔗 Copy link</button>
    <a href="__WA__" target="_blank" rel="noopener">💬 WhatsApp</a>
    <a href="__TG__" target="_blank" rel="noopener">📣 Telegram</a>
    <a href="__TW__" target="_blank" rel="noopener">𝕏 X (Twitter)</a>
    <a href="__LI__" target="_blank" rel="noopener">💼 LinkedIn</a>
  </div>
</div>
<script>
(function(){
  var url="__URL__", title="__TITLE__";
  var btn=document.getElementById('shareBtn'), menu=document.getElementById('shareMenu'),
      toast=document.getElementById('shareToast'), copyBtn=document.getElementById('shareCopy');
  function closeMenu(){ menu.hidden=true; btn.setAttribute('aria-expanded','false'); }
  btn.addEventListener('click', function(e){
    e.stopPropagation();
    if(navigator.share){ navigator.share({title:title,url:url}).catch(function(){}); return; }
    var open=menu.hidden;
    closeMenu();
    if(open){ menu.hidden=false; btn.setAttribute('aria-expanded','true'); }
  });
  copyBtn.addEventListener('click', function(){
    var done=function(){ toast.hidden=false; setTimeout(function(){toast.hidden=true;},1800); closeMenu(); };
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(url).then(done, done); }
    else { var ta=document.createElement('textarea'); ta.value=url; ta.style.position='fixed'; ta.style.opacity='0';
      document.body.appendChild(ta); ta.focus(); ta.select();
      try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta); done(); }
  });
  document.addEventListener('click', function(e){ if(!menu.hidden && !menu.contains(e.target) && e.target!==btn) closeMenu(); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeMenu(); });
})();
</script>"""

def share_widget_html(url, title):
    """Dependency-free share control: native Web Share API on mobile/supported
    browsers, a small menu of direct network links (WhatsApp/Telegram/X/
    LinkedIn) plus copy-link everywhere else. Shared by edition and guide
    pages so every article and daily brief carries the same control."""
    enc_url = quote(url, safe="")
    enc_title = quote(title, safe="")
    wa = f"https://wa.me/?text={enc_title}%20{enc_url}"
    tg = f"https://t.me/share/url?url={enc_url}&text={enc_title}"
    tw = f"https://twitter.com/intent/tweet?url={enc_url}&text={enc_title}"
    li = f"https://www.linkedin.com/sharing/share-offsite/?url={enc_url}"
    # json.dumps, not html.escape: this text lands inside an inline <script>,
    # where HTML entities are never decoded by the JS parser (raw-text element).
    js_url = json.dumps(url).replace("</", "<\/")
    js_title = json.dumps(title).replace("</", "<\/")
    out = _SHARE_TEMPLATE
    out = out.replace("__WA__", wa).replace("__TG__", tg).replace("__TW__", tw).replace("__LI__", li)
    out = out.replace('"__URL__"', js_url).replace('"__TITLE__"', js_title)
    return out


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


def classify_impact(headline, sowhat, body, conf):
    """Directional operator-impact read, derived from the signal's own words.
    Returns (label, css_class, intensity 1-3). This is an editorial interpretation
    shown as a chip, not a sourced statistic."""
    t  = " ".join([headline or "", sowhat or "", body or ""]).lower()
    sw = (sowhat or "").lower()
    c  = (conf or "").lower()
    # intensity keyed to how firm the item is
    if "confirm" in c:            intensity = 3
    elif "reported" in c:         intensity = 2
    elif "early" in c or "inference" in c or "signal" in c: intensity = 1
    else:                         intensity = 2
    def has(p): return re.search(p, t) is not None
    # an item about capacity/volume that risks discounting is a "watch", not clean demand
    watch_override = re.search(r"discount|not rate|volume[^.]*not|oversupply|competitors will lag|fill the (extra )?lift|price war", sw) is not None
    easing = has(r"advisor|level\s*[0-9]|do not travel") and has(r"eas(e|es|ed|ing)|lift(s|ed)?|downgrad|to level 2|from level 3|removes|reopen|resum")
    if easing and not watch_override:
        return ("+demand", "demand", intensity)
    if has(r"advisor|do not travel|level\s*4|level\s*3|outbreak|ebola|marburg|cholera|dengue|crash|killed|fatal|security|attack|terror|abduct|kidnap|protest|unrest|riot|coup|flood|cyclone|drought|storm|\bban\b|grounded|suspend|closure|closed|warning"):
        return ("risk", "risk", intensity)
    if has(r"lev(y|ies)|\bfees?\b|\btax\b|\bvat\b|surcharge|tariff|\bhike|fuel|diesel|petrol|price[s]?\s*(rise|rose|up|increase)|rise[s]?\s*\d|increase|raises|costlier|permit.*(rise|up|increase)|weaker shilling|depreciat|more expensive"):
        return ("-margin", "margin", intensity)
    if watch_override:
        return ("watch", "watch", intensity)
    if has(r"route|arrivals|\bdemand\b|record|growth|grew|congress|summit|\bmice\b|expo|marathon|compression|booking|opens|opening|launch|expansion|recover|capacity|frequenc|seats|\+\s*\d|up\s+\d|surge|boom|record-|rebound"):
        return ("+demand", "demand", intensity)
    return ("watch", "watch", intensity)


IMPACT_TOKENS = {
    "demand":("+demand","demand"), "+demand":("+demand","demand"),
    "opportunity":("+demand","demand"), "opp":("+demand","demand"), "up":("+demand","demand"),
    "margin":("-margin","margin"), "-margin":("-margin","margin"), "cost":("-margin","margin"), "-cost":("-margin","margin"),
    "risk":("risk","risk"), "-risk":("risk","risk"),
    "watch":("watch","watch"), "neutral":("watch","watch"),
}

def resolve_impact(tagstr, headline, sowhat, body, conf):
    """Author-set 'impact:<token>' on the tag line wins; otherwise auto-classify.
    Returns (label, css_class, intensity 1-3, source) where source is 'author' or 'auto'."""
    m = re.search(r"impact:\s*([+\-]?[a-zA-Z]+)", tagstr or "", re.I)
    if m:
        raw = m.group(1).lower()
        pick = IMPACT_TOKENS.get(raw) or IMPACT_TOKENS.get(raw.lstrip("+-"))
        if pick:
            c = (conf or "").lower()
            inten = 3 if "confirm" in c else (2 if "reported" in c else (1 if ("early" in c or "inference" in c or "signal" in c) else 2))
            return pick[0], pick[1], inten, "author"
    lab, cls, inten = classify_impact(headline, sowhat, body, conf)
    return lab, cls, inten, "auto"

def parse_items(tele):
    items, cur = [], None
    for raw in tele.split("\n"):
        l = raw.strip()
        if not l: continue
        lm = l.strip("*").strip()   # de-bold so **1⃣ ...** headlines still parse
        if KEYCAP.match(lm):
            if cur: items.append(cur)
            cur = {"headline": KEYCAP.sub("", lm).strip(), "body": [], "sowhat":"", "tags":""}
        elif cur is not None:
            if l.startswith("🎯"): cur["sowhat"]=l
            elif l.startswith("🏷"): cur["tags"]=l.replace("🏷","").strip(); items.append(cur); cur=None
            elif l[0] in "━📡💬📅🏨": items.append(cur); cur=None
            else: cur["body"].append(l)
    if cur: items.append(cur)
    out=[]
    for it in items:
        if not it.get("tags"): continue
        tagstr = it["tags"]
        # drop the optional 'impact:<token>' field before reading segment/country/confidence
        clean = re.sub(r"[·|]?\s*impact:\s*[+\-]?[a-zA-Z]+", "", tagstr, flags=re.I).strip(" ·|")
        # "·" joins multiple segments *within* the first field (e.g.
        # "City·Bush·Beach"); "|" is the only field separator. Splitting on
        # both broke multi-segment tags apart, shifting country into segments
        # and confidence into country for every "A·B·C | ..." tag.
        f=[x.strip() for x in re.split(r"\|", clean)]  # only | separates fields
        segs=segments_from_tag(f[0] if f else "")
        if not segs: continue
        conf = f[2] if len(f)>2 else ""
        _imp,_impc,_inten,_src = resolve_impact(tagstr, it["headline"], it["sowhat"], " ".join(it["body"]), conf)
        out.append({"headline":it["headline"],"body":" ".join(it["body"]).strip(),
                    "sowhat":it["sowhat"].strip(),"segments":segs,
                    "countries":f[1] if len(f)>1 else "","confidence":conf,
                    "impact":_imp,"impactClass":_impc,"intensity":_inten,"impactSet":_src})
    return out

def render_body(text):
    out=[]
    for blk in re.split(r"\n\s*\n", text):
        blk=blk.strip()
        if not blk: continue
        if set(blk) <= set("━—-–_ "): out.append('<hr class="divider">'); continue
        r=[]
        for l in [x.strip() for x in blk.split("\n") if x.strip()]:
            e=linkify(md_inline(html.escape(l)))
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
            if _SLOT_FRAMING.match(cand) or _CORRECTION_LINE.match(cand):
                continue  # framing / correction furniture, not the headline
            return strip_edition_label(strip_process_talk(cand))[:220]
    return None

# A line that is essentially just a date (optionally with a short kicker after
# a "|") is masthead furniture, not the story. Skip it so the title/OG land on
# the real headline. Requires a 4-digit year so real headlines mentioning a day
# ("Kampala said 28 July") are not caught.
_DATELINE = re.compile(r"^(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\.?,?\s+\d{1,2}\s+[A-Za-z]+\s+\d{4}", re.I)
_DATELINE2 = re.compile(r"^\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+\d{4}", re.I)

# ---------------------------------------------------------------- process talk
# Internal editorial process is not reader-facing copy. Phrases like "nothing
# cleared the recency gate" describe how the brief was made, not what happened in
# the market -- and because the standfirst and meta description are lifted from
# the opening line, that sentence was surfacing as the HEADLINE on quiet-day
# editions. Owners open a brief for the story, not for our workflow.
#
# Belt-and-braces at build time: even if a future generation run writes the
# phrase again, it never reaches a title, description, OG tag or standfirst.
_PROCESS_TALK = re.compile(
    r"(?:\*\*)?(?:Expert Brief\.\s*|Standing brief:\s*|Tier\s*\d[^.]*?Brief\.?\s*)?(?:\*\*)?"
    r"(?:No(?:thing)?\s+new\b[^.;]*?|Nothing\b[^.;]*?)"
    r"clear(?:ed|s)?\b[^.;]*?recency\s+gate\b[^.;]*?"
    r"(?:[.;]\s*|,\s*so\s+|\s+—\s*|\s+But\s+)",
    re.I)
_PROCESS_HINT = re.compile(
    r"recency gate|standing brief|cleared the wire|clears the bar|cleared the gate|"
    r"no fresh wire|quiet news slot|one expert read|"
    r"no fresh story|nothing new clear|no new (?:story|development)|"
    r"quiet (?:news )?(?:slot|day|session)|slow news (?:slot|day)|"
    r"one expert brief|then the board", re.I)

# ---------------------------------------------------------------- slot framing
# "Quiet news slot. So here is a number in the Bank of Tanzania's survey that
# nobody has read properly." -- that was the HEADLINE on the 28 Aug midday brief,
# on the site, in the OG card and in the feeds. It tells a reader how busy our
# news day was before it tells them anything about their business, and the actual
# story ("The mainland just overtook Zanzibar on yield") sat three lines below.
#
# The existing strip_process_talk() handles "nothing cleared the recency gate",
# but a quiet-slot opener is not a sentence to salvage a fragment from -- the
# whole line is framing. So summarise() SKIPS these outright and keeps looking
# for the lead item, rather than publishing the remainder after the full stop.
_SLOT_FRAMING = re.compile(
    r"^\W*(?:\*|_)*\s*(?:tier\s*\d\s*[\u2014-]?\s*)?"
    r"(?:quiet|slow|thin|light)\s+(?:news\s+)?"
    r"(?:slot|day|session|wire|morning|midday|afternoon|evening)\b"
    r"|^\W*(?:\*|_)*\s*no\s+(?:hard\s+)?news\b"
    r"|^\W*(?:\*|_)*\s*one\s+expert\s+brief\b"
    r"|^\W*(?:\*|_)*\s*no\s+(?:fresh|new)\s+(?:wire|news|stor(?:y|ies))\b", re.I)

# A correction notice is editorially essential but it is not the lead. It stays
# in the body; it must not become the title, standfirst or social card.
_CORRECTION_LINE = re.compile(
    r"^\W*(?:\*|_)*\s*(?:\u26a0\ufe0f?\s*)?"
    r"(?:correction|clarification|update|erratum)\b[\s:(\u2014-]", re.I)
# The same "we had no news today" opener, in every phrasing it has appeared in.
_PROCESS_TALK2 = re.compile(
    r"(?:\*\*)?(?:Tier\s*\d[^.·]*?Brief[^.·]*?[.·]\s*)?(?:\*\*)?"
    r"No(?:thing)?\s+(?:new|fresh)?\s*(?:story|development|developments|item)?s?\b"
    r"[^.;—]*?(?:clear(?:ed|s)?\b[^.;—]*?(?:gate|wire|bar)|since\s+(?:this\s+)?"
    r"(?:morning|midday|last\s+night|the\s+\w+))[^.;—]*?"
    r"(?:\s*[—-]\s*so\s+|,\s*so\s+|[.;]\s*(?:So\s+)?)",
    re.I)
# ------------------------------------------------------------- edition labels
# "Expert Brief:", "The Expert Brief \u2014", "Tonight, an expert brief:" are
# internal edition-TYPE labels, not the story. Leading with one costs the reader
# the first few words before they learn anything about their business, and it
# reads as filing furniture in a search result or a shared card. Same principle
# as the quiet-slot fix: the headline should be the main story.
_EDITION_LABEL = re.compile(
    r"^[\W\d]*"                       # bold marks, item keycap, section emoji
    r"(?:(?:tonight|today|this\s+(?:morning|midday|evening))\s*,?\s*)?"
    r"(?:the\s+|an?\s+)?"
    r"(?:tier\s*\d\s*[\u2014\u2013-]?\s*)?"
    r"expert\s+brief"
    r"\s*(?:[:.\u2014\u2013-]|\s)\s*",
    re.I)

def strip_edition_label(text):
    """Drop a leading edition-type label so the headline opens on the story."""
    if not text:
        return text
    out = _EDITION_LABEL.sub("", text, count=1)
    if out == text:
        return text
    out = re.sub(r"^[\s:;,\u2014\u2013-]+", "", out).strip()
    if out and out[:1].islower():
        out = out[:1].upper() + out[1:]
    return out or text

_STRIPPED_LOG = []

def strip_process_talk(text):
    """Remove internal editorial-process sentences from reader-facing copy."""
    if not text or not _PROCESS_HINT.search(text):
        return text
    # a markdown italic wrapper would otherwise block re-capitalisation
    wrap = text.startswith("_") and text.endswith("_") and len(text) > 2
    body = text[1:-1] if wrap else text
    out = _PROCESS_TALK.sub("", body)
    out = _PROCESS_TALK2.sub("", out, count=1)
    out = re.sub(r"^\**\s*(?:Expert Brief|Tier\s*\d\s*[\u2014-]?\s*Standing Brief)\.?\**\s*", "", out)
    out = re.sub(r"^\s*(?:So|But)\s+(?=[a-z])", "", out).strip()
    out = re.sub(r"^[,;\u2014\-\s]+", "", out)
    if out and out[:1].islower():
        out = out[:1].upper() + out[1:]
    if wrap and out:
        out = "_" + out + "_"
    if out != text:
        _STRIPPED_LOG.append((text[:70], out[:70]))
    return out or text          # never return empty: fall back to the original

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
        # framing and corrections are never the headline -- keep looking
        if _SLOT_FRAMING.match(l) or _SLOT_FRAMING.match(probe): continue
        if _CORRECTION_LINE.match(l) or _CORRECTION_LINE.match(probe): continue
        if len(l) > 40:
            cand = strip_process_talk(md_strip(re.sub(r"\s+"," ",l)))
            # a line that was nothing but process talk is not a summary -- keep looking
            if len(cand) > 40:
                return strip_edition_label(cand)[:200]
            continue
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
:root{--sand:#f6f1e7;--ink:#1f2421;--muted:#6b6656;--gold:#c8892f;--gold-d:#a86f1f;--teal:#0f6d63;--teal-d:#0a4f48;--line:#e2d8c4;--sand-2:#efe7d6;--card:#fffdf9;--serif:Georgia,"Iowan Old Style","Times New Roman",serif;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI Variable Text","Segoe UI",Inter,Roboto,"Helvetica Neue",Arial,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;--r:12px;--r-sm:6px;--r-xs:3px}
*{box-sizing:border-box}body{margin:0;font-family:var(--serif);color:var(--ink);background:var(--sand);line-height:1.68;font-size:18px;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:var(--gold);color:#231a06}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.skip{position:absolute;left:-9999px;top:0;z-index:20;background:var(--gold);color:#231a06;font:600 13px/1 var(--sans);padding:10px 14px;border-radius:0 0 var(--r-xs) 0}
.skip:focus{left:0}
a{color:var(--teal-d);text-decoration:none}
a:focus-visible{outline:2px solid var(--gold);outline-offset:2px;border-radius:var(--r-xs)}
.art p a{text-decoration:underline;text-decoration-color:rgba(15,109,99,.35);text-underline-offset:2px;text-decoration-thickness:1px}
.art p a:hover{text-decoration-color:var(--teal-d)}
header.s{background:var(--teal-d);color:#fff;padding:13px 0;border-bottom:3px solid var(--gold)}
header.s .wrap{display:flex;align-items:center;gap:10px}
header.s .wrap>a{display:flex;align-items:center;gap:10px;color:#fff}
header.s .logo{width:32px;height:32px;border-radius:var(--r-xs);background:var(--gold);color:#231a06;display:grid;place-items:center;font:700 13px/1 var(--mono);letter-spacing:.5px}
header.s b{letter-spacing:-.01em}
header.s b{font-size:16px}
.art{background:var(--card);margin:24px auto;border:1px solid var(--line);border-radius:var(--r);padding:26px 30px 34px;overflow:hidden}
/* height:auto is load-bearing. The <img> carries width="1200" height="630" for
   CLS, and that height attribute is a presentational hint that BEATS
   aspect-ratio when CSS sets width but not height. The box rendered 718x630
   instead of 718x377, so object-fit:cover cropped 241px off each side -- which
   silently guillotined every typographic data card ("Evening Wrap" -> "g Wrap").
   A photograph survives a centre-crop; a card carrying text does not. */
.art .hero{display:block;width:calc(100% + 60px);height:auto;margin:-26px -30px 20px -30px;aspect-ratio:1200/630;object-fit:cover;background:var(--teal-d)}
/* Cards and generated graphics are composed to the frame: show them whole. */
.art .hero.graphic{object-fit:contain}
.share-wrap{position:relative;display:inline-flex;align-items:center;margin:2px 0 18px}
.share-btn{display:inline-flex;align-items:center;gap:7px;font-family:var(--sans);font-size:13px;font-weight:700;color:var(--teal-d);background:var(--sand-2);border:1px solid var(--line);border-radius:20px;padding:7px 14px;cursor:pointer}
.share-btn:hover{border-color:var(--gold);color:var(--gold-d)}
.share-btn svg{width:14px;height:14px;fill:currentColor}
.share-menu{position:absolute;top:calc(100% + 6px);left:0;z-index:30;background:var(--card);border:1px solid var(--line);border-radius:var(--r-sm);box-shadow:0 10px 26px rgba(0,0,0,.18);padding:6px;min-width:190px}
.share-menu a,.share-menu button{display:flex;align-items:center;gap:9px;width:100%;text-align:left;font-family:var(--sans);font-size:13.5px;font-weight:600;color:var(--ink);background:none;border:none;padding:8px 10px;border-radius:var(--r-xs);cursor:pointer;text-decoration:none;box-sizing:border-box}
.share-menu a:hover,.share-menu button:hover{background:var(--sand-2)}
.share-toast{margin-left:10px;font-family:var(--sans);font-size:12.5px;color:var(--teal-d);font-weight:600}
.badge{font-family:var(--sans);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:4px 9px;border-radius:var(--r-xs);background:var(--sand-2);color:var(--gold-d)}
.art time{font-family:var(--sans);font-size:13px;color:var(--muted);margin-left:8px}
.art h1{font-size:clamp(28px,4.2vw,38px);line-height:1.14;margin:14px 0 20px;border-bottom:2px solid var(--gold);padding-bottom:16px;font-weight:700}
.kicker{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:2px}
.art p{margin:0 0 14px}
.item-head{font-weight:700;font-size:17px;display:inline-block;margin-top:4px}
.sowhat{display:block;background:var(--sand-2);border-left:4px solid var(--gold);padding:8px 12px;border-radius:0 var(--r-sm) var(--r-sm) 0;font-family:var(--sans);font-size:14px;margin-top:4px}
.tagline{display:inline-block;font-family:var(--sans);font-size:12px;color:var(--muted)}
.radar-item{display:block;font-family:var(--sans);font-size:14px;margin:2px 0}
.meta-line{display:block;font-family:var(--sans);font-size:14px;color:var(--muted)}
hr.divider{border:none;border-top:1px dashed var(--line);margin:16px 0}
.nav{font-family:var(--sans);font-size:14px;font-weight:600;margin:0 0 6px;display:inline-block}
.sub{font-family:var(--sans);font-size:14px;color:var(--muted);margin-top:20px;border-top:1px solid var(--line);padding-top:16px;line-height:1.9}
.more{font-family:var(--sans);font-size:13.5px;background:var(--sand-2);border-radius:var(--r-sm);padding:11px 14px;margin-top:22px}
.more a{margin-right:10px}
.sub a{font-weight:600;margin-right:14px}
footer.s{text-align:center;color:var(--muted);font-family:var(--sans);font-size:12px;padding:20px}
.art h1{letter-spacing:-.018em}
.pnrow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:22px;border-top:1px solid var(--line);padding-top:16px}
.pn{font-family:var(--sans);font-size:13.5px;font-weight:600;color:var(--teal-d);text-decoration:none;max-width:48%}
.pn:hover{text-decoration:underline}
.pn.next{margin-left:auto;text-align:right}
@media(max-width:640px){
  .wrap{padding:0 16px}
  .art{padding:20px 18px 26px;margin:16px auto}
  .art .hero{width:calc(100% + 36px);margin:-20px -18px 18px -18px}
  .art h1{font-size:25px}
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
.badge{font-family:var(--mono);letter-spacing:.08em;font-size:10.5px;border-radius:var(--r-xs);
  background:transparent;border:1px solid var(--gold);color:var(--gold-d);padding:4px 8px}
.art time{font-family:var(--mono);font-size:11.5px;letter-spacing:.04em}
/* Byline sits in the instrument-panel row with the edition and the date:
   same mono register, quieter than the badge, and a real rel="author" link. */
.kicker .byline{font:600 11.5px/1.6 var(--mono);letter-spacing:.04em;color:var(--muted)}
.kicker .byline a{color:var(--muted);border-bottom:1px solid transparent;
  transition:color .18s ease,border-color .18s ease}
.kicker .byline a:hover{color:var(--teal-d);border-bottom-color:var(--gold)}
/* Reference rail — the internal link graph, given a shape of its own. */
.refs{margin:26px 0 0;padding:18px 22px;background:var(--sand-2);
  border-left:3px solid var(--teal-d);border-radius:0 var(--r-sm) var(--r-sm) 0}
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
/* Standfirst — the one-line summary a reader (or an answer engine) should take
   away if they read nothing else. Larger, quieter, set apart from the body. */
.standfirst{font-size:1.14em;line-height:1.5;color:#3b4340;margin:0 0 20px;
  padding:0 0 18px;border-bottom:1px solid var(--line);text-wrap:pretty;font-weight:400}

/* Bare URLs pasted from the chat editions now render as anchors — keep them from
   blowing out the measure on a phone. */
.art a[href^="http"]{overflow-wrap:anywhere}

/* Rate and cost tables must survive a 360px screen without a horizontal page
   scroll: the table scrolls, the article does not. */
.art table{display:block;width:100%;max-width:100%;overflow-x:auto;
  border-collapse:collapse;font-family:var(--sans);font-size:14px;margin:18px 0;
  -webkit-overflow-scrolling:touch}
.art th,.art td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);
  vertical-align:top;white-space:nowrap}
.art th{font:700 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;
  color:var(--teal-d);border-bottom:2px solid var(--gold);white-space:nowrap}
.art tbody tr:last-child td{border-bottom:none}
.art td:first-child{white-space:normal}

/* Footer was a flat run of separators; give the link row and the geography row
   distinct weight so it reads as a masthead, not link soup. */
footer.s a{color:var(--muted);border-bottom:1px solid transparent}
footer.s a:hover{color:var(--teal-d);border-bottom-color:var(--gold)}

/* --- dark mode -------------------------------------------------------------
   Operators read the morning brief at 05:30 on a phone in a dark room. The
   cream field that reads as newsprint by day is a torch at night. Same
   editorial palette, inverted: warm ink-green ground, gold kept as the single
   accent, teal lifted so links stay legible instead of drowning. Chrome that
   uses teal as a *background* (header, hero placeholder) is set explicitly —
   swapping the variable alone would flip those to light panels. */
@media (prefers-color-scheme: dark){
  :root{--sand:#0d1512;--sand-2:#18211e;--ink:#e6e3d8;--muted:#98a29c;
        --gold:#d9a441;--gold-d:#e8bc63;--teal:#3fae9f;--teal-d:#5fc9b8;
        --line:#26302c;--card:#121a17}
  header.s{background:#0a100e;border-bottom-color:var(--gold)}
  header.s .logo{background:var(--gold);color:#0a100e}
  .art{box-shadow:none}
  .art .hero{background:#0a100e}
  .standfirst{color:#b9c2bc}
  .hcredit{color:#7d8a85}
  .sowhat{background:#1b2521}
  ::selection{background:var(--gold);color:#0a100e}
  .refs{border-left-color:var(--gold)}
  .refs h2{color:var(--gold-d)}
  .art th{color:var(--gold-d)}
  .art p a{text-decoration-color:rgba(95,201,184,.4)}
  img{opacity:.94}
  .sub-h{color:var(--gold-d)}
  .chan-n{color:var(--gold-d)}
  .chan a{color:var(--ink)}
  .chan a:hover{background:#1b2521;color:var(--teal-d)}
  footer.s .f-nav a{color:var(--ink)}
}

/* --- channel row + footer ---------------------------------------------------
   The follow block was four emoji and four links on one line: emoji doing the
   job that weight, rule and label should do, and a footer that ran the nav and
   the geography together as one string of middots. Both now read as masthead
   furniture — mono labels, hairline rules, one gold accent on hover. */
.sub{border-top:1px solid var(--line);padding-top:18px;margin-top:26px;color:var(--muted);line-height:1.6}
.sub-h{margin:0 0 2px;font:700 11px/1 var(--mono);letter-spacing:.1em;
  text-transform:uppercase;color:var(--teal-d)}
.sub-note{margin:0 0 14px;font-family:var(--sans);font-size:13.5px;line-height:1.5}
.chan{list-style:none;margin:0;padding:0;display:grid;gap:0;
  border-top:1px solid var(--line)}
.chan li{border-bottom:1px solid var(--line)}
.chan a{display:flex;align-items:baseline;gap:12px;padding:10px 2px;margin:0;line-height:1.5;
  font-family:var(--sans);color:var(--ink);
  border-left:2px solid transparent;padding-left:10px;
  transition:border-color .18s ease,background-color .18s ease,color .18s ease}
.chan a:hover{border-left-color:var(--gold);background:var(--sand-2);color:var(--teal-d)}
.chan-n{font:700 11px/1.6 var(--mono);letter-spacing:.09em;text-transform:uppercase;
  color:var(--teal-d);min-width:96px;flex:0 0 auto}
.chan-d{font-size:14px;color:var(--muted);line-height:1.5}
footer.s{border-top:1px solid var(--line);margin-top:34px;padding:22px 0 30px;text-align:left}
footer.s .f-line{margin:0 0 12px;font-family:var(--sans);font-size:13px;
  color:var(--muted);max-width:62ch}
footer.s .f-nav{margin:0 0 10px;display:flex;flex-wrap:wrap;gap:0 18px}
footer.s .f-nav a{font:600 12px/1.9 var(--sans);color:var(--ink)}
footer.s .f-geo{margin:0;font:600 10.5px/1.6 var(--mono);letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted)}
@media(max-width:640px){
  .chan a{flex-direction:column;gap:2px}
  .chan-n{min-width:0}
}

/* Operators print these briefs and take them into rate meetings. */
@media print{
  body{background:#fff;font-size:11.5pt;line-height:1.45}
  header.s,footer.s,.crumbs,.pnrow,.sub,.chan,.more,.art .hero,.hcredit{display:none!important}
  .wrap{max-width:none;padding:0}
  .art{border:none;border-radius:0;margin:0;padding:0;background:#fff}
  .art h1{font-size:19pt;border-bottom:1.5pt solid #000;page-break-after:avoid}
  .standfirst{font-size:12.5pt;border-bottom:.5pt solid #999;page-break-after:avoid}
  .item-head{page-break-after:avoid}
  .sowhat{background:#f2f2f2;border-left:2pt solid #666;page-break-inside:avoid}
  .refs{background:none;border-left:1pt solid #999;page-break-inside:avoid}
  a{color:#000;text-decoration:none}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:8.5pt;color:#555}
}
"""

# --- entity graph -----------------------------------------------------------
# Every edition page previously declared its own anonymous publisher node, so 73
# pages taught answer engines 73 unlinked "EA Hospitality Pulse" organisations.
# One @id, referenced everywhere, consolidates them into a single known entity —
# and typed, sameAs-anchored subjects let an engine resolve "Zanzibar" to a place
# rather than a keyword.
# Distribution channels, not sources — excluded from schema.org `citation`.
_SELF_DOMAINS = ("linkedin.com", "t.me", "telegram.me", "whatsapp.com", "x.com",
                 "twitter.com", "facebook.com", "instagram.com", "youtube.com",
                 "eahospitalitypulse.com", "github.io")
ORG_ID = BASE + "/#org"
SITE_ID = BASE + "/#website"
# A masthead is not an author. Every edition was attributed to the organisation,
# which tells a reader and an answer engine nothing about who did the work or why
# they would know -- and named, resolvable authorship is one of the few E-E-A-T
# signals a small publication can actually control. One Person node, one @id,
# referenced from every article and linked both ways to the organisation.
PERSON_ID = BASE + "/#author"
AUTHOR_SLUG = "about/onyango-george"
AUTHOR_NAME = "Onyango George"
AUTHOR_SHORT = "OG"
AUTHOR_BYLINE = f"{AUTHOR_NAME} ({AUTHOR_SHORT})"
CONTACT_EMAIL = "eahospitalitypulse@gmail.com"

def author_node():
    return {"@type": "Person", "@id": PERSON_ID, "name": AUTHOR_NAME,
            "alternateName": AUTHOR_SHORT,
            "email": "mailto:" + CONTACT_EMAIL,
            "url": BASE + "/" + AUTHOR_SLUG + ".html",
            "jobTitle": "Editor",
            "knowsAbout": ["East African hospitality", "hotel market analysis",
                           "travel advisories", "tourism demand", "hotel distribution"],
            "worksFor": {"@id": ORG_ID},
            "publishingPrinciples": BASE + "/methodology.html"}

def org_node():
    return {"@type": "Organization", "@id": ORG_ID, "name": "EA Hospitality Pulse",
            "url": BASE + "/",
            "email": CONTACT_EMAIL,
            "logo": {"@type": "ImageObject", "url": BASE + "/apple-touch-icon.png"},
            "founder": {"@id": PERSON_ID},
            "publishingPrinciples": BASE + "/methodology.html",
            "sameAs": [CHANNELS[k] for k in ("telegram", "linkedin", "whatsapp")
                       if CHANNELS.get(k)]}

ABOUT_ENTITIES = [
    {"@type": "Place", "name": "Kenya", "sameAs": "https://en.wikipedia.org/wiki/Kenya"},
    {"@type": "Place", "name": "Uganda", "sameAs": "https://en.wikipedia.org/wiki/Uganda"},
    {"@type": "Place", "name": "Tanzania", "sameAs": "https://en.wikipedia.org/wiki/Tanzania"},
    {"@type": "Place", "name": "Zanzibar", "sameAs": "https://en.wikipedia.org/wiki/Zanzibar"},
    {"@type": "Place", "name": "Rwanda", "sameAs": "https://en.wikipedia.org/wiki/Rwanda"},
    {"@type": "Thing", "name": "Hospitality industry",
     "sameAs": "https://en.wikipedia.org/wiki/Hospitality_industry"},
    {"@type": "Thing", "name": "Tourism", "sameAs": "https://en.wikipedia.org/wiki/Tourism"},
]

# Every edition opens in Telegram clothes: a brand masthead line, then a date-and-
# flags line, then an italic intro. On the web the site header carries the brand and
# the kicker carries the edition and date — so all 73 pages opened with the same two
# lines of duplicated chrome before any journalism. Strip those two, and promote the
# editor's italic intro to a real standfirst: a quotable, self-contained summary sat
# under the headline, which is what answer engines lift and what readers scan.
_BRAND_RE = re.compile(r"EA\s+HOSPITALITY\s+PULSE", re.I)
_SEG_SPLIT = re.compile(r"<br\s*/?>")

def _seg_text(seg):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", seg))).strip()

def lead_furniture(body_html):
    """Returns (standfirst_html, body_html). Conservative: only strips leading
    segments, only masthead/date/divider lines, and stops at the first real line."""
    standfirst = ""
    stripping = True
    out = []
    for blk in re.split(r"(?<=</p>)\s*", body_html):
        if not stripping or not blk.strip().startswith("<p>"):
            out.append(blk); continue
        segs = _SEG_SPLIT.split(blk.strip()[3:-4])
        keep = []
        for seg in segs:
            txt = _seg_text(seg)
            if stripping and not keep:
                if not txt: continue
                if _BRAND_RE.search(txt): continue
                probe = re.sub(r"^[^0-9A-Za-z]+", "", md_strip(txt))
                if _DATELINE.match(probe) or _DATELINE2.match(probe): continue
                if set(txt) <= set("\u2501\u2014-\u2013_ "): continue
                _em = re.match(r"^\s*<em>(.*?)</em>\s*$", seg.strip(), re.S)
                if _em and not standfirst:
                    _raw = _em.group(1).strip()
                    _sf = strip_process_talk(_raw)
                    # an italic intro that was purely process talk is dropped, not shown
                    if _PROCESS_HINT.search(_raw) and len(_sf) < 25:
                        continue
                    standfirst = _sf; continue
                stripping = False
            keep.append(seg)
        if keep:
            out.append("<p>" + "<br>".join(keep) + "</p>")
            stripping = False
    body = "\n".join(x for x in out if x.strip())
    sf = f'<p class="standfirst">{standfirst}</p>' if standfirst else ""
    return sf, body

# ---- snippet construction ---------------------------------------------------
# Search Console, 1 Aug - 13 Sep 2026: 1,693 impressions, 5 clicks. Several
# edition pages sat at average position 3.6-5.7 and took ZERO clicks. That is
# not a ranking problem, it is a snippet problem, and the export showed exactly
# why: the <title> and the meta description were the same sentence. Google
# rendered the headline, then rendered the headline again underneath it, so the
# result carried no information the searcher did not already have from the link.
#
# A title also has ~60 characters of visible width. Ours ran to 120, spending
# the back half on "| Morning Brief, 25 August 2026 - EA Hospitality Pulse",
# which no searcher ever saw and which made every result on the site look
# identical to every other one.
_LEAD_LABEL = re.compile(
    r"^\s*(?:special|exclusive|analysis|briefing|deep\s*dive|part\s+\d+(?:\s+of\s+\d+)?)"
    r"\s*[:\u2014\u2013-]\s*", re.I)

def _trim(text, limit):
    """Truncate on a word boundary, never mid-word."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" .,;:\u2014\u2013-")
    return (cut or text[:limit]) + "\u2026"

def serp_title(lead):
    """Headline first, inside the window Google actually renders."""
    t = _LEAD_LABEL.sub("", lead or "").strip() or (lead or "")
    t = t.rstrip(" .")
    return _trim(t, 52) + " | EA Pulse"

_SOWHAT_RE = re.compile(r'<span class="sowhat">(.*?)</span>', re.S)

def serp_description(standfirst_html, body_html, lead):
    """The description must ADD to the title, never repeat it.

    Preference order: the editor's standfirst (a written one-line summary), then
    the first 'so what' line (the operator action, which is the most quotable
    thing in the brief and the reason someone clicks), then the first body
    sentence that is not the headline. Falls back to the headline only when the
    edition genuinely carries nothing else."""
    def _clean(x):
        x = re.sub(r"<[^>]+>", " ", x or "")
        x = html.unescape(x)
        x = re.sub(r"^[^0-9A-Za-z\u201c\u2018\"']+", "", x)   # drop leading emoji/flags
        # The 'so what' line opens with our own internal label. In a SERP that
        # spends nine characters of a 155-character window telling the searcher
        # nothing, so lead on the substance instead.
        x = re.sub(r"^so[\s\u2014-]*what\s*[:\u2014,-]\s*", "", x, flags=re.I)
        return re.sub(r"\s+", " ", x).strip()

    lead_key = re.sub(r"[^a-z0-9]", "", (lead or "").lower())[:45]
    def _usable(cand):
        if not cand or len(cand) < 45:
            return False
        # A description is the one line of ours a searcher reads before deciding.
        # It must not be a sentence about how the brief was made, and it must not
        # open mid-clause because a <br> happened to fall there.
        if _PROCESS_HINT.search(cand) or _SLOT_FRAMING.match(cand):
            return False
        if not cand[:1].isupper() and not cand[:1].isdigit():
            return False
        key = re.sub(r"[^a-z0-9]", "", cand.lower())[:45]
        return key != lead_key                       # never echo the title

    cands = []
    sf = _clean(standfirst_html)
    if sf:
        cands.append(sf)
    for m in _SOWHAT_RE.finditer(body_html or ""):
        cands.append(_clean(m.group(1)))
    for m in re.finditer(r"<p>(.*?)</p>", body_html or "", re.S):
        for seg in re.split(r"<br\s*/?>", m.group(1)):
            cands.append(_clean(seg))

    for c in cands:
        if _usable(c):
            return _trim(c, 155)
    return _trim(lead or "", 155)


def edition_page(e, siblings=None, prev=None, nxt=None, hero=None, credit=None):
    # One clean headline drives <title>, description, OG/Twitter, JSON-LD and H1.
    lead = clean_headline(e["summary"]) or e["edition"]
    short_date = e["dateDisplay"].split(", ", 1)[-1] if ", " in e["dateDisplay"] else e["dateDisplay"]
    _t = lead if len(lead) <= 62 else lead[:62].rsplit(" ", 1)[0] + "…"
    title = serp_title(lead)
    # A social card has far more room than a SERP line, and the edition + date
    # is genuinely useful context when a brief is shared into a WhatsApp group.
    social_title = f"{_t} — {e['edition']}, {short_date}"
    url = f"{BASE}/editions/{e['id']}.html"
    img = f"{BASE}/og/{e['id']}.png"          # share card (OG/Twitter meta)
    hero_src = f"../og/{hero}" if hero else f"../og/{e['id']}.png"   # clean in-page photo
    # Non-photographic heroes are composed to the frame and must not be cropped.
    _hk = (credit or {}).get("source_kind") or ""
    hero_cls = " graphic" if _hk in ("data-card", "illustration") else ""
    # Clean, word-boundary headline (<=110 chars — Google's NewsArticle limit).
    headline = lead.split(".")[0].strip() or lead
    if len(headline) > 110:
        headline = headline[:110].rsplit(" ", 1)[0] + "…"
    h1text = headline if headline.endswith(("…", ".", "?", "!")) else headline + "."
    standfirst, body_html = lead_furniture(e["bodyHtml"])
    desc = serp_description(standfirst, body_html, lead)
    _plain = re.sub(r"<[^>]+>", " ", body_html)
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
    # Answer engines weight sourced content. Every edition already links its
    # primary sources inline; surfacing them as schema.org `citation` tells a
    # retrieval engine *what this brief is built on* instead of making it infer.
    _cites, _seen = [], set()
    for _m in re.finditer(r'href="(https?://[^"]+)"', body_html):
        _u = _m.group(1)
        if _u.startswith(BASE) or "eahospitalitypulse.com" in _u:
            continue
        _root = re.sub(r"^https?://(www\.)?", "", _u).split("/")[0].lower()
        # Our own distribution channels are not evidence. Declaring a LinkedIn
        # post as `citation` would tell an answer engine this brief is sourced
        # from social media, which is the opposite of the truth.
        if any(_root.endswith(_d) for _d in _SELF_DOMAINS):
            continue
        if _u in _seen:
            continue
        _seen.add(_u); _cites.append(_u)
        if len(_cites) >= 12:
            break
    # Head-level prev/next: the crawl hint <a rel> cannot give, so an engine can
    # walk the archive in order without re-parsing every page body.
    head_rel = ""
    if prev: head_rel += f'<link rel="prev" href="{BASE}/editions/{prev["id"]}.html">\n'
    if nxt:  head_rel += f'<link rel="next" href="{BASE}/editions/{nxt["id"]}.html">\n'
    ld = {
        "@context":"https://schema.org","@type":"NewsArticle",
        "headline": headline,
        "datePublished": e["date"], "dateModified": e["date"],
        "description": desc, "url": url, "mainEntityOfPage": url,
        "image": [img], "inLanguage": "en", "isAccessibleForFree": True,
        "articleSection": e["edition"],
        "author":author_node(),
        "publisher":org_node(),
        "isPartOf":{"@type":"WebSite","@id":SITE_ID,"name":"EA Hospitality Pulse","url":BASE+"/",
                    "publisher":{"@id":ORG_ID}},
        "keywords":"East Africa hospitality, "+e["edition"]+", Kenya, Uganda, Tanzania, Zanzibar, Rwanda, travel advisories, hotel demand, tourism",
        "wordCount": wordcount,
        "speakable":{"@type":"SpeakableSpecification","cssSelector":["h1",".standfirst",".sowhat"]},
        "about":ABOUT_ENTITIES,
        "spatialCoverage":[a for a in ABOUT_ENTITIES if a["@type"]=="Place"]
    }
    if _cites:
        ld["citation"] = [{"@type": "WebPage", "url": u} for u in _cites]
    crumbs = {
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":BASE+"/"},
            {"@type":"ListItem","position":2,"name":"Editions","item":BASE+"/#archive"},
            {"@type":"ListItem","position":3,"name":e["edition"]+" — "+e["dateDisplay"],"item":url},
        ]}
    credit_html = ""
    if credit:
        # Wikimedia artist fields are free text and are sometimes a paragraph of
        # contact instructions. Credit the NAME; the full field stays in the JSON.
        _artraw = re.sub(r"<[^>]+>", " ", str(credit.get("artist") or "")).strip()
        _artraw = re.sub(r"\s+", " ", _artraw)
        _m = re.search(r"photo(?:graph)? (?:was )?taken by\s+"
                       r"((?:[A-Z]\.\s+|[A-Z][\w'\u2019-]+\s+){0,3}[A-Z][\w'\u2019-]+)",
                       _artraw, re.I)
        if _m:
            _artraw = _m.group(1)
        elif len(_artraw) > 60:
            _artraw = re.split(r"(?<=[.;])\s", _artraw)[0][:60].rsplit(" ", 1)[0] + "\u2026"
        _art = html.escape(_artraw or "Unknown")
        _lic = html.escape(credit.get("license") or "See source")
        _src = html.escape(credit.get("descurl") or "")
        _licurl = html.escape(credit.get("licenseurl") or "")
        _srcname = html.escape(credit.get("source") or "Wikimedia Commons")
        # Say what the reader is actually looking at. "Photo:" on a typographic
        # data card is simply untrue, and an AI hero has to say so plainly --
        # "Image:" is not disclosure when the result looks like reportage.
        _kind = credit.get("source_kind") or ""
        _label = {"ai": "AI-generated", "data-card": "Graphic",
                  "illustration": "Illustration"}.get(_kind, "Photo")
        _lictag = (f'<a href="{_licurl}" target="_blank" rel="noopener nofollow">{_lic}</a>' if _licurl else _lic)
        _srctag = (f'<a href="{_src}" target="_blank" rel="noopener nofollow">{_srcname}</a>' if _src else _srcname)
        credit_html = (f'<p class="hcredit">{_label}: {_art} \u00b7 {_srctag} \u00b7 {_lictag}</p>')
    _guides = load_guide_links()[:5]
    guides_html = ""
    if _guides:
        _gl = "".join(
            f'<li><a href="../guides/{g["slug"]}.html">{html.escape(g["title"])}</a></li>'
            for g in _guides)
        guides_html = (f'<aside class="refs" aria-label="Reference guides">'
                       f'<h2>Reference</h2><ul>'
                       f'<li><a href="../trackers/index.html"><b>Live trackers</b> \u2014 park fees, '
                       f'advisories, rates, costs, pipeline and MICE</a></li>{_gl}</ul></aside>')
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
<meta name="author" content="{AUTHOR_BYLINE}">
<meta name="news_keywords" content="{news_kw}">
<link rel="canonical" href="{url}">
{head_rel}<meta name="theme-color" content="#0a4f48" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0d1512" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="../feed.xml">
<meta property="og:type" content="article"><meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="{html.escape(social_title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<meta property="og:image:alt" content="{html.escape(social_title)}">
<meta name="twitter:image:alt" content="{html.escape(social_title)}">
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
.hcredit{{margin:-8px 0 18px;font:12px/1.5 var(--sans);color:#7c8a86}}
.hcredit a{{color:#5566a3;text-decoration:none}}</style></head>
<body>
<a class="skip" href="#content">Skip to the brief</a>
<header class="s"><div class="wrap"><a href="/"><span class="logo" aria-hidden="true">EA</span><b>EA Hospitality Pulse</b></a></div></header>
<main class="wrap" id="content">
  <article class="art">
    <img class="hero{hero_cls}" src="{hero_src}" width="1200" height="630" alt="{html.escape(e['edition']+' — '+e['dateDisplay'])}" loading="eager" fetchpriority="high" decoding="async">
    {credit_html}
    {crumb_html}
    <div class="kicker"><span class="badge">{html.escape(e['edition'])}</span><time datetime="{e['date']}">{html.escape(e['dateDisplay'])}</time><span class="byline">By <a href="../{AUTHOR_SLUG}.html" rel="author">{AUTHOR_BYLINE}</a></span></div>
    <h1>{html.escape(h1text)}</h1>
    {standfirst}
    {share_widget_html(url, social_title)}
    {body_html}
    {sib_html}
    {guides_html}
    {pn_html}
    <div class="sub">
      <h2 class="sub-h">Follow the Pulse</h2>
      <p class="sub-note">Daily briefs across Kenya, Uganda, Tanzania, Zanzibar and Rwanda.</p>
      <ul class="chan">
        <li><a href="{CHANNELS['telegram']}" target="_blank" rel="noopener"><span class="chan-n">Telegram</span><span class="chan-d">The full edition, three times a day</span></a></li>
        <li><a href="{CHANNELS['whatsapp']}" target="_blank" rel="noopener"><span class="chan-n">WhatsApp</span><span class="chan-d">The daily skim</span></a></li>
        <li><a href="{CHANNELS['linkedin']}" target="_blank" rel="noopener"><span class="chan-n">LinkedIn</span><span class="chan-d">The Big Read, most evenings</span></a></li>
        <li><a href="../archive.html"><span class="chan-n">Archive</span><span class="chan-d">Every edition, searchable</span></a></li>
      </ul>
    </div>
  </article>
</main>
<footer class="s"><div class="wrap">
<p class="f-line">EA Hospitality Pulse — daily intelligence for city, bush and beach properties across East Africa. Free to read, free to republish with attribution.</p>
<p class="f-nav"><a href="../index.html">Home</a><a href="../trackers/index.html">Trackers</a><a href="../archive.html">Archive</a><a href="../methodology.html">Methodology</a><a href="../{AUTHOR_SLUG}.html">Editor</a><a href="../faq.html">FAQ</a><a href="../republish.html">Republish</a><a href="../credits.html">Image credits</a></p>
<p class="f-geo">Kenya &middot; Uganda &middot; Tanzania &middot; Zanzibar &middot; Rwanda</p>
</div></footer>
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
        _srcname = _a.get("source") or "Wikimedia Commons"
        _titletag = (f'<a href="{html.escape(_src)}" target="_blank" rel="noopener">{html.escape(_title or _srcname)}</a>'
                     if _src else html.escape(_title or _srcname))
        rows.append(f'<tr><td>Edition {html.escape(_eid)}</td>'
                    f'<td>{_titletag}{_by}</td>'
                    f'<td>{_lic_html}</td></tr>')
    body = "\n".join(rows)
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Image credits | EA Hospitality Pulse</title>
<meta name="description" content="Attribution for imagery used across EA Hospitality Pulse — data cards (own work), official press and media libraries, and legacy Creative Commons photography.">
<link rel="canonical" href="{BASE}/credits.html">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<style>{ARTICLE_CSS}
.art table{{width:100%;border-collapse:collapse;font-family:Helvetica Neue,Arial,sans-serif;font-size:14px}}
.art th,.art td{{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}}
.art th{{background:var(--sand-2)}}
.tw{{overflow-x:auto}}
</style></head>
<body>
<header class="s"><div class="wrap"><a href="/"><span class="logo" aria-hidden="true">EA</span><b>EA Hospitality Pulse</b></a></div></header>
<div class="wrap"><article class="art">
<a class="nav" href="./index.html">← Home</a>
<h1>Image credits</h1>
<p>Most editions lead with a <strong>data card</strong> — a typographic hero carrying the edition's own headline figure. For a market-intelligence brief that is content rather than decoration, and it cannot be off-topic. Those cards are our own work.</p>
<p>Where a photograph is genuinely the right image, we use <strong>official press and media libraries</strong> — national tourism boards, park authorities, hotel groups and airlines — which publish images for editorial reuse, plus public-health imagery from WHO and Africa CDC. We do not use press-agency or news-outlet photographs, and we do not hot-link images from other publishers’ servers. Historic editions may still carry Creative Commons photography from Wikimedia Commons under its original licence; that source was retired on 28 August 2026 because it supplied regional scenery unrelated to the story. Source and licence for every image are listed below.</p>
<div class="tw"><table><thead><tr><th>Used for</th><th>Source (Wikimedia Commons)</th><th>Licence</th></tr></thead>
<tbody>
{body}
</tbody></table></div>
<p class="meta-line">Base illustrations (savannah, Nairobi skyline, Zanzibar beach) are licensed stock held in the repository. Questions about attribution: eahospitalitypulse@gmail.com.</p>
</article></div>
<footer class="s"><div class="wrap">
<p class="f-line">EA Hospitality Pulse — daily intelligence for city, bush and beach properties across East Africa.</p>
<p class="f-nav"><a href="./index.html">Home</a><a href="./archive.html">Archive</a><a href="./methodology.html">Methodology</a><a href="./faq.html">FAQ</a></p>
<p class="f-geo">Kenya &middot; Uganda &middot; Tanzania &middot; Zanzibar &middot; Rwanda</p>
</div></footer>
</body></html>"""
    open(os.path.join(HERE,"credits.html"),"w",encoding="utf-8").write(page)

# ---- honest lastmod ---------------------------------------------------------
# Every static URL in the sitemap carried today's date, rebuilt daily — so the
# sitemap claimed the terms page changed this morning when it last changed in
# August. Search engines discount a lastmod they can see is wrong, which costs
# the URLs where the date IS meaningful. Read the real date from git.
_GIT_MTIME_CACHE = {}

def file_lastmod(rel, fallback):
    """Last commit date for a tracked file (YYYY-MM-DD); mtime, then fallback."""
    if rel in _GIT_MTIME_CACHE:
        return _GIT_MTIME_CACHE[rel]
    val = None
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                           capture_output=True, text=True, cwd=HERE, timeout=20)
        out = (r.stdout or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", out):
            val = out
    except Exception:
        pass
    if not val:
        try:
            ts = os.path.getmtime(os.path.join(HERE, rel))
            val = datetime.date.fromtimestamp(ts).isoformat()
        except Exception:
            val = fallback
    _GIT_MTIME_CACHE[rel] = val
    return val


# ---- static-page head hygiene ----------------------------------------------
# index.html and archive.html get their heads patched at build time; the other
# hand-maintained pages never did. So the FAQ — the single most citable page on
# the site — carried no robots directive at all, which means Google applies the
# conservative default snippet length and an AI Overview has less of the answer
# to lift. Same story for og:locale, image alts, and two pages with no social
# tags whatsoever. This pass writes the missing tags idempotently, inside a
# marked block, so it can be re-run or reverted without touching hand-written
# markup.
SEO_MARK_OPEN  = "<!--SEO_HEAD-->"
SEO_MARK_CLOSE = "<!--/SEO_HEAD-->"
INDEXABLE_ROBOTS = ('<meta name="robots" content="index,follow,'
                    'max-image-preview:large,max-snippet:-1,max-video-preview:-1">')

# Pages the build already owns (index/archive) or that must never be indexed
# (radar is an internal ops board) are handled elsewhere or left alone.
_SEO_SKIP = {"index.html", "archive.html", "radar.html", "404.html", "signals.html"}

def _head_has(head, needle):
    return needle in head

def polish_static_heads():
    """Idempotently add the answer-engine meta that hand-written pages lack."""
    targets = [f for f in sorted(os.listdir(HERE))
               if f.endswith(".html") and f not in _SEO_SKIP]
    tools_dir = os.path.join(HERE, "tools")
    if os.path.isdir(tools_dir):
        targets += [os.path.join("tools", t) for t in sorted(os.listdir(tools_dir))
                    if t.endswith(".html")]
    touched = []
    for rel in targets:
        path = os.path.join(HERE, rel)
        try:
            doc = open(path, encoding="utf-8").read()
        except Exception:
            continue
        # strip any previous run's block so the pass is idempotent
        doc = re.sub(re.escape(SEO_MARK_OPEN) + r".*?" + re.escape(SEO_MARK_CLOSE) + r"\n?",
                     "", doc, flags=re.S)
        if "</head>" not in doc:
            continue
        head = doc.split("</head>", 1)[0]
        add = []
        if '<meta name="robots"' not in head:
            add.append(INDEXABLE_ROBOTS)
        if 'rel="alternate" type="application/rss+xml"' not in head:
            depth = "../" if rel.startswith("tools/") else ""
            add.append(f'<link rel="alternate" type="application/rss+xml" '
                       f'title="EA Hospitality Pulse" href="{depth}feed.xml">')
        if '<meta name="color-scheme"' not in head:
            add.append('<meta name="color-scheme" content="light dark">')
        if '<meta name="theme-color"' not in head:
            add.append('<meta name="theme-color" content="#0a4f48">')

        # title/description are the only reliable copy on a hand-written page —
        # reuse them rather than inventing social copy the author never wrote.
        _t = re.search(r"<title>(.*?)</title>", head, re.S)
        _d = re.search(r'<meta name="description" content="([^"]*)"', head)
        page_title = html.unescape(_t.group(1).strip()) if _t else "EA Hospitality Pulse"
        page_desc = html.unescape(_d.group(1).strip()) if _d else ""
        _c = re.search(r'<link rel="canonical" href="([^"]*)"', head)
        page_url = _c.group(1) if _c else f"{BASE}/{rel}"

        if '<meta property="og:' not in head:
            add.append('<meta property="og:type" content="website">')
            add.append('<meta property="og:site_name" content="EA Hospitality Pulse">')
            add.append(f'<meta property="og:title" content="{html.escape(page_title)}">')
            if page_desc:
                add.append(f'<meta property="og:description" content="{html.escape(page_desc)}">')
            add.append(f'<meta property="og:url" content="{html.escape(page_url)}">')
            add.append(f'<meta property="og:image" content="{BASE}/og/default.png">')
            add.append('<meta property="og:image:width" content="1200">')
            add.append('<meta property="og:image:height" content="630">')
        if '<meta name="twitter:card"' not in head:
            add.append('<meta name="twitter:card" content="summary_large_image">')
            add.append(f'<meta name="twitter:title" content="{html.escape(page_title)}">')
            if page_desc:
                add.append(f'<meta name="twitter:description" content="{html.escape(page_desc)}">')
            add.append(f'<meta name="twitter:image" content="{BASE}/og/default.png">')
        # An image with no alt is an image an answer engine cannot describe.
        _alt = html.escape(page_title)
        if '<meta property="og:image:alt"' not in head:
            add.append(f'<meta property="og:image:alt" content="{_alt}">')
        if '<meta name="twitter:image:alt"' not in head:
            add.append(f'<meta name="twitter:image:alt" content="{_alt}">')
        if '<meta property="og:locale"' not in head:
            add.append('<meta property="og:locale" content="en_GB">')
        if '<link rel="canonical"' not in head:
            add.append(f'<link rel="canonical" href="{BASE}/{rel}">')

        if add:
            doc = doc.replace("</head>",
                              SEO_MARK_OPEN + "\n" + "\n".join(add) + "\n"
                              + SEO_MARK_CLOSE + "\n</head>", 1)
            touched.append((rel, len(add)))
        open(path, "w", encoding="utf-8").write(doc)

    # A 404 that is indexable is a 404 competing with real pages in the index.
    _404 = os.path.join(HERE, "404.html")
    if os.path.exists(_404):
        d404 = open(_404, encoding="utf-8").read()
        if '<meta name="robots"' not in d404 and "</head>" in d404:
            d404 = d404.replace("</head>",
                '<meta name="robots" content="noindex,follow">\n</head>', 1)
            open(_404, "w", encoding="utf-8").write(d404)
            touched.append(("404.html", 1))
    if touched:
        print("static head hygiene: " + ", ".join(f"{r} (+{n})" for r, n in touched))
    return touched


# ---- author page ------------------------------------------------------------
# The Person node had an @id but no home of its own, so it pointed at the
# methodology page -- a page about the process, not the person. An author entity
# with nowhere to resolve to is the weakest version of the signal.
#
# What makes this page carry weight is not a biography. It is the published
# record, and the record is generated here rather than typed, so it cannot drift
# out of date between edits: edition count and run length from editions-src, the
# forecast record straight from ledger/predictions.csv including the calls that
# were wrong, dataset and guide counts from the builds that just ran. A claim a
# reader can check beats a credential a reader has to take on trust.
AUTHOR_SLUG = "about/onyango-george"

def ledger_record():
    """Public forecast record, read from the ledger source rather than restated."""
    import csv
    try:
        rows = list(csv.DictReader(open(os.path.join(HERE, "ledger", "predictions.csv"),
                                        encoding="utf-8")))
    except Exception:
        return None
    st = {}
    for r in rows:
        st[r.get("status", "?")] = st.get(r.get("status", "?"), 0) + 1
    resolved = st.get("correct", 0) + st.get("incorrect", 0) + st.get("partial", 0)
    if not resolved:
        return None
    score = st.get("correct", 0) + 0.5 * st.get("partial", 0)
    return {"total": len(rows), "open": st.get("open", 0), "resolved": resolved,
            "correct": st.get("correct", 0), "partial": st.get("partial", 0),
            "incorrect": st.get("incorrect", 0),
            "accuracy": round(100 * score / resolved)}


def build_author_page(editions, guides, trackers):
    dates = sorted(e["date"] for e in editions if e.get("date"))
    if not dates:
        return None
    try:
        first = datetime.date.fromisoformat(dates[0]).strftime("%-d %B %Y")
    except Exception:
        first = dates[0]
    n_ed, n_guides = len(editions), len(guides or [])
    n_trk = len(trackers or [])
    n_rec = sum(t.get("records", 0) for t in (trackers or []))
    lr = ledger_record()
    url = f"{BASE}/{AUTHOR_SLUG}.html"

    same_as = [CHANNELS[k] for k in ("linkedin", "telegram", "whatsapp") if CHANNELS.get(k)]
    person = author_node()
    person["url"] = url
    person["mainEntityOfPage"] = url
    person["sameAs"] = same_as
    person["description"] = (
        "Consultant and analyst covering hospitality across Kenya, Uganda, Tanzania, "
        "Zanzibar and Rwanda, and editor of the EA Hospitality Pulse daily brief.")

    ld = [{"@context": "https://schema.org", "@type": "ProfilePage",
           "@id": url + "#profile", "url": url,
           "name": f"{AUTHOR_BYLINE} \u2014 editor, EA Hospitality Pulse",
           "dateCreated": dates[0], "dateModified": datetime.date.today().isoformat(),
           "inLanguage": "en", "isPartOf": {"@id": SITE_ID},
           "mainEntity": person},
          {"@context": "https://schema.org", "@type": "BreadcrumbList",
           "itemListElement": [
               {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
               {"@type": "ListItem", "position": 2, "name": AUTHOR_BYLINE, "item": url}]}]

    # The forecast record is the strongest thing on this page precisely because
    # it includes the misses. Stating them plainly is the whole argument.
    if lr:
        record = f"""<h2>The record</h2>
    <p>Anyone can sound confident about a market. The only part of that which can
    be checked is a forecast logged before the outcome is known, with a falsifiable
    test and a resolve-by date attached, then scored in public when the evidence
    lands.</p>
    <div class="tk-wrap"><table class="tk"><tbody>
      <tr><td class="k">Forecasts logged</td><td class="num">{lr['total']}</td>
          <td>Every forward-looking call made in the brief since {first}</td></tr>
      <tr><td class="k">Resolved and scored</td><td class="num">{lr['resolved']}</td>
          <td>{lr['correct']} correct, {lr['partial']} partial, {lr['incorrect']} wrong</td></tr>
      <tr><td class="k">Accuracy on resolved calls</td><td class="num">{lr['accuracy']}%</td>
          <td>Partial credit counted as a half</td></tr>
      <tr><td class="k">Still open</td><td class="num">{lr['open']}</td>
          <td>Logged with a resolve-by date, not yet due</td></tr>
    </tbody></table></div>
    <p>The {lr['incorrect']} calls that were wrong stay published with the ones that
    were right. That is the point of the ledger: a record you can only trust if it
    shows the misses. <a href="../index.html#ledger">See the full track record</a>.</p>"""
    else:
        record = ""

    body = f"""<h2>What I do</h2>
    <p>I advise hospitality businesses in East Africa on market, pricing and
    distribution questions, and I publish what I learn doing it. <b>EA Hospitality
    Pulse</b> is the public half of that work: a brief for the people who actually
    carry the decision &mdash; owners and general managers of hotels, lodges, camps
    and beach resorts in Kenya, Uganda, Tanzania, Zanzibar and Rwanda.</p>
    <p>It runs three times a day, it is free, there is no paywall and no signup
    wall, and every item closes with something to do rather than something to know.
    Since {first} that has come to <b>{n_ed} editions</b>, {n_guides} reference
    guides and {n_trk} live datasets carrying {n_rec} sourced records.</p>

    {record}

    <h2>What I cover</h2>
    <p>Five markets &mdash; Kenya, Uganda, Tanzania, Zanzibar and Rwanda &mdash;
    across the three segments that behave differently enough to need separate
    reading: city and MICE, bush and safari, beach and coast. Ethiopia is tracked
    as a comparator and transmission market rather than a home one.</p>
    <p>The recurring subjects are the ones that move a booking or a margin: travel
    advisory levels and what they actually do to demand, park and permit pricing,
    air connectivity and route decisions, distribution economics, the cost side,
    new supply, and the conference calendar that compresses a city&rsquo;s room stock
    for a week at a time. Those live as
    <a href="../trackers/index.html">continuously maintained trackers</a>, not as
    one-off articles.</p>

    <h2>How I work</h2>
    <p>Claims are graded, not asserted. <b>Confirmed</b> means read directly from a
    primary or official source. <b>Reported</b> means credible press carried it and
    I have not independently confirmed it. <b>Early signal</b> means an upstream
    indicator suggests something is coming and is labelled as inference until it
    resolves. Figures carry the source they came from and the period they cover,
    and anything outside its re-confirmation window is flagged rather than left
    looking current.</p>
    <p>Corrections are published in the next edition rather than quietly edited in.
    The <a href="../methodology.html">methodology page</a> sets out the sourcing
    standard, the verification bar and the correction protocol in full.</p>

    <h2>Get in touch</h2>
    <p>Questions, corrections, data, or a market I should be watching and
    am not: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. Corrections get
    priority over everything else in the inbox.</p>"""

    sibs = "".join(
        f'<li><a href="../{u}"><span class="chan-n">{n}</span>'
        f'<span class="chan-d">{d}</span></a></li>'
        for n, d, u in [
            ("Methodology", "Sourcing, grading and corrections", "methodology.html"),
            ("Track record", "Every forecast, scored in public", "index.html#ledger"),
            ("Trackers", "Seven live datasets, maintained daily", "trackers/index.html"),
            ("Archive", "Every edition, searchable", "archive.html")])

    ld_html = "\n".join(f'<script type="application/ld+json">{json.dumps(b)}</script>'
                        for b in ld)
    desc = ("Consultant and analyst covering hospitality in Kenya, Uganda, Tanzania, "
            "Zanzibar and Rwanda. Editor of the EA Hospitality Pulse daily brief.")
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Onyango George (OG) \u2014 editor, EA Hospitality Pulse</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="{AUTHOR_BYLINE}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0a4f48" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0d1512" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="../feed.xml">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="Onyango George (OG) \u2014 editor, EA Hospitality Pulse">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og/default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Onyango George (OG), editor of EA Hospitality Pulse">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Onyango George (OG) \u2014 editor, EA Hospitality Pulse">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{BASE}/og/default.png">
<meta name="twitter:image:alt" content="Onyango George (OG), editor of EA Hospitality Pulse">
<link rel="icon" href="../favicon.png"><link rel="apple-touch-icon" href="../apple-touch-icon.png">
{ld_html}
<style>{ARTICLE_CSS}
.tk-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:0 0 16px}}
table.tk{{width:100%;border-collapse:collapse;font-family:var(--sans);font-size:14px}}
table.tk td{{padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.5}}
table.tk td.k{{font-weight:600;min-width:180px}}
table.tk td.num{{font-family:var(--mono);font-size:15px;white-space:nowrap;color:var(--teal-d);font-weight:700}}
table.tk tbody tr:last-child td{{border-bottom:none}}
.art h2{{font-size:19px;margin:30px 0 10px;letter-spacing:-.01em}}
.who{{font:600 11px/1.6 var(--mono);letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);margin:0 0 14px}}
@media (prefers-color-scheme: dark){{table.tk td.num{{color:var(--gold-d)}}}}
</style></head>
<body>
<a class="skip" href="#content">Skip to the profile</a>
<header class="s"><div class="wrap"><a href="/"><span class="logo" aria-hidden="true">EA</span><b>EA Hospitality Pulse</b></a></div></header>
<main class="wrap" id="content">
  <article class="art">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../index.html">Home</a>
      <span aria-hidden="true">/</span><span aria-current="page">{AUTHOR_BYLINE}</span></nav>
    <h1>{AUTHOR_BYLINE}</h1>
    <p class="who">Editor, EA Hospitality Pulse &middot; Consultant &amp; analyst, East African hospitality</p>
    <p class="standfirst">I advise hospitality businesses in Kenya, Uganda, Tanzania,
    Zanzibar and Rwanda, and publish a daily market brief for the owners and
    managers who have to act on the same information.</p>
    {body}
    <div class="sub">
      <h2 class="sub-h">Elsewhere</h2>
      <p class="sub-note">The brief publishes three times a day across all three channels.</p>
      <ul class="chan">{sibs}</ul>
    </div>
  </article>
</main>
<footer class="s"><div class="wrap">
<p class="f-line">EA Hospitality Pulse &mdash; daily intelligence for city, bush and beach properties across East Africa. Free to read, free to republish with attribution.</p>
<p class="f-nav"><a href="../index.html">Home</a><a href="../trackers/index.html">Trackers</a><a href="../archive.html">Archive</a><a href="../methodology.html">Methodology</a><a href="../{AUTHOR_SLUG}.html">Editor</a><a href="../faq.html">FAQ</a><a href="../republish.html">Republish</a></p>
<p class="f-geo">Kenya &middot; Uganda &middot; Tanzania &middot; Zanzibar &middot; Rwanda</p>
</div></footer>
</body></html>"""
    os.makedirs(os.path.join(HERE, "about"), exist_ok=True)
    open(os.path.join(HERE, AUTHOR_SLUG + ".html"), "w", encoding="utf-8").write(page)
    print(f"Author page built: {AUTHOR_SLUG}.html "
          f"({n_ed} editions, {lr['resolved'] if lr else 0} scored forecasts)")
    return {"slug": AUTHOR_SLUG, "url": url}


def build_signals_page(insights):
    """Standalone, server-rendered "All signals" page.

    The homepage's #signals section renders every insight from window.INSIGHTS
    in client-side JS, so a crawler that doesn't run JS -- or a search landing
    on "Zanzibar park fee levy" -- sees a masthead, not an answer. Same
    diagnosis as build_trackers.py, same fix: a real URL with the whole feed
    already present in the HTML source, filterable client-side on top of that.
    """
    SEGSHORT = {"city": "City", "bush": "Bush", "beach": "Beach"}

    def imp_chip(it):
        imp = it.get("impact")
        if not imp:
            return ""
        n = it.get("intensity") or 2
        cls = it.get("impactClass") or "watch"
        dots = "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(3))
        src = "editor-set" if it.get("impactSet") == "author" else "auto-derived"
        title = f"Impact ({src}): {imp} · intensity {n}/3"
        return (f'<span class="imp imp-{html.escape(cls)}" title="{html.escape(title)}">'
                f'{html.escape(imp)}<span class="dots">{dots}</span></span>')

    def card(it):
        segs = it.get("segments") or []
        seg_class = " ".join(segs)
        seg_label = "/".join(SEGSHORT.get(s, s) for s in segs)
        headline = md_inline(html.escape(it["headline"]))
        body = it.get("body", "")
        body_html = ""
        if body:
            trimmed = body[:220] + ("…" if len(body) > 220 else "")
            body_html = f"<p>{md_inline(html.escape(trimmed))}</p>"
        sw = it.get("sowhat")
        sw_html = f'<div class="isw">{md_inline(html.escape(sw))}</div>' if sw else ""
        # The edition label ("Morning Brief") sat directly under the impact chip
        # and overlapped it on typical card widths. The date is already shown,
        # so drop the edition from the visible line — it stays searchable via
        # data-q below. The chip itself was absolutely positioned top-right and
        # still overlapped the meta line on some widths, so it now sits inline
        # in the meta line, beside confidence, instead of floating over the card.
        meta = [f'<span>{html.escape(it["dateDisplay"])}</span>']
        if seg_label:
            meta.append(f'<span>· {html.escape(seg_label)}</span>')
        if it.get("countries"):
            meta.append(f'<span>· {html.escape(it["countries"])}</span>')
        if it.get("confidence"):
            meta.append(f'<span class="conf">· {html.escape(it["confidence"])}</span>')
        imp = imp_chip(it)
        if imp:
            meta.append(f'<span>· {imp}</span>')
        search_blob = html.escape(" ".join([
            it["headline"], body, sw or "", it.get("countries") or "",
            it.get("edition") or "", seg_label, it.get("confidence") or ""
        ]).lower())
        return (f'<a class="insight {html.escape(seg_class)}" data-seg="{html.escape(seg_class)}" '
                f'data-q="{search_blob}" href="editions/{it["source"]}.html">'
                f'<div class="imeta">{"".join(meta)}</div>'
                f'<h3>{headline}</h3>{body_html}{sw_html}'
                f'<span class="open">Open full edition →</span></a>')

    cards_html = "\n".join(card(it) for it in insights)
    n = len(insights)
    updated = datetime.date.today().isoformat()

    title = "All signals — every dated hospitality signal | EA Hospitality Pulse"
    desc = (f"Every dated, sourced signal from EA Hospitality Pulse editions — {n} and counting — "
            "searchable and filterable by city, bush or beach segment, with impact and confidence "
            "on every line.")
    url = BASE + "/signals.html"

    ld_collection = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": url + "#page", "url": url, "name": "All signals",
        "description": desc, "isPartOf": {"@id": SITE_ID},
        "about": {"@id": ORG_ID}, "inLanguage": "en",
        "dateModified": updated,
        "mainEntity": {"@type": "ItemList", "name": "EA Hospitality Pulse signals",
                        "numberOfItems": n},
    }
    ld = f'<script type="application/ld+json">{json.dumps(ld_collection)}</script>'

    style = """
  :root{
    --sand:#0a0f1a; --sand-2:#141f33; --ink:#e8edf5; --muted:#93a0b6;
    --gold:#e2a93d; --gold-d:#caa14a; --teal:#17a495; --teal-d:#0f6d63;
    --city:#5b8fd6; --bush:#a8c258; --beach:#33c2d4; --line:#233047;
    --card:#0f1826; --coral:#ff6b4a; --sage:#57c08a; --amber:#e6b800;
    --sans:'Helvetica Neue',Arial,sans-serif;
    --mono:ui-monospace,'SF Mono','Roboto Mono',Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:Georgia,Cambria,serif;color:var(--ink);background:var(--sand);line-height:1.6}
  a{color:#43bcae}
  .wrap{max-width:1060px;margin:0 auto;padding:0 22px}
  header.site{background:linear-gradient(135deg,#0b1526,#101f37);border-bottom:1px solid var(--line);padding:8px 0}
  .topbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
  .brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit}
  .logo{width:42px;height:42px;border-radius:9px;background:var(--gold);display:grid;place-items:center;font-size:22px;color:#1a1206;font-weight:800;box-shadow:0 2px 8px rgba(0,0,0,.25)}
  .brand h1{font-size:20px;margin:0;letter-spacing:.2px;color:#fff}
  .brand p{margin:0;font-family:var(--sans);font-size:12.5px;color:#c7d0e0}
  nav.top a{color:#fff;font-family:var(--sans);font-size:14px;margin-left:18px;opacity:.9;text-decoration:none}
  nav.top a:hover{opacity:1;border-bottom:2px solid var(--gold)}
  main.wrap{padding:28px 22px 40px}
  .crumbs{font-family:var(--sans);font-size:13px;color:var(--muted);margin:0 0 14px}
  .crumbs a{color:var(--muted)}
  .section-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:6px}
  .kicker{font-family:var(--sans);text-transform:uppercase;letter-spacing:2px;font-size:12px;color:var(--gold-d);font-weight:700}
  h1.pg{font-size:clamp(26px,4vw,40px);margin:6px 0 10px;line-height:1.15}
  .lede{color:var(--muted);font-family:var(--sans);font-size:14.5px;margin:0 0 16px;max-width:64ch}
  .sigtabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
  .sigtab{font-family:var(--sans);font-size:13.5px;font-weight:700;padding:9px 16px;border-radius:22px;border:1px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer;text-decoration:none;transition:all .12s}
  .sigtab.active{background:var(--gold);color:#1a1206;border-color:var(--gold)}
  .controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
  .controls input{flex:1;min-width:200px;font-family:var(--sans);font-size:14px;padding:11px 14px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
  .controls input::placeholder{color:var(--muted)}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
  .insight{position:relative;display:block;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:18px 20px;text-decoration:none;color:inherit;transition:transform .12s,box-shadow .12s}
  .insight:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.35)}
  .insight.city{border-left-color:var(--city)}
  .insight.bush{border-left-color:var(--bush)}
  .insight.beach{border-left-color:var(--beach)}
  .insight .imeta{font-family:var(--sans);font-size:12px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
  .insight .imeta .conf{font-weight:700;color:var(--gold-d)}
  .insight h3{margin:2px 0 8px;font-size:17px;line-height:1.3;color:var(--ink)}
  .insight p{font-family:var(--sans);font-size:14px;color:var(--muted);margin:0 0 6px}
  .insight .isw{font-family:var(--sans);font-size:14px;background:var(--sand-2);padding:8px 12px;border-radius:6px;margin:8px 0 4px}
  .insight .open{font-family:var(--sans);font-size:13px;font-weight:600;color:var(--teal);margin-top:10px;display:inline-block}
  .imp{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:11px;font-weight:800;letter-spacing:.3px;vertical-align:middle}
  .imp-demand{color:var(--sage)} .imp-margin{color:var(--coral)} .imp-risk{color:#ff5b5b} .imp-watch{color:var(--amber)}
  .imp .dots{display:inline-flex;gap:3px}
  .imp .dots i{width:5px;height:5px;border-radius:50%;background:currentColor;opacity:.25}
  .imp .dots i.on{opacity:1}
  .empty{color:var(--muted);font-style:italic;padding:20px 0;display:none;font-family:var(--sans)}
  .loadmore-row{display:flex;flex-direction:column;align-items:center;gap:8px;margin:26px 0 6px}
  .count-note{font-family:var(--sans);font-size:13px;color:var(--muted)}
  .btn-load{font-family:var(--sans);font-weight:600;font-size:15px;padding:12px 20px;border-radius:8px;border:none;background:var(--teal-d);color:#fff;cursor:pointer}
  footer.site{padding:28px 0;text-align:center;color:var(--muted);font-family:var(--sans);font-size:13px}
  .foot-links{margin-top:10px;font-size:12.5px}
  .foot-links a{margin:0 2px;color:var(--muted)}
"""

    js = """
(function(){
  var all = Array.prototype.slice.call(document.querySelectorAll('.insight'));
  var PAGE = 30, shown = PAGE;
  var seg = 'all', q = '';
  var params = new URLSearchParams(location.search);
  if (params.get('seg')) seg = params.get('seg');
  var tabs = document.querySelectorAll('.sigtab');
  tabs.forEach(function(t){
    if (t.dataset.seg === seg) t.classList.add('active'); else t.classList.remove('active');
  });
  var search = document.getElementById('search');
  var empty = document.getElementById('empty');
  var loadmore = document.getElementById('loadmore');
  var count = document.getElementById('count');
  function matches(el){
    if (seg !== 'all' && el.dataset.seg.indexOf(seg) === -1) return false;
    if (q && el.dataset.q.indexOf(q) === -1) return false;
    return true;
  }
  function render(){
    var vis = all.filter(matches);
    all.forEach(function(el){ el.style.display = 'none'; });
    vis.forEach(function(el, i){ if (i < shown) el.style.display = ''; });
    empty.style.display = vis.length ? 'none' : 'block';
    loadmore.style.display = vis.length > shown ? '' : 'none';
    count.textContent = vis.length ? ('Showing ' + Math.min(shown, vis.length) + ' of ' + vis.length) : '';
  }
  tabs.forEach(function(t){
    t.addEventListener('click', function(ev){
      ev.preventDefault();
      seg = t.dataset.seg; shown = PAGE;
      tabs.forEach(function(x){ x.classList.toggle('active', x === t); });
      var u = new URL(location.href);
      if (seg === 'all') u.searchParams.delete('seg'); else u.searchParams.set('seg', seg);
      history.replaceState(null, '', u);
      render();
    });
  });
  if (search) search.addEventListener('input', function(){
    q = search.value.trim().toLowerCase(); shown = PAGE; render();
  });
  if (loadmore) loadmore.addEventListener('click', function(){ shown += PAGE; render(); });
  render();
})();
"""

    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="{AUTHOR_BYLINE}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#0a0f1a">
<meta name="color-scheme" content="dark">
<link rel="alternate" type="application/rss+xml" title="EA Hospitality Pulse" href="feed.xml">
<meta property="og:type" content="website">
<meta property="og:site_name" content="EA Hospitality Pulse">
<meta property="og:title" content="All signals — EA Hospitality Pulse">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og/default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="EA Hospitality Pulse — all signals">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="All signals — EA Hospitality Pulse">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{BASE}/og/default.png">
<link rel="icon" href="favicon.png"><link rel="apple-touch-icon" href="apple-touch-icon.png">
{ld}
<style>{style}</style></head>
<body>
<header class="site"><div class="wrap topbar">
  <a class="brand" href="index.html"><div class="logo" aria-hidden="true">EA</div>
    <div><h1>EA Hospitality Pulse</h1><p>Daily intelligence for city, bush &amp; beach properties</p></div></a>
  <nav class="top">
    <a href="index.html">Home</a>
    <a href="start-here.html">New Here? Start Here</a>
    <a href="about/onyango-george.html">Editor</a>
    <a href="trackers/index.html">Trackers</a>
    <a href="signals.html">Signals</a>
    <a href="archive.html">Archive</a>
  </nav>
</div></header>
<main class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">Home</a> <span aria-hidden="true">/</span> <span aria-current="page">All signals</span></nav>
  <div class="section-head"><div><div class="kicker">Live signal feed</div><h1 class="pg">All signals</h1></div></div>
  <p class="lede">Every dated, sourced signal from every EA Hospitality Pulse edition — {n} so far — filterable by segment, with a clear "so what" for pricing and inventory on every line.</p>
  <div class="sigtabs" id="sigtabs">
    <a class="sigtab" data-seg="all" href="signals.html">All signals</a>
    <a class="sigtab" data-seg="city" href="signals.html?seg=city">\U0001F3D9 City</a>
    <a class="sigtab" data-seg="bush" href="signals.html?seg=bush">\U0001F33F Bush</a>
    <a class="sigtab" data-seg="beach" href="signals.html?seg=beach">\U0001F3D6 Beach</a>
  </div>
  <div class="controls"><input id="search" type="text" placeholder="Search all signals..."></div>
  <div class="cards" id="cards">
{cards_html}
  </div>
  <div class="empty" id="empty">No signals match your search yet.</div>
  <div class="loadmore-row">
    <span id="count" class="count-note"></span>
    <button id="loadmore" class="btn-load" style="display:none">Load older ↓</button>
  </div>
</main>
<footer class="site"><div class="wrap">
  <p>EA Hospitality Pulse — Daily intelligence for city, bush &amp; beach properties across East Africa.<br>
  {updated} · Kenya · Uganda · Tanzania · Zanzibar · Rwanda</p>
  <p class="foot-links"><a href="archive.html">Archive</a> · <a href="trackers/index.html">Trackers</a> · <a href="methodology.html">Methodology</a> · <a href="republish.html">Republish</a> · <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms</a> · <a href="mailto:{CONTACT_EMAIL}">Contact</a></p>
</div></footer>
<script>{js}</script>
</body></html>"""

    with open(os.path.join(HERE, "signals.html"), "w", encoding="utf-8") as f:
        f.write(html_doc)
    return n



def main():
    # Static tracker pages. Every dataset on the site was an anchor section of
    # index.html rendered from JavaScript, so a searcher asking "Uganda gorilla
    # permit price" landed on a masthead and an answer engine that does not run
    # JS saw nothing at all. These give each dataset a real URL with the content
    # in the HTML source.
    try:
        import build_trackers
        trackers = build_trackers.build()
    except Exception as ex:
        print("trackers skipped:", ex)
        trackers = []

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

    # Static "All signals" page. Same rationale as the trackers: every
    # insight lived only in window.INSIGHTS, rendered client-side on the
    # homepage, invisible to a crawler that does not run JS.
    try:
        n_sig = build_signals_page(insights)
    except Exception as ex:
        print("signals page skipped:", ex)

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
        # ---- homepage snippet ------------------------------------------
        # 1,156 of 1,693 impressions in the 1 Aug - 13 Sep window landed on this
        # page, at average position 7.15, and returned ONE click (0.09% CTR).
        # Position 7 with a working snippet returns 3-4%. The cause was visible
        # in the markup: a 94-character title that opened on the brand name, so
        # the ~60 characters Google actually renders read "EA Hospitality Pulse
        # - Daily intelligence for city, bush & b..." - which matches no query
        # anyone types. The homepage ranks for long-tail fee, rate and advisory
        # questions because the trackers live in its anchor sections, so the
        # title now names those things and keeps the brand short at the end.
        _home_title = "East Africa hotel rates, park fees &amp; advisories | EA Pulse"
        _home_desc = "Free daily data for hotels, lodges and camps across Kenya, Uganda, Tanzania, Zanzibar and Rwanda: live rate index, park fees, levies and US/UK advisory levels."
        idx = re.sub(r"<title>.*?</title>", "<title>" + _home_title + "</title>",
                     idx, count=1, flags=re.S)
        idx = _sub(r'(<meta name="description" content=")[^"]*(")', _home_desc, idx)
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
        # Every edition page declares isPartOf {"@id": BASE+"/#website"}. The home
        # page's WebSite node carried no @id, so that reference resolved to nothing
        # and the site graph stayed unlinked. Give the node the id it is referenced by.
        if '"@type":"WebSite"' in idx and '#website' not in idx:
            idx = idx.replace('{"@context":"https://schema.org","@type":"WebSite",',
                              '{"@context":"https://schema.org","@type":"WebSite","@id":"' + SITE_ID + '",', 1)
        # The site has a real full-text search (archive.html reads ?q=), but the
        # WebSite node never advertised it — so an engine had no machine-readable
        # way to query the archive and no basis for a sitelinks search box.
        if '"@type":"WebSite"' in idx and 'potentialAction' not in idx:
            _search = json.dumps({
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {"@type": "EntryPoint",
                               "urlTemplate": BASE + "/archive.html?q={search_term_string}"},
                    "query-input": "required name=search_term_string"}})[1:-1]
            idx = re.sub(r'(\{"@context":"https://schema\.org","@type":"WebSite")',
                         lambda m: m.group(1) + "," + _search, idx, count=1)
        # The homepage holds 68% of the site's impressions, so it is the best
        # internal link source the trackers can have. One nav entry, injected
        # idempotently rather than hand-edited into the markup.
        if 'href="about/onyango-george.html"' not in idx:
            idx = idx.replace('<a href="start-here.html">New Here? Start Here</a>',
                              '<a href="start-here.html">New Here? Start Here</a>\n'
                              '      <a href="about/onyango-george.html">Editor</a>', 1)
        if trackers and 'href="trackers/index.html"' not in idx:
            idx = idx.replace('<a href="start-here.html">New Here? Start Here</a>',
                              '<a href="start-here.html">New Here? Start Here</a>\n'
                              '      <a href="trackers/index.html">Trackers</a>', 1)
        if '<a href="signals.html">Signals</a>' not in idx:
            idx = idx.replace('<a href="trackers/index.html">Trackers</a>',
                              '<a href="trackers/index.html">Trackers</a>\n'
                              '      <a href="signals.html">Signals</a>', 1)

        # Dataset consolidation. Each homepage Dataset node addressed itself to
        # an index.html anchor; the tracker pages now hold the same datasets at
        # a real URL. Point the homepage nodes at the canonical page and share
        # its @id so an engine resolves one dataset, not two near-duplicates.
        _DS_MAP = {
            "EA Pulse Rate Index": "hotel-rate-index",
            "EA Pulse Cost-Side Index": "cost-index",
            "EA Pulse Rules, Fees & Levies Tracker": "park-fees-and-levies",
            "EA Pulse Connectivity Tracker": "airport-traffic-and-routes",
            "EA Pulse Development Pipeline Tracker": "hotel-development-pipeline",
            "EA Pulse MICE Events Tracker": "mice-calendar",
        }
        _slugs = {t["slug"] for t in (trackers or [])}
        for _name, _slug in _DS_MAP.items():
            if _slug not in _slugs:
                continue
            _canon = f"{BASE}/trackers/{_slug}.html"
            _pat = r'(\{"@context": "https://schema\.org", "@type": "Dataset", "name": "'\
                   + re.escape(_name) + r'".*?"url": ")[^"]*(")'
            idx = re.sub(_pat, lambda m: m.group(1) + _canon + m.group(2), idx,
                         count=1, flags=re.S)
            idx = idx.replace(
                '{"@context": "https://schema.org", "@type": "Dataset", "name": "' + _name + '"',
                '{"@context": "https://schema.org", "@type": "Dataset", "@id": "'
                + _canon + '#dataset", "name": "' + _name + '"', 1)

        # Social/answer-engine parity with the edition pages: an image with no alt
        # is an image an engine cannot describe, and no locale is a locale it guesses.
        if '<meta property="og:image:alt"' not in idx:
            _alt = ('<meta property="og:image:alt" content="EA Hospitality Pulse — daily '
                    'intelligence for East African hospitality">\n'
                    '<meta name="twitter:image:alt" content="EA Hospitality Pulse — daily '
                    'intelligence for East African hospitality">\n'
                    '<meta property="og:locale" content="en_GB">\n')
            idx = idx.replace('<meta name="twitter:card"', _alt + '<meta name="twitter:card"', 1)

        # AI Overviews and large-snippet surfaces need explicit permission; the home
        # page had no robots directive at all, so it inherited the conservative default.
        if '<meta name="robots"' not in idx:
            idx = idx.replace('<link rel="canonical"',
                '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n<link rel="canonical"', 1)
        open(idx_path, "w", encoding="utf-8").write(idx)
    except Exception as e:
        print("build stamp skipped:", e)

    # ---- archive.html: give the hub page a machine-readable index -------------
    # The archive lists every edition, but it builds that list in JavaScript from
    # data.js — so a crawler or answer engine that does not execute scripts saw a
    # search box and nothing else. A CollectionPage + ItemList states the same
    # inventory in the head, where it is retrievable without a JS runtime.
    arc_path = os.path.join(HERE, "archive.html")
    try:
        arc = open(arc_path, encoding="utf-8").read()
        arc = re.sub(r"<!--ARCHIVE_LD-->.*?<!--/ARCHIVE_LD-->\n?", "", arc, flags=re.S)
        _recent = editions[:60]
        arc_ld = {
            "@context": "https://schema.org", "@type": "CollectionPage",
            "@id": BASE + "/archive.html", "url": BASE + "/archive.html",
            "name": "EA Hospitality Pulse archive",
            "description": ("Every EA Hospitality Pulse edition — daily briefs, Sunday "
                            "Foresight essays and shock playbooks for hotels, lodges, camps "
                            "and resorts in Kenya, Uganda, Tanzania, Zanzibar and Rwanda."),
            "inLanguage": "en", "isPartOf": {"@id": SITE_ID},
            "publisher": {"@id": ORG_ID},
            "about": ABOUT_ENTITIES,
            "mainEntity": {
                "@type": "ItemList",
                "name": "EA Hospitality Pulse editions",
                "numberOfItems": len(editions),
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1,
                     "url": f"{BASE}/editions/{e2['id']}.html",
                     "name": f"{e2['edition']} — {e2['dateDisplay']}"}
                    for i, e2 in enumerate(_recent)],
            },
        }
        arc_crumbs = {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Archive",
                 "item": BASE + "/archive.html"},
            ]}
        _inject = ("<!--ARCHIVE_LD-->\n"
                   '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n'
                   '<meta property="og:image:alt" content="EA Hospitality Pulse archive">\n'
                   '<meta name="twitter:card" content="summary_large_image">\n'
                   '<meta name="twitter:title" content="Archive — every EA Hospitality Pulse edition">\n'
                   '<meta name="twitter:description" content="Filter every brief by country, segment and topic.">\n'
                   f'<meta name="twitter:image" content="{BASE}/og/default.png">\n'
                   '<meta name="twitter:image:alt" content="EA Hospitality Pulse archive">\n'
                   '<meta property="og:locale" content="en_GB">\n'
                   f'<script type="application/ld+json">{json.dumps(arc_ld)}</script>\n'
                   f'<script type="application/ld+json">{json.dumps(arc_crumbs)}</script>\n'
                   "<!--/ARCHIVE_LD-->\n")
        # Drop any pre-existing duplicates of the tags we now own, then inject.
        for _dup in ('<meta name="robots"', '<meta property="og:locale"'):
            arc = re.sub(r"^" + re.escape(_dup) + r'[^>]*>\n', "", arc, flags=re.M)
        arc = arc.replace("</head>", _inject + "</head>", 1)
        open(arc_path, "w", encoding="utf-8").write(arc)
        print(f"archive.html: structured index written ({len(_recent)} of {len(editions)} editions)")
    except Exception as e:
        print("archive structured data skipped:", e)

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
    author_page = build_author_page(editions, guides, trackers)
    build_credits_page()
    polish_static_heads()

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
    # The home page and the archive genuinely change every build (a new edition
    # lands in both); everything else states the date it actually last changed.
    _STATIC = [("index.html", "daily"), ("archive.html", "daily"),
               ("signals.html", "daily"),
               ("republish.html", "monthly"), ("methodology.html", "monthly"),
               ("faq.html", "monthly"), ("start-here.html", "monthly"),
               ("survey.html", "monthly"), ("survey-pay.html", "monthly"),
               ("survey-agents.html", "monthly"), ("credits.html", "monthly"),
               ("api.html", "monthly"), ("privacy.html", "yearly"),
               ("terms.html", "yearly")]
    urls = []
    for _rel, _cf in _STATIC:
        _loc = BASE + "/" if _rel == "index.html" else f"{BASE}/{_rel}"
        _lm = today if _cf == "daily" else file_lastmod(_rel, today)
        urls.append((_loc, _lm, _cf))
    for g in guides:
        urls.append((f"{BASE}/guides/{g['slug']}.html", g["updated"], "monthly"))
    if author_page:
        urls.append((f"{BASE}/{AUTHOR_SLUG}.html", today, "monthly"))
    if trackers:
        # A tracker changes when its data changes, which is what lastmod is for.
        urls.append((f"{BASE}/trackers/index.html", today, "daily"))
        for tr in trackers:
            urls.append((f"{BASE}/trackers/{tr['slug']}.html", tr["updated"], "weekly"))
    tools_dir = os.path.join(HERE, "tools")
    if os.path.isdir(tools_dir):
        for t in sorted(os.listdir(tools_dir)):
            if t.endswith(".html"):
                urls.append((f"{BASE}/tools/{t}",
                             file_lastmod(os.path.join("tools", t), today), "monthly"))
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

    # llms.txt is the file answer engines fetch to orient themselves. It was
    # hand-written and static, so it pointed at the archive but never at an actual
    # edition — an engine had to crawl to find anything datable. Regenerate one
    # marked block with the ten most recent editions, leaving the prose untouched.
    _llms_path = os.path.join(HERE, "llms.txt")
    try:
        _llms = open(_llms_path, encoding="utf-8").read()
        _recent = "\n".join(
            f"- [{e['edition']} — {e['dateDisplay']}]({BASE}/editions/{e['id']}.html): "
            f"{md_strip(clean_headline(e['summary']) or e['edition'])[:150]}"
            for e in editions[:10])
        _tr = "\n".join(
            f"- [{tr['nav']}]({BASE}/trackers/{tr['slug']}.html): {tr['records']} records, "
            f"last updated {tr['updated']}"
            for tr in (trackers or []))
        _auth = (f"\n\n## Author\n- [{AUTHOR_BYLINE}]({BASE}/{AUTHOR_SLUG}.html): "
                 f"editor and author of every edition; consultant and analyst covering "
                 f"hospitality in Kenya, Uganda, Tanzania, Zanzibar and Rwanda. "
                 f"Contact {CONTACT_EMAIL}.")
        _block = ("<!--AUTO:RECENT-->\n## Ten most recent editions (auto-updated "
                  + today + ")\n" + _recent
                  + (("\n\n## Dataset freshness (auto-updated " + today + ")\n" + _tr) if _tr else "")
                  + _auth + "\n<!--/AUTO:RECENT-->")
        if "<!--AUTO:RECENT-->" in _llms:
            _llms = re.sub(r"<!--AUTO:RECENT-->.*?<!--/AUTO:RECENT-->", lambda m: _block,
                           _llms, flags=re.S)
        else:
            _llms = _llms.replace("## Contact", _block + "\n\n## Contact", 1)
        open(_llms_path, "w", encoding="utf-8").write(_llms)
    except Exception as _ex:
        print("llms.txt refresh skipped:", _ex)

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
