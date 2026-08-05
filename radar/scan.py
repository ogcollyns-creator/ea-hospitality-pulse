#!/usr/bin/env python3
"""EA Pulse source radar — scanner.

  python3 radar/scan.py init
  python3 radar/scan.py scan  [--workers 8] [--max-seconds 900] [--slot midday] [--only id,id]
  python3 radar/scan.py status
  python3 radar/scan.py health

Design note: sources are grouped by host and each host is processed by exactly
one worker, sequentially. Politeness therefore holds no matter what --workers is
set to, and raising it only widens the front across hosts.
"""
import sys, os, time, json, argparse, threading, re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import store, fetcher, extract as X

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "radar.db")
REGISTRY = os.path.join(HERE, "registry.json")

_local = threading.local()


def db_for_thread(path):
    if not hasattr(_local, "db"):
        _local.db = store.connect(path)
        _local.db.execute("PRAGMA busy_timeout=30000")
    return _local.db


def norm_title(t):
    return re.sub(r"[^a-z0-9 ]+", "", (t or "").lower())[:120].strip()


def item_key(sid, url, title):
    return X.sha1(f"{sid}|{X.canon(url)}|{norm_title(title)}")


# ---------------------------------------------------------------- negotiation

def negotiate(db, src, raw, headers, final_url):
    """Decide the cheapest detection method that actually works for this source,
    then cache it. Run once per source, not once per scan."""
    hint = src["method_hint"]
    ctype = headers.get("content-type", "")
    if hint == "rss" or "xml" in ctype and b"<rss" in raw[:2000] or b"<feed" in raw[:2000]:
        if X.parse_feed(raw):
            return "rss", final_url
    text = X.decode(raw, ctype)
    feed = X.discover_feed(text, final_url)
    if feed:
        try:
            fraw, fh, furl = fetcher.fetch(db, feed, accept="application/rss+xml,application/xml")
            if len(X.parse_feed(fraw)) >= 2:
                return "rss", furl
        except Exception:
            pass
    if hint == "pdf":
        return "pdf", None
    return "html", None


# ---------------------------------------------------------------- per-method scans

def scan_rss(db, src, dbw):
    raw, h, furl = fetcher.fetch(db, src["feed_url"] or src["url"],
                                 src["etag"], src["last_modified"],
                                 accept="application/rss+xml,application/xml;q=0.9,*/*;q=0.8")
    items = X.parse_feed(raw)
    new = 0
    for it in items[:60]:
        if not it["url"]:
            continue
        k = item_key(src["id"], it["url"], it["title"])
        if store.upsert_item(dbw, k, src["id"], X.canon(it["url"]), it["title"],
                             it["summary"], it["published_ts"], "", "item"):
            new += 1
    dbw.commit()
    return new, h.get("etag"), h.get("last-modified"), X.sha1(str(sorted(i["url"] for i in items)))


def scan_html(db, src, dbw, follow_docs=0):
    raw, h, furl = fetcher.fetch(db, src["url"], src["etag"], src["last_modified"])
    text = X.decode(raw, h.get("content-type", ""))
    if src["frag"] and src["frag"] in text:
        text = text.split(src["frag"], 1)[1]
    try:
        ml = src["min_len"]
    except (KeyError, IndexError):
        ml = 28
    items = X.extract_items(text, furl, min_len=ml or 28)
    new, docs_fetched = 0, 0
    if items:
        for it in items[:80]:
            k = item_key(src["id"], it["url"], it["title"])
            fresh = store.upsert_item(dbw, k, src["id"], it["url"], it["title"], "",
                                      None, "", "doc" if it["is_doc"] else "item")
            if fresh:
                new += 1
                # Only newly-seen documents are opened, capped per run. This keeps
                # a ministry that posts 40 PDFs from becoming a 40-request burst.
                if it["is_doc"] and docs_fetched < follow_docs:
                    docs_fetched += 1
                    try:
                        draw, dh, _ = fetcher.fetch(db, it["url"], accept="application/pdf,*/*")
                        body = X.pdf_text(draw) if b"%PDF" in draw[:1024] else X.html_to_text(X.decode(draw))
                        if body:
                            dbw.execute("UPDATE items SET summary=?, published_ts=COALESCE(published_ts,?), "
                                        "content_hash=? WHERE key=?",
                                        (body[:2000], X.first_date_in(body), X.sha1(body), k))
                    except Exception:
                        pass
        content_hash = X.sha1(str(sorted(i["url"] for i in items)))
    else:
        # No headline-shaped anchors: fall back to hashing the readable body. We
        # lose per-item granularity but still detect that the page moved, which
        # for a single-notice regulator page is the whole signal.
        body = X.html_to_text(text)
        content_hash = X.sha1(body)
        if content_hash != (src["content_hash"] or ""):
            k = X.sha1(f"{src['id']}|page|{content_hash}")
            if store.upsert_item(dbw, k, src["id"], src["url"],
                                 f"[page changed] {src['name']}", body[:1500],
                                 X.first_date_in(body), content_hash, "page-change"):
                new += 1
    dbw.commit()
    return new, h.get("etag"), h.get("last-modified"), content_hash


