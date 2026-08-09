#!/usr/bin/env python3
"""
Build search-index.json — the data behind the searchable archive.

Parses every edition and guide source, extracts facets (country, segment,
topic, confidence) and a searchable text body, and emits a single JSON file
the archive page loads once and filters entirely client-side. No backend,
no search service, no PII.

The tag format has changed across the archive's life. Three variants are
handled, and where a tag line carries no facets we fall back to scanning the
edition body — an edition that never names a country is genuinely uncountried
rather than silently dropped.

Run:  python3 build_search_index.py
"""
import os, re, json, glob, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "site_config.json")))

FLAG2CC = {"\U0001F1F0\U0001F1EA": "KE", "\U0001F1FA\U0001F1EC": "UG",
           "\U0001F1F9\U0001F1FF": "TZ", "\U0001F1F7\U0001F1FC": "RW"}
CC_NAME = {"KE": "Kenya", "UG": "Uganda", "TZ": "Tanzania",
           "RW": "Rwanda", "ZNZ": "Zanzibar"}
SEGS = ["Bush", "City", "Beach", "Trade"]

TOPICS = {
    "Advisories":    r"advisor|travel warning|level \d|do not travel|reconsider travel",
    "Health":        r"ebola|outbreak|mpox|cholera|marburg|who afro|africa cdc|quarantine|port health",
    "Aviation":      r"airline|route|flight|aircraft|airport|seat|capacity|kq |rwandair|uganda airlines|emirates|qatar|turkish",
    "Rates":         r"rate index|adr |rack rate|room rate|pricing|discount|repric",
    "Costs":         r"fuel|diesel|petrol|epra|inflation|exchange rate|electricity|tariff|levy|cost",
    "Regulation":    r"gazette|regulation|licen|permit|tax|vat|levy|fee increase|park fee|visa",
    "Development":   r"pipeline|opening|signing|new hotel|construction|refurb|rebuild|keys|rooms under",
    "MICE":          r"conference|mice|exhibition|summit|convention|delegate|fhs|magical kenya|expo",
    "Distribution":  r"ota|booking\.com|expedia|commission|channel manager|direct booking|gds",
    "Security":      r"protest|unrest|attack|kidnap|security|curfew|election|demonstration",
    "Conservation":  r"conservanc|wildlife|poach|gorilla|migration|park|reserve|kws|uwa",
    "Sustainability": r"sustainab|plastic|carbon|green globe|earthcheck|travelife|certif",
}

def facets_from_tagline(line):
    """Parse one tag line into (segments, countries, confidence)."""
    segs, ccs, conf = set(), set(), None
    body = line.replace("\U0001F3F7", "").strip()
    for flag, cc in FLAG2CC.items():
        if flag in body:
            ccs.add(cc)
    parts = [p.strip() for p in body.split("|")]
    for p in parts:
        if re.search(r"\ball segments?\b", p, re.I):
            segs.update(SEGS)
        for s in SEGS:
            if re.search(r"\b" + s + r"\b", p, re.I):
                segs.add(s)
        # bare country codes, but only in a short facet cell — avoids matching
        # "KE" inside a source name or prose
        if len(p) <= 30:
            for cc in list(CC_NAME) + ["ZNZ"]:
                if re.search(r"\b" + cc + r"\b", p):
                    ccs.add(cc)
        if re.fullmatch(r"(confirmed|reported|early signal|early)", p.strip(), re.I):
            conf = p.strip().title()
    return segs, ccs, conf

def scan_body(text):
    """Fallback facets from the edition body."""
    ccs = set()
    for flag, cc in FLAG2CC.items():
        if flag in text:
            ccs.add(cc)
    for cc, name in CC_NAME.items():
        if re.search(r"\b" + name + r"\b", text, re.I):
            ccs.add(cc)
    if re.search(r"\bzanzibar\b", text, re.I):
        ccs.add("ZNZ")
    segs = {s for s in SEGS if re.search(r"\b" + s + r"\b", text, re.I)}
    return segs, ccs

def topics_for(text):
    t = text.lower()
    return sorted([name for name, pat in TOPICS.items() if re.search(pat, t)])

