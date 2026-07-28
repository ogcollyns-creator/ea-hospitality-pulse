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
import os, time, gzip, io, socket, urllib.request, urllib.error
from urllib.parse import urlparse, urljoin

UA = ("EAHospitalityPulse-Radar/1.0 (+https://ogcollyns-creator.github.io/ea-hospitality-pulse; "
      "editorial source monitoring; contact ogcollyns@gmail.com)")
# Per-host courtesy delay. Overridable for tests and for the rare source whose
# robots.txt asks for more; never lowered below what robots.txt requests.
DEFAULT_DELAY = float(os.environ.get("RADAR_DELAY", "6.0"))
TIMEOUT = int(os.environ.get("RADAR_TIMEOUT", "25"))


class FetchError(Exception):
    pass


class NotModified(Exception):
    pass


class Blocked(Exception):
    pass


def _open(url, headers, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=headers)
    return urllib.request.urlopen(req, timeout=timeout)


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
        resp = _open(f"{scheme}://{host}/robots.txt",
                     {"User-Agent": UA, "Accept": "text/plain"}, timeout=12)
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

    headers = {"User-Agent": UA, "Accept-Encoding": "gzip",
               "Accept": accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-GB,en;q=0.9"}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    try:
        resp = _open(url, headers)
    except urllib.error.HTTPError as e:
        if e.code == 304:
            raise NotModified()
        if e.code in (401, 403, 451):
            raise Blocked(f"HTTP {e.code}")
        raise FetchError(f"HTTP {e.code}")
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        raise FetchError(f"{type(e).__name__}: {getattr(e, 'reason', e)}")
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e}")

    if resp.status == 304:
        raise NotModified()
    raw = _body(resp)
    h = {k.lower(): v for k, v in resp.headers.items()}
    return raw, h, resp.geturl()