SCANNERS = {"rss": scan_rss, "html": scan_html, "pdf": scan_html}


def scan_source(src, db_path, follow_docs):
    dbw = db_for_thread(db_path)
    sid = src["id"]
    try:
        method = src["resolved_method"]
        if not method:
            raw, h, furl = fetcher.fetch(dbw, src["url"])
            method, feed = negotiate(dbw, src, raw, h, furl)
            dbw.execute("UPDATE sources SET resolved_method=?, feed_url=? WHERE id=?",
                        (method, feed, sid))
            dbw.commit()
            src = dict(dbw.execute("SELECT * FROM sources WHERE id=?", (sid,)).fetchone())
        fn = SCANNERS.get(method, scan_html)
        kw = {"follow_docs": follow_docs} if fn is scan_html else {}
        new, etag, lm, chash = fn(dbw, src, dbw, **kw)
        changed = bool(new) or chash != (src["content_hash"] or "")
        store.record_attempt(dbw, sid, True, etag=etag, last_modified=lm,
                             content_hash=chash, changed=changed)
        return (sid, "ok", new, changed, "")
    except fetcher.NotModified:
        store.record_attempt(dbw, sid, True)
        return (sid, "304", 0, False, "")
    except fetcher.Blocked as e:
        store.record_attempt(dbw, sid, False, error=f"blocked: {e}")
        return (sid, "blocked", 0, False, str(e))
    except Exception as e:
        store.record_attempt(dbw, sid, False, error=f"{type(e).__name__}: {e}")
        return (sid, "error", 0, False, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- commands

def cmd_init(a):
    db = store.connect(a.db)
    n = store.load_registry(db, a.registry)
    print(f"registry loaded: {n} sources → {a.db}")


def cmd_scan(a):
    db = store.connect(a.db)
    store.load_registry(db, a.registry)
    only = a.only.split(",") if a.only else None
    due = store.due_sources(db, force=a.force, only=only, slot=a.slot)
    if a.limit:
        due = due[: a.limit]
    if not due:
        print("nothing due")
        return
    run_id = store.start_run(db, note=a.slot or "")
    by_host = {}
    for s in due:
        by_host.setdefault(urlparse(s["url"]).netloc, []).append(s)
    print(f"scanning {len(due)} sources across {len(by_host)} hosts, workers={a.workers}")

    deadline = time.time() + a.max_seconds
    results, lock = [], threading.Lock()

    def run_host(group):
        out = []
        for s in group:
            if time.time() > deadline:
                break
            out.append(scan_source(s, a.db, a.follow_docs))
        with lock:
            results.extend(out)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(run_host, by_host.values()))

    ok = sum(1 for r in results if r[1] in ("ok", "304"))
    changed = sum(1 for r in results if r[3])
    new = sum(r[2] for r in results)
    errs = [r for r in results if r[1] in ("error", "blocked")]
    store.finish_run(db, run_id, len(results), changed, new, len(errs))
    print(f"done: {len(results)} tried | {ok} ok | {changed} changed | {new} new items | {len(errs)} errors")
    for sid, st, _, _, msg in errs[:15]:
        print(f"  ! {sid}: {st} {msg[:90]}")


def cmd_status(a):
    db = store.connect(a.db)
    r = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    if r:
        print(f"last run #{r['id']}: tried={r['tried']} changed={r['changed']} "
              f"new={r['new_items']} errors={r['errors']}")
    tot = db.execute("SELECT COUNT(*) c FROM sources WHERE enabled=1").fetchone()["c"]
    never = db.execute("SELECT COUNT(*) c FROM sources WHERE enabled=1 AND last_ok_ts IS NULL").fetchone()["c"]
    items = db.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    day = db.execute("SELECT COUNT(*) c FROM items WHERE first_seen_ts > ?",
                     (int(time.time()) - 86400,)).fetchone()["c"]
    print(f"sources: {tot} enabled | {never} never fetched")
    print(f"items: {items} total | {day} first seen in last 24h")
    print("\nmost recent first-seen:")
    for row in db.execute("""SELECT i.title, s.name, i.first_seen_ts FROM items i
                             JOIN sources s ON s.id=i.source_id
                             ORDER BY i.first_seen_ts DESC LIMIT 10"""):
        print(f"  {time.strftime('%d %b %H:%M', time.localtime(row['first_seen_ts']))} "
              f"· {row['name'][:28]:28} · {row['title'][:70]}")


