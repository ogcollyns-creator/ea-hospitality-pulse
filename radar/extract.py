#!/usr/bin/env python3
"""Content extractors: feeds, sitemaps, HTML and PDF. Stdlib only.

Deliberately tolerant. These parsers run against government sites that emit
malformed XML, mislabelled charsets and HTML written in 2009. A parser that
raises on the fifth malformed gazette page is a parser that never runs in
production, so every function degrades to a partial result rather than failing.
"""
import re, zlib, html as htmllib, hashlib
from urllib.parse import urljoin, urldefrag, urlparse
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

# ---------------------------------------------------------------- helpers

def sha1(s):
    return hashlib.sha1(s.encode("utf-8", "replace") if isinstance(s, str) else s).hexdigest()


def decode(raw, ctype=""):
    m = re.search(r"charset=([\w\-]+)", ctype or "", re.I)
    for enc in ([m.group(1)] if m else []) + ["utf-8", "cp1252", "latin-1"]:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def canon(url):
    """Canonicalise for identity purposes: drop fragment, trailing slash, and the
    tracking parameters that make the same page look new on every fetch."""
    url, _ = urldefrag(url or "")
    url = re.sub(r"([?&])(utm_[^=]*|fbclid|gclid|mc_cid|mc_eid|_ga)=[^&]*", r"\1", url)
    url = re.sub(r"[?&]+$", "", url).replace("?&", "?")
    return url.rstrip("/") or url


def parse_date(s):
    """Best-effort date → epoch seconds. Returns None rather than guessing."""
    if not s:
        return None
    s = s.strip()
    try:
        return int(parsedate_to_datetime(s).timestamp())
    except Exception:
        pass
    t = s.replace("Z", "+00:00")
    for cut in (len(t), 25, 19, 10):
        try:
            d = datetime.fromisoformat(t[:cut])
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return int(d.timestamp())
        except Exception:
            continue
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return int(datetime.strptime(s[:20].strip(), fmt).replace(tzinfo=timezone.utc).timestamp())
        except Exception:
            continue
    return None


_TAG = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"(?is)<(script|style|noscript|svg)\b.*?</\1>")
_NAV = re.compile(r"(?is)<(nav|header|footer|form)\b.*?</\1>")


def html_to_text(h, strip_chrome=True):
    h = _SCRIPT.sub(" ", h)
    if strip_chrome:
        h = _NAV.sub(" ", h)
    txt = htmllib.unescape(_TAG.sub(" ", h))
    return re.sub(r"\s+", " ", txt).strip()


# ---------------------------------------------------------------- feeds

def discover_feed(h, base):
    """<link rel=alternate type=...rss/atom...> — the cheapest possible upgrade."""
    for m in re.finditer(r"(?is)<link\b([^>]+)>", h):
        attrs = m.group(1)
        if not re.search(r'type\s*=\s*["\']?application/(rss|atom)\+xml', attrs, re.I):
            continue
        href = re.search(r'href\s*=\s*["\']([^"\']+)', attrs, re.I)
        if href:
            return urljoin(base, htmllib.unescape(href.group(1)))
    for guess in ("/feed/", "/rss.xml", "/feed.xml", "/atom.xml", "/index.xml"):
        if guess.strip("/") in h.lower():
            return urljoin(base, guess)
    return None


def _txt(el):
    return (el.text or "").strip() if el is not None else ""


def parse_feed(raw):
    """RSS 2.0 / RDF / Atom → [{url,title,summary,published_ts}]."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        # Malformed feeds are common. Strip the prolog and retry once.
        try:
            root = ET.fromstring(re.sub(rb"^[^<]+", b"", raw))
        except ET.ParseError:
            return []
    ns = {"a": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = _txt(it.find("title")) or _txt(it.find("a:title", ns))
        link = _txt(it.find("link")) or _txt(it.find("guid"))
        if not link:
            le = it.find("a:link", ns)
            if le is not None:
                link = le.get("href", "")
        date = (_txt(it.find("pubDate")) or _txt(it.find("a:published", ns))
                or _txt(it.find("a:updated", ns)) or _txt(it.find("dc:date", ns))
                or _txt(it.find("updated")) or _txt(it.find("date")))
        summ = (_txt(it.find("description")) or _txt(it.find("a:summary", ns))
                or _txt(it.find("a:content", ns)))
        if link or title:
            out.append({"url": link.strip(), "title": html_to_text(title)[:400],
                        "summary": html_to_text(summ)[:1000],
                        "published_ts": parse_date(date)})
    return out


def parse_sitemap(raw):
    """Returns (child_sitemaps, [(loc, lastmod_ts)])."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return [], []
    kids, urls = [], []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "sitemap":
            loc = _txt(el.find("{*}loc")) or _txt(next((c for c in el if c.tag.endswith("loc")), None))
            if loc:
                kids.append(loc.strip())
        elif tag == "url":
            loc = lastmod = ""
            for c in el:
                t = c.tag.split("}")[-1]
                if t == "loc":
                    loc = (c.text or "").strip()
                elif t == "lastmod":
                    lastmod = (c.text or "").strip()
            if loc:
                urls.append((loc, parse_date(lastmod)))
    return kids, urls


