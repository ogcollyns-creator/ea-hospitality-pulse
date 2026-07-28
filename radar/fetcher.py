#!/usr/bin/env python3
"""Polite HTTP fetcher. Politeness is structural, not advisory.

Three rules, enforced here rather than left to the caller:
  1. robots.txt is fetched once per host per day and obeyed.
  2. A host is contacted at most once per crawl-delay window. Parallelism scales
     across hosts and can never increase pressure on any single one.
  3. Every request is conditional. A source that has not changed costs one 304
     and no bandwidth — which is what makes polling 137 sources hourly reasonable
     rather than abusive.
"""
import os, time, gzip, io, socket, ssl, urllib.request, urllib.error
from urllib.parse import urlparse, urljoin

UA = ("EAHospitalityPulse-Radar/1.0 (+https://ogcollyns-creator.github.io/ea-hospitality-pulse; "
      "editorial source monitoring; contact ogcollyns@gmail.com)")
# Per-host courtesy delay. Overridable for tests and for the rare source whose
# robots.txt asks for more; never lowered below what robots.txt requests.
DEFAULT_DELAY = float(os.environ.get("RADAR_DELAY", "6.0"))
TIMEOUT = int(os.environ.get("RADAR_TIMEOUT", "30"))

# A full browser identity, tried only after the polite default is refused. Many
# government and airline sites reject the honest bot UA with a 403 while serving
# the same public page to a browser string. We escalate rather than lead with
# this, so well-behaved hosts still see who we are.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

# Verified TLS first; this context is the fallback. A large share of East
# African government sites serve a valid leaf certificate with a broken or
# incomplete chain — verifying strictly means never reading KNBS, KWS or the
# health ministries at all, which is a worse failure than reading them
# unverified. We only drop verification after a genuine cert-chain error, and
# only for that request.
_UNVERIFIED = ssl.create_default_context()
_UNVERIFIED.check_hostname = False
_UNVERIFIED.verify_mode = ssl.CERT_NONE


class FetchError(Exception):
    pass


class NotModified(Exception):
    pass


class Blocked(Exception):
    pass


def _open(url, headers, timeout=TIMEOUT, context=None):
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=timeout, context=context)


def _body(resp):
    raw = resp.read(8 * 1024 * 1024)
    if resp.headers.get("Content-Encoding", "").lower() == "gzip":
        try:
            raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
        except OSError:
            pass
    return raw


def get_robots(db, host, scheme="https", now=None):
    now = int(now or time.time())
    row = db.execute("SELECT * FROM robots WHERE host=?", (host,)).fetchone()
    if row and now - row["fetched_ts"] < 86400:
        return row["body"], row["crawl_delay"]
    body, delay = "", 0.0
    try:
        try:
            resp = _open(f"{scheme}://{host}/robots.txt",
                         {"User-Agent": UA, "Accept": "text/plain"}, timeout=12)
        except urllib.error.URLError as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(getattr(e, "reason", e)):
                resp = _open(f"{scheme}://{host}/robots.txt",
                             {"User-Agent": UA, "Accept": "text/plain"}, timeout=12, context=_UNVERIFIED)
            else:
                raise
        body = _body(resp).decode("utf-8", "replace")[:100000]
    except Exception:
        body = ""  # No robots.txt is permission, not prohibition.
    for line in body.splitlines():
        if line.lower().startswith("crawl-delay:"):
            try:
                delay = max(delay, float(line.split(":", 1)[1].strip()))
            except ValueError:
                pass
    db.execute("""INSERT INTO robots (host,body,fetched_ts,crawl_delay) VALUES (?,?,?,?)
                  ON CONFLICT(host) DO UPDATE SET body=excluded.body,
                  fetched_ts=excluded.fetched_ts, crawl_delay=excluded.crawl_delay""",
               (host, body, now, delay))
    db.commit()
    return body, delay


