#!/usr/bin/env python3
"""
Licence-aware image DISCOVERY across several sources, with verification.

Why this module exists
----------------------
`fetch_edition_images.py` searches Wikimedia Commons only. Commons search is
literal and its East African coverage is thin, which is why editions fall back
to generic photos. This widens discovery to Openverse and Google Programmable
Search while keeping the licence guarantee that `docs/image-policy.md` requires.

The rule that makes Google safe to use
--------------------------------------
The image policy bars "anything off Google Images WITHOUT tracing it to a
licence". That is exactly what this module does: Google is a *discovery* layer
only. It never supplies a licence. Every Google candidate must be resolved back
to an authoritative licence source (Wikimedia Commons, Openverse, Flickr) and
confirmed there before it is publishable. Anything that cannot be confirmed is
quarantined, not published.

Concretely:
  * Google CSE is always called with the `rights` parameter set, so the result
    set is pre-filtered to Creative Commons / public-domain material.
  * That filter is treated as a HINT, never as proof. Google infers licence
    metadata from page markup and gets it wrong often enough that publishing on
    its say-so would be reckless.
  * `verify()` re-checks each candidate against the issuing platform's own API.
    Only a licence string returned by that API is trusted.

Sources
-------
  wikimedia  — Commons API. Licence is authoritative.
  openverse  — Openverse API, filtered to commercial-safe licences. Authoritative.
  google     — Google Programmable Search JSON API. Discovery only; must verify.

Credentials
-----------
Google needs two values, read from the environment and never committed:
    GOOGLE_CSE_KEY   API key            (console.cloud.google.com)
    GOOGLE_CSE_CX    Search engine ID   (programmablesearchengine.google.com,
                                         with "Search the entire web" + Image
                                         search both switched on)
If either is absent, the Google source is skipped silently and the other
sources still run. Add them as GitHub Actions repository secrets; the free CSE
tier allows 100 queries/day, which is ample for one edition per slot.

Usage
-----
    from image_sources import discover, verify, ALLOWED_LICENCES

    cands = discover("Maasai Mara wildebeest crossing", per_source=6)
    good, quarantined = verify(cands)

Standalone smoke test:
    python3 image_sources.py "Diani beach Kenya"
"""
import os, json, re, sys, time, urllib.parse, urllib.request

UA = ("EAHospitalityPulse-image-fetch/2.0 "
      "(https://eahospitalitypulse.com; ceo@eahospitalitypulse.com)")

# ---------------------------------------------------------------- licences
# Commercial-safe only. The Pulse is a commercial product and we crop/overlay
# branding, so NC (non-commercial) and ND (no-derivatives) are both excluded --
# this mirrors the "Never use" list in docs/image-policy.md.
ALLOWED_LICENCES = (
    "cc0", "public domain", "publicdomain", "pdm", "no restrictions",
    "cc by", "cc-by", "by", "cc by-sa", "cc-by-sa", "by-sa", "attribution",
)
FORBIDDEN_MARKERS = ("nc", "nd", "noncommercial", "non-commercial", "noderiv")

# Google CSE `rights` values. NC/ND deliberately omitted so the API itself
# never returns material we could not lawfully use.
GOOGLE_RIGHTS = "cc_publicdomain|cc_attribute|cc_sharealike"


def licence_ok(lic: str) -> bool:
    """True only for commercial-safe CC / public-domain licences."""
    if not lic:
        return False
    s = re.sub(r"[^a-z0-9 -]", " ", lic.lower())
    toks = set(re.split(r"[ \-]+", s))
    # reject NC / ND however they are spelled
    if toks & set(FORBIDDEN_MARKERS):
        return False
    if "noncommercial" in s.replace(" ", "") or "noderivat" in s.replace(" ", ""):
        return False
    return any(a in s for a in ALLOWED_LICENCES)