def title_of(text, fallback):
    """Pull a human headline out of an edition.

    Editions lead with an italic standfirst line, which is the best title we
    have. Markdown emphasis must be stripped or it leaks asterisks into the UI.
    """
    def tidy(x):
        x = re.sub(r"^[\s*_]+|[\s*_]+$", "", x).strip()
        x = re.sub(r"\s+", " ", x)
        return x

    m = re.search(r"^\s*\*(?!\*)(.+?)\*\s*$", text, re.M)
    if m:
        c = tidy(m.group(1))
        if 20 < len(c) < 200:
            return c
    m = re.search(r"\*\*THE THEME:?(.*?)\*\*", text, re.S)
    if m:
        c = tidy(m.group(1))
        if 10 < len(c) < 200:
            return c.title()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("**") and line.endswith("**"):
            c = tidy(line)
            if 20 < len(c) < 200 and not c.isupper():
                return c
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("**") and line.endswith("**"):
            c = tidy(line)
            if 20 < len(c) < 200:
                return c.capitalize()
    return fallback

def clean(text):
    t = re.sub(r"^## (TELEGRAM|LINKEDIN|WHATSAPP).*$", " ", text, flags=re.M)
    t = re.sub(r"[─-╿]+", " ", t)
    t = re.sub(r"[*_`#>]", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

records = []

for path in sorted(glob.glob(os.path.join(HERE, "editions-src", "*.md"))):
    slug = os.path.basename(path)[:-3]
    html = os.path.join(HERE, "editions", slug + ".html")
    if not os.path.exists(html):
        continue
    raw = open(path, encoding="utf-8").read()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", slug)
    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
    if slug.startswith("foresight"): kind = "Sunday Foresight"
    elif slug.startswith("playbook"): kind = "Playbook"
    else: kind = "Daily brief"
    slot = ""
    for s in ("morning", "midday", "evening"):
        if s in slug: slot = s.title()

    segs, ccs, confs = set(), set(), set()
    for line in raw.splitlines():
        if "\U0001F3F7" in line:
            s, c, cf = facets_from_tagline(line)
            segs |= s; ccs |= c
            if cf: confs.add(cf)
    if not ccs or not segs:
        bs, bc = scan_body(raw)
        if not ccs: ccs = bc
        if not segs: segs = bs

    body = clean(raw)
    records.append({
        "slug": slug,
        "url": f"editions/{slug}.html",
        "date": date,
        "kind": kind,
        "slot": slot,
        "title": title_of(raw, f"{kind}{' — ' + slot if slot else ''} — {date}"),
        "countries": sorted(ccs),
        "segments": sorted(segs),
        "topics": topics_for(body),
        "confidence": sorted(confs),
        "words": len(body.split()),
        "text": body[:4000],
    })

for path in sorted(glob.glob(os.path.join(HERE, "guides-src", "*.md"))):
    slug = os.path.basename(path)[:-3]
    html = os.path.join(HERE, "guides", slug + ".html")
    if not os.path.exists(html):
        continue
    raw = open(path, encoding="utf-8").read()
    body = clean(raw)
    segs, ccs = scan_body(raw)
    m = re.search(r"^#\s+(.+)$", raw, re.M)
    records.append({
        "slug": slug,
        "url": f"guides/{slug}.html",
        "date": "",
        "kind": "Guide",
        "slot": "",
        "title": (m.group(1).strip() if m else slug.replace("-", " ").title()),
        "countries": sorted(ccs),
        "segments": sorted(segs),
        "topics": topics_for(body),
        "confidence": [],
        "words": len(body.split()),
        "text": body[:4000],
    })

records.sort(key=lambda r: (r["date"] or "0000", r["slug"]), reverse=True)

facet_counts = {"countries": {}, "segments": {}, "topics": {}, "kind": {}}
for r in records:
    for c in r["countries"]: facet_counts["countries"][c] = facet_counts["countries"].get(c, 0) + 1
    for s in r["segments"]:  facet_counts["segments"][s] = facet_counts["segments"].get(s, 0) + 1
    for t in r["topics"]:    facet_counts["topics"][t] = facet_counts["topics"].get(t, 0) + 1
    facet_counts["kind"][r["kind"]] = facet_counts["kind"].get(r["kind"], 0) + 1

out = {
    "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "count": len(records),
    "countryNames": CC_NAME,
    "facets": facet_counts,
    "records": records,
}
with open(os.path.join(HERE, "search-index.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

print(f"search-index.json — {len(records)} records, {os.path.getsize(os.path.join(HERE,'search-index.json')):,} bytes")
print("  countries:", facet_counts["countries"])
print("  segments: ", facet_counts["segments"])
print("  kinds:    ", facet_counts["kind"])
print("  topics:   ", dict(sorted(facet_counts["topics"].items(), key=lambda x: -x[1])))
nc = [r["slug"] for r in records if not r["countries"]]
print("  records with no country facet:", len(nc), nc[:5])