def cmd_health(a):
    db = store.connect(a.db)
    now = int(time.time())
    rows = db.execute("""SELECT * FROM sources WHERE enabled=1 ORDER BY fail_streak DESC,
                         COALESCE(last_ok_ts,0) ASC""").fetchall()
    bad = [r for r in rows if r["fail_streak"] > 0 or r["last_ok_ts"] is None]
    print(f"{len(rows)-len(bad)}/{len(rows)} sources healthy\n")
    if bad:
        print("needs attention (a dead source is a blind spot, not a non-event):")
        for r in bad[:40]:
            age = f"{(now-r['last_ok_ts'])//3600}h" if r["last_ok_ts"] else "never"
            print(f"  {r['id']:24} fails={r['fail_streak']:<3} last_ok={age:<7} {r['last_error'][:70]}")



def cmd_export(a):
    """Append-only JSONL mirror of the items table.

    The SQLite file is a cache; this file is the record. first_seen_ts is the one
    column in this system that cannot be reconstructed after the fact, so it must
    survive a lost CI cache, a corrupted database and a fresh checkout. JSONL
    because it is append-only, diffs cleanly in git, and can be replayed by
    anything — including a human with grep."""
    db = store.connect(a.db)
    path = a.out
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    have = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                try:
                    have.add(json.loads(line)["key"])
                except Exception:
                    continue
    n = 0
    with open(path, "a") as f:
        for r in db.execute("SELECT * FROM items ORDER BY first_seen_ts ASC"):
            if r["key"] in have:
                continue
            f.write(json.dumps({
                "key": r["key"], "source_id": r["source_id"], "url": r["url"],
                "title": r["title"], "published_ts": r["published_ts"],
                "first_seen_ts": r["first_seen_ts"], "kind": r["kind"],
            }, ensure_ascii=False) + "\n")
            n += 1
    print(f"exported {n} new rows -> {path} ({len(have)+n} total)")


def cmd_restore(a):
    """Replay the JSONL ledger into a database, preserving original first_seen_ts.

    Run after a cache miss. Existing rows are never overwritten, so replaying a
    ledger over a live database is safe and idempotent."""
    db = store.connect(a.db)
    store.load_registry(db, a.registry)
    if not os.path.exists(a.out):
        print(f"no ledger at {a.out} — nothing to restore")
        return
    n = 0
    for line in open(a.out):
        try:
            r = json.loads(line)
        except Exception:
            continue
        cur = db.execute("""INSERT INTO items (key,source_id,url,title,summary,
                            published_ts,first_seen_ts,content_hash,kind)
                            VALUES (?,?,?,?,'',?,?,'',?)
                            ON CONFLICT(key) DO NOTHING""",
                         (r["key"], r["source_id"], r["url"], r.get("title", ""),
                          r.get("published_ts"), r["first_seen_ts"], r.get("kind", "item")))
        n += cur.rowcount
    db.commit()
    print(f"restored {n} items from ledger (first_seen preserved)")


def cmd_checkpoint(a):
    db = store.connect(a.db)
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    db.commit()
    print("wal checkpointed")


def main():
    p = argparse.ArgumentParser(prog="radar/scan.py")
    p.add_argument("--db", default=DB)
    p.add_argument("--registry", default=REGISTRY)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    s = sub.add_parser("scan")
    s.add_argument("--workers", type=int, default=8)
    s.add_argument("--max-seconds", type=int, default=900)
    s.add_argument("--slot", choices=["morning", "midday", "evening"])
    s.add_argument("--only")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--force", action="store_true")
    s.add_argument("--follow-docs", type=int, default=3,
                   help="max newly-seen PDFs to open per source per run")
    s.set_defaults(fn=cmd_scan)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("health").set_defaults(fn=cmd_health)
    for name, fn in (("export", cmd_export), ("restore", cmd_restore)):
        sp = sub.add_parser(name)
        sp.add_argument("--out", default=os.path.join(HERE, "out", "items.jsonl"))
        sp.set_defaults(fn=fn)
    sub.add_parser("checkpoint").set_defaults(fn=cmd_checkpoint)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