# ---------------------------------------------------------------- attribution
# Wikimedia's "Artist" field is free text. It is often a name, but it is just as
# often a paragraph: contact requests, editing rules, email addresses. Rendering
# it raw put a four-line note under a hero. We want the NAME for the credit.
# "Timothy A. Gonsalves" must survive: a full stop after a single initial is part
# of the name, not the end of the sentence.
# A period is only part of the name when it follows a SINGLE letter (an initial).
# Allowing it after any word swallowed the next sentence ("Gonsalves. Feel").
_NAME = r"(?:[A-Z]\.\s+|[A-Z][\w'\u2019-]+\s+){0,3}[A-Z][\w'\u2019-]+"
_ARTIST_PATTERNS = (
    r"photo(?:graph)? (?:was )?taken by\s+(" + _NAME + r")",
    r"^\s*(?:by\s+)?(" + _NAME + r")\s*(?:$|[.,;\n])",
)
# An author asking to be contacted before commercial use has not changed the
# licence -- CC BY-SA 4.0 permits commercial reuse -- but this is a commercial
# product and there is no shortage of alternatives. Prefer another photograph
# rather than pick a fight nobody needs.
_COURTESY_FLAGS = (
    "contact me before commercial", "before commercial use",
    "not for commercial", "no commercial", "permission required",
    "please ask before", "commercial use requires",
)


def clean_artist(raw, limit=60):
    """A displayable author name from a free-text Wikimedia artist field."""
    t = _strip_html(raw or "").replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return "Unknown"
    for pat in _ARTIST_PATTERNS:
        m = re.search(pat, t, re.I)
        if m:
            name = m.group(1).strip(" .,;")
            if 2 <= len(name) <= limit:
                return name
    t = re.split(r"(?<=[.;])\s", t)[0].strip(" .,;")
    return (t[:limit].rsplit(" ", 1)[0] + "…") if len(t) > limit else (t or "Unknown")


def courtesy_blocked(candidate):
    """True when the author asks to be contacted before commercial reuse."""
    hay = " ".join(str(candidate.get(k) or "")
                   for k in ("artist_raw", "artist", "title")).lower()
    return any(f in hay for f in _COURTESY_FLAGS)