# ---------------------------------------------------------------- HTML items

_BAD_ANCHOR = re.compile(
    r"(?i)^(home|about|contact|menu|search|login|sign in|read more|more|next|previous|"
    r"back|share|tweet|facebook|linkedin|whatsapp|privacy|terms|cookies?|subscribe|"
    r"newsletter|download|click here|skip to content|all rights reserved)\b")
_ASSET = re.compile(r"(?i)\.(jpg|jpeg|png|gif|webp|svg|ico|css|js|woff2?|ttf|mp4|zip)($|\?)")


def extract_items(h, base, min_len=28):
    """Headline-shaped anchors from an index page.

    Most upstream sources are HTML index pages with no feed: a gazette listing, a
    press-release table, a regulator's notices column. Their anchors *are* the
    items. Filtering on anchor-text length plus a chrome blacklist gets the real
    headlines out with no per-site adapter — which is what makes 137 sources
    maintainable by one person."""
    host = urlparse(base).netloc.lower()
    seen, out = set(), []
    body = _NAV.sub(" ", _SCRIPT.sub(" ", h))
    for m in re.finditer(r'(?is)<a\b[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', body):
        href, inner = m.group(1), m.group(2)
        text = html_to_text(inner, strip_chrome=False)
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = canon(urljoin(base, htmllib.unescape(href)))
        if not url.startswith("http") or _ASSET.search(url):
            continue
        is_doc = url.lower().split("?")[0].endswith((".pdf", ".doc", ".docx", ".xlsx"))
        # Off-domain links are almost always chrome, unless they are documents.
        if urlparse(url).netloc.lower() != host and not is_doc:
            continue
        if len(text) < min_len and not is_doc:
            continue
        if _BAD_ANCHOR.match(text):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append({"url": url, "title": text[:400], "summary": "",
                    "published_ts": None, "is_doc": is_doc})
    return out


# ---------------------------------------------------------------- PDF

_PDF_TEXT = re.compile(rb"\((?:\\.|[^\\()])*\)")


def pdf_text(raw, max_streams=250):
    """Crude but dependency-free PDF text extraction.

    Good enough for what this pipeline needs: change detection, date discovery
    and keyword scanning on ministry advisories and situation reports. It is not
    a layout-faithful extractor and is not trying to be — if a document matters
    enough to quote precisely, a human opens the PDF."""
    chunks = []
    for i, m in enumerate(re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S)):
        if i >= max_streams:
            break
        blob = m.group(1)
        for candidate in (blob, blob.strip()):
            try:
                blob = zlib.decompress(candidate)
                break
            except zlib.error:
                continue
        if b"Tj" not in blob and b"TJ" not in blob:
            continue
        parts = []
        for t in _PDF_TEXT.findall(blob):
            s = t[1:-1]
            s = re.sub(rb"\\([()\\])", rb"\1", s)
            s = re.sub(rb"\\[0-9]{1,3}", b" ", s)
            try:
                parts.append(s.decode("utf-8"))
            except UnicodeDecodeError:
                parts.append(s.decode("latin-1", "replace"))
        if parts:
            chunks.append("".join(parts))
    txt = re.sub(r"\s+", " ", " ".join(chunks)).strip()
    return txt


def first_date_in(text, limit=4000):
    """Find a plausible publication date in page text. Used only to *corroborate*
    first_seen — never to override it."""
    win = text[:limit]
    # Trailing boundary is (?!\d) not \b: extracted PDF text routinely runs the
    # year straight into the next word ("...28 July 2026Screening at..."), where
    # \b does not match and the date is silently lost.
    MON = ("January|February|March|April|May|June|July|August|September|"
           "October|November|December")
    pats = [rf"\b(\d{{1,2}}\s+(?:{MON})\s+20\d{{2}})(?!\d)",
            rf"\b((?:{MON})\s+\d{{1,2}},?\s+20\d{{2}})(?!\d)",
            r"\b(20\d{2}-\d{2}-\d{2})(?!\d)",
            r"\b(\d{1,2}/\d{1,2}/20\d{2})(?!\d)"]
    for p in pats:
        m = re.search(p, win, re.I)
        if m:
            ts = parse_date(m.group(1))
            if ts:
                return ts
    return None