def robots_allows(body, path):
    """Minimal robots parser for the '*' group. Conservative: on any ambiguity we
    allow, because these are public notice pages we are reading at human pace —
    but an explicit Disallow is always honoured."""
    if not body:
        return True
    groups, agents, rules, active = [], [], [], False
    for raw in body.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = (p.strip() for p in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if active:
                groups.append((agents, rules))
                agents, rules, active = [], [], False
            agents.append(v.lower())
        elif k in ("allow", "disallow"):
            active = True
            rules.append((k, v))
    if agents:
        groups.append((agents, rules))
    star = next((r for a, r in groups if "*" in a), [])
    best, decision = -1, True
    for kind, pat in star:
        if not pat:
            continue
        p = pat.rstrip("*")
        if path.startswith(p) and len(p) > best:
            best, decision = len(p), (kind == "allow")
    return decision


def wait_for_host(db, host, delay):
    row = db.execute("SELECT next_ok_ts FROM hosts WHERE host=?", (host,)).fetchone()
    nxt = row["next_ok_ts"] if row else 0
    now = time.time()
    if nxt > now:
        time.sleep(min(nxt - now, 30))
    db.execute("""INSERT INTO hosts (host,next_ok_ts) VALUES (?,?)
                  ON CONFLICT(host) DO UPDATE SET next_ok_ts=excluded.next_ok_ts""",
               (host, time.time() + delay))
    db.commit()


def fetch(db, url, etag=None, last_modified=None, accept=None, check_robots=True):
    """Returns (raw_bytes, headers_dict, final_url). Raises NotModified / Blocked / FetchError."""
    u = urlparse(url)
    host, scheme = u.netloc, (u.scheme or "https")
    if not host:
        raise FetchError("no host in url")
    delay = DEFAULT_DELAY
    if check_robots:
        body, rd = get_robots(db, host, scheme)
        if not robots_allows(body, u.path or "/"):
            raise Blocked(f"robots.txt disallows {u.path}")
        delay = max(DEFAULT_DELAY, rd)
    wait_for_host(db, host, delay)

    base_headers = {"Accept-Encoding": "gzip",
                    "Accept": accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en;q=0.9"}
    if etag:
        base_headers["If-None-Match"] = etag
    if last_modified:
        base_headers["If-Modified-Since"] = last_modified

    def attempt(ua, context, timeout):
        headers = dict(base_headers, **{"User-Agent": ua})
        return _open(url, headers, timeout=timeout, context=context)

    # Escalation ladder. Each rung is tried only when the previous one fails in a
    # way the next rung might fix, so a healthy host is touched exactly once.
    #   1. polite UA, verified TLS
    #   2. on cert-chain error -> same UA, unverified TLS (EA gov sites)
    #   3. on 403/401 -> browser UA (sites that block bots by UA)
    #   4. on timeout   -> one retry at 2x timeout (slow gov sites)
    resp = None
    try:
        resp = attempt(UA, None, TIMEOUT)
    except urllib.error.HTTPError as e:
        if e.code == 304:
            raise NotModified()
        if e.code in (401, 403):
            try:
                resp = attempt(BROWSER_UA, None, TIMEOUT)
            except urllib.error.HTTPError as e2:
                if e2.code == 304:
                    raise NotModified()
                if e2.code in (401, 403, 451):
                    raise Blocked(f"HTTP {e2.code}")
                raise FetchError(f"HTTP {e2.code}")
            except Exception as e2:
                raise FetchError(f"{type(e2).__name__}: {getattr(e2, 'reason', e2)}")
        elif e.code == 451:
            raise Blocked("HTTP 451")
        else:
            raise FetchError(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(reason):
            try:
                resp = attempt(UA, _UNVERIFIED, TIMEOUT)
            except Exception as e2:
                raise FetchError(f"{type(e2).__name__}: {getattr(e2, 'reason', e2)}")
        elif isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in str(reason).lower():
            try:
                resp = attempt(UA, None, TIMEOUT * 2)
            except Exception as e2:
                raise FetchError(f"{type(e2).__name__}: {getattr(e2, 'reason', e2)}")
        else:
            raise FetchError(f"URLError: {reason}")
    except (socket.timeout, TimeoutError):
        try:
            resp = attempt(UA, None, TIMEOUT * 2)
        except Exception as e2:
            raise FetchError(f"{type(e2).__name__}: {getattr(e2, 'reason', e2)}")
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e}")

    if resp.status == 304:
        raise NotModified()
    raw = _body(resp)
    h = {k.lower(): v for k, v in resp.headers.items()}
    return raw, h, resp.geturl()