def _get(url, timeout=45, headers=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _json(url, **kw):
    return json.loads(_get(url, **kw).decode("utf-8", "replace"))


def _strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def _candidate(**kw):
    """Uniform shape every source returns."""
    c = {"title": "", "image_url": "", "page_url": "", "artist": "",
         "artist_raw": "", "licence": "", "licence_url": "", "source": "",
         "width": 0, "height": 0, "verified": False, "verify_note": ""}
    c.update(kw)
    return c


# ---------------------------------------------------------------- Wikimedia
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def search_wikimedia(query, n=8, width=1600):
    """Commons search. Licence comes straight from the API, so it is trusted."""
    q = {"action": "query", "generator": "search", "gsrsearch": query,
         "gsrnamespace": "6", "gsrlimit": str(n), "prop": "imageinfo",
         "iiprop": "url|extmetadata|size", "iiurlwidth": str(width),
         "format": "json"}
    try:
        data = _json(COMMONS_API + "?" + urllib.parse.urlencode(q))
    except Exception as e:
        print(f"  [wikimedia] search failed: {e}", file=sys.stderr)
        return []
    out = []
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        ii = (page.get("imageinfo") or [None])[0]
        if not ii:
            continue
        em = ii.get("extmetadata", {}) or {}
        lic = _strip_html(em.get("LicenseShortName", {}).get("value", ""))
        out.append(_candidate(
            title=page.get("title", "").replace("File:", ""),
            image_url=ii.get("thumburl") or ii.get("url", ""),
            page_url=ii.get("descriptionurl", ""),
            artist=clean_artist(em.get("Artist", {}).get("value", "")),
            # raw text kept ONLY for the courtesy check below -- cleaning first
            # strips the very notice we need to read
            artist_raw=_strip_html(em.get("Artist", {}).get("value", "")),
            licence=lic,
            licence_url=em.get("LicenseUrl", {}).get("value", ""),
            source="Wikimedia Commons",
            width=ii.get("width", 0), height=ii.get("height", 0),
            # authoritative: the licence was issued by the platform itself
            verified=licence_ok(lic),
            verify_note="Commons API licence" if licence_ok(lic) else "licence not commercial-safe",
        ))
    return out


# ---------------------------------------------------------------- Openverse
OPENVERSE_API = "https://api.openverse.org/v1/images/"


def search_openverse(query, n=8):
    """
    Openverse aggregates Flickr, Commons, museums, Rawpixel and more.
    `license_type=commercial,modification` asks the API for exactly the subset
    our policy allows, so results are authoritative.
    """
    q = {"q": query, "page_size": str(n),
         "license_type": "commercial,modification", "mature": "false"}
    try:
        data = _json(OPENVERSE_API + "?" + urllib.parse.urlencode(q))
    except Exception as e:
        print(f"  [openverse] search failed: {e}", file=sys.stderr)
        return []
    out = []
    for r in data.get("results", []) or []:
        lic = (r.get("license") or "").upper()
        ver = r.get("license_version") or ""
        pretty = f"CC {lic} {ver}".strip() if lic not in ("CC0", "PDM") else lic
        out.append(_candidate(
            title=r.get("title") or "",
            image_url=r.get("url") or "",
            page_url=r.get("foreign_landing_url") or r.get("detail_url") or "",
            artist=r.get("creator") or "Unknown",
            licence=pretty,
            licence_url=r.get("license_url") or "",
            source=f"Openverse · {r.get('source') or 'unknown'}",
            width=r.get("width") or 0, height=r.get("height") or 0,
            verified=licence_ok(pretty),
            verify_note="Openverse API licence" if licence_ok(pretty) else "licence not commercial-safe",
        ))
    return out


# ---------------------------------------------------------------- Google CSE
GOOGLE_API = "https://www.googleapis.com/customsearch/v1"


def google_configured():
    return bool(os.environ.get("GOOGLE_CSE_KEY") and os.environ.get("GOOGLE_CSE_CX"))


def search_google(query, n=8, rights=GOOGLE_RIGHTS):
    """
    Google Programmable Search, image mode, constrained by `rights`.

    DISCOVERY ONLY. Every candidate comes back verified=False with an explicit
    note, and must survive verify() before anything downstream may publish it.
    Google's rights filter reads licence metadata it has inferred from the host
    page; it is a useful narrowing signal and nothing more.
    """
    if not google_configured():
        print("  [google] GOOGLE_CSE_KEY / GOOGLE_CSE_CX not set — source skipped",
              file=sys.stderr)
        return []
    q = {"key": os.environ["GOOGLE_CSE_KEY"], "cx": os.environ["GOOGLE_CSE_CX"],
         "q": query, "searchType": "image", "num": str(min(int(n), 10)),
         "rights": rights, "safe": "active", "imgSize": "large",
         "imgType": "photo"}
    try:
        data = _json(GOOGLE_API + "?" + urllib.parse.urlencode(q))
    except Exception as e:
        print(f"  [google] search failed: {e}", file=sys.stderr)
        return []
    out = []
    for r in data.get("items", []) or []:
        img = r.get("image", {}) or {}
        out.append(_candidate(
            title=r.get("title") or "",
            image_url=r.get("link") or "",
            page_url=img.get("contextLink") or "",
            artist="",                      # Google supplies no author
            licence="",                     # and no licence we may trust
            licence_url="",
            source="Google CSE (unverified)",
            width=img.get("width") or 0, height=img.get("height") or 0,
            verified=False,
            verify_note="google rights-filtered candidate; licence not yet traced",
        ))
    return out


# ---------------------------------------------------------------- verification
_COMMONS_FILE_RE = re.compile(r"/wiki/(File:[^?#]+)", re.I)


def _verify_via_commons(page_url):
    m = _COMMONS_FILE_RE.search(page_url or "")
    if not m:
        return None
    title = urllib.parse.unquote(m.group(1))
    q = {"action": "query", "titles": title, "prop": "imageinfo",
         "iiprop": "url|extmetadata|size", "iiurlwidth": "1600", "format": "json"}
    try:
        data = _json(COMMONS_API + "?" + urllib.parse.urlencode(q))
    except Exception:
        return None
    page = next(iter((data.get("query", {}).get("pages", {}) or {}).values()), {})
    ii = (page.get("imageinfo") or [None])[0]
    if not ii:
        return None
    em = ii.get("extmetadata", {}) or {}
    return {
        "artist": clean_artist(em.get("Artist", {}).get("value", "")),
        "artist_raw": _strip_html(em.get("Artist", {}).get("value", "")),
        "licence": _strip_html(em.get("LicenseShortName", {}).get("value", "")),
        "licence_url": em.get("LicenseUrl", {}).get("value", ""),
        "image_url": ii.get("thumburl") or ii.get("url", ""),
        "source": "Wikimedia Commons",
        "note": "traced to Commons API",
    }


def _verify_via_openverse(page_url):
    """Ask Openverse whether it indexes this exact landing page."""
    if not page_url:
        return None
    q = {"q": page_url, "page_size": "5", "license_type": "commercial,modification"}
    try:
        data = _json(OPENVERSE_API + "?" + urllib.parse.urlencode(q))
    except Exception:
        return None
    for r in data.get("results", []) or []:
        if (r.get("foreign_landing_url") or "").rstrip("/") == page_url.rstrip("/"):
            lic = (r.get("license") or "").upper()
            ver = r.get("license_version") or ""
            pretty = f"CC {lic} {ver}".strip() if lic not in ("CC0", "PDM") else lic
            return {
                "artist": r.get("creator") or "Unknown",
                "licence": pretty,
                "licence_url": r.get("license_url") or "",
                "image_url": r.get("url") or "",
                "source": f"Openverse · {r.get('source') or 'unknown'}",
                "note": "traced to Openverse API",
            }
    return None


# Registry of (host fragment, verifier NAME). Names, not function objects, so the
# lookup resolves at call time -- that keeps the table patchable in tests and lets
# a new verifier be dropped in without rebuilding the tuple.
VERIFIERS = (
    ("commons.wikimedia.org", "_verify_via_commons"),
    ("upload.wikimedia.org",  "_verify_via_commons"),
    ("*",                     "_verify_via_openverse"),   # last-resort lookup
)


def _resolve_verifier(name):
    fn = globals().get(name)
    return fn if callable(fn) else None


def verify(candidates, pause=0.34):
    """
    Split candidates into (publishable, quarantined).

    A candidate is publishable only if a platform API returned a
    commercial-safe licence for it. Google-sourced candidates always go
    through a real trace; the rights filter alone never qualifies.
    """
    good, bad = [], []
    for c in candidates:
        if courtesy_blocked(c):
            c["verified"] = False
            c["verify_note"] = ("SKIPPED — author requests contact before commercial "
                                "use; licence allows it but we prefer another image")
            bad.append(c)
            continue
        if c.get("verified") and licence_ok(c.get("licence", "")):
            good.append(c)
            continue

        host = urllib.parse.urlparse(c.get("page_url") or "").netloc.lower()
        resolved = None
        for pattern, fname in VERIFIERS:
            if pattern != "*" and pattern not in host:
                continue
            fn = _resolve_verifier(fname)
            if fn is None:
                continue
            try:
                resolved = fn(c.get("page_url"))
            except Exception:
                resolved = None
            if resolved:
                break
            time.sleep(pause)

        if resolved and licence_ok(resolved.get("licence", "")):
            c.update({k: v for k, v in resolved.items() if k != "note"})
            c["verified"] = True
            c["verify_note"] = resolved["note"]
            good.append(c)
        else:
            c["verified"] = False
            c["verify_note"] = (
                "QUARANTINED — no commercial-safe licence could be traced to an "
                f"authoritative source (host: {host or 'unknown'})")
            bad.append(c)
        time.sleep(pause)
    return good, bad


# ---------------------------------------------------------------- discovery
def discover(query, per_source=6, sources=("wikimedia", "openverse", "google")):
    """Run every configured source and return a flat candidate list."""
    out = []
    if "wikimedia" in sources:
        out += search_wikimedia(query, per_source)
    if "openverse" in sources:
        out += search_openverse(query, per_source)
    if "google" in sources:
        out += search_google(query, per_source)
    # de-duplicate on image URL, keeping the first (most authoritative) hit
    seen, uniq = set(), []
    for c in out:
        k = (c.get("image_url") or "").split("?")[0]
        if not k or k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return uniq


def _main(argv):
    query = " ".join(argv[1:]) or "Maasai Mara wildebeest"
    print(f"query: {query!r}")
    print(f"google configured: {google_configured()}")
    cands = discover(query)
    good, bad = verify(cands)
    print(f"\n{len(cands)} candidates -> {len(good)} publishable, {len(bad)} quarantined\n")
    for c in good:
        print(f"  OK   [{c['licence']}] {c['title'][:60]}")
        print(f"       {c['source']} · {c['artist']} · {c['verify_note']}")
    for c in bad:
        print(f"  HOLD {c['title'][:60]}")
        print(f"       {c['verify_note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
