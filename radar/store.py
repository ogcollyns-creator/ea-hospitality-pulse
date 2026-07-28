#!/usr/bin/env python3
"""SQLite store for the EA Pulse source radar.

Everything the scanner needs to resume lives here — never in memory. Kill the
process at any point and re-run `scan`; it picks up from the last committed row.

The single most valuable column in this database is items.first_seen_ts. It is
written once and never updated. That column is what makes the recency gate
enforceable: it records when *we* first observed an item, independent of whatever
date a page claims. It cannot be backfilled — start collecting it on day one.
"""
import sqlite3, os, time, json

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS sources (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  url            TEXT NOT NULL,
  tier           INTEGER NOT NULL,
  country        TEXT NOT NULL,
  category       TEXT NOT NULL,
  method_hint    TEXT NOT NULL,
  cadence_min    INTEGER NOT NULL,
  lead_days      INTEGER NOT NULL DEFAULT 0,
  segments       TEXT NOT NULL DEFAULT '[]',
  slots          TEXT NOT NULL DEFAULT '[]',
  why            TEXT NOT NULL DEFAULT '',
  frag           TEXT NOT NULL DEFAULT '',
  -- negotiated at runtime, cached thereafter
  resolved_method TEXT,
  feed_url       TEXT,
  etag           TEXT,
  last_modified  TEXT,
  content_hash   TEXT,
  last_ok_ts     INTEGER,
  last_try_ts    INTEGER,
  last_change_ts INTEGER,
  fail_streak    INTEGER NOT NULL DEFAULT 0,
  breaker_until  INTEGER NOT NULL DEFAULT 0,
  last_error     TEXT NOT NULL DEFAULT '',
  enabled        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS items (
  key            TEXT PRIMARY KEY,     -- sha1(source_id|canonical_url|title)
  source_id      TEXT NOT NULL,
  url            TEXT NOT NULL,
  title          TEXT NOT NULL DEFAULT '',
  summary        TEXT NOT NULL DEFAULT '',
  published_ts   INTEGER,              -- from the source, if it states one
  first_seen_ts  INTEGER NOT NULL,     -- when WE first saw it. Never updated.
  content_hash   TEXT NOT NULL DEFAULT '',
  kind           TEXT NOT NULL DEFAULT 'item',  -- item | page-change | doc
  FOREIGN KEY (source_id) REFERENCES sources(id)
);
CREATE INDEX IF NOT EXISTS idx_items_first_seen ON items(first_seen_ts DESC);
CREATE INDEX IF NOT EXISTS idx_items_source ON items(source_id, first_seen_ts DESC);

CREATE TABLE IF NOT EXISTS robots (
  host           TEXT PRIMARY KEY,
  body           TEXT NOT NULL DEFAULT '',
  fetched_ts     INTEGER NOT NULL,
  crawl_delay    REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hosts (
  host           TEXT PRIMARY KEY,
  next_ok_ts     REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS runs (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  started_ts     INTEGER NOT NULL,
  finished_ts    INTEGER,
  tried          INTEGER NOT NULL DEFAULT 0,
  changed        INTEGER NOT NULL DEFAULT 0,
  new_items      INTEGER NOT NULL DEFAULT 0,
  errors         INTEGER NOT NULL DEFAULT 0,
  note           TEXT NOT NULL DEFAULT ''
);
"""


def connect(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def load_registry(db, registry_path):
    """Idempotent upsert of the registry. Preserves all runtime state columns —
    editing registry.json never resets etags, hashes or first_seen history."""
    with open(registry_path) as f:
        reg = json.load(f)
    seen = set()
    for s in reg["sources"]:
        seen.add(s["id"])
        db.execute("""
          INSERT INTO sources (id,name,url,tier,country,category,method_hint,
                               cadence_min,lead_days,segments,slots,why,frag)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, url=excluded.url, tier=excluded.tier,
            country=excluded.country, category=excluded.category,
            method_hint=excluded.method_hint, cadence_min=excluded.cadence_min,
            lead_days=excluded.lead_days, segments=excluded.segments,
            slots=excluded.slots, why=excluded.why, frag=excluded.frag
        """, (s["id"], s["name"], s["url"], s["tier"], s["country"], s["category"],
              s["method"], s["cadence_min"], s.get("lead_days", 0),
              json.dumps(s.get("segments", [])), json.dumps(s.get("slots", [])),
              s.get("why", ""), s.get("frag", "")))
    # Sources removed from the registry are disabled, not deleted — their item
    # history stays queryable and re-adding them restores state.
    db.execute("UPDATE sources SET enabled=0 WHERE id NOT IN (%s)" %
               ",".join("?" * len(seen)), tuple(seen))
    db.execute("UPDATE sources SET enabled=1 WHERE id IN (%s)" %
               ",".join("?" * len(seen)), tuple(seen))
    db.commit()
    return len(seen)


def due_sources(db, now=None, force=False, only=None, slot=None):
    """Sources past their cadence, with a closed circuit breaker."""
    now = int(now or time.time())
    q = "SELECT * FROM sources WHERE enabled=1"
    args = []
    if not force:
        q += " AND (breaker_until <= ?) AND (last_try_ts IS NULL OR last_try_ts + cadence_min*60 <= ?)"
        args += [now, now]
    if only:
        q += " AND id IN (%s)" % ",".join("?" * len(only))
        args += list(only)
    if slot:
        q += " AND slots LIKE ?"
        args.append("%%\"%s\"%%" % slot)
    # Tier 1 first, then whatever has waited longest.
    q += " ORDER BY tier ASC, COALESCE(last_try_ts,0) ASC"
    return [dict(r) for r in db.execute(q, args).fetchall()]


def record_attempt(db, sid, ok, *, etag=None, last_modified=None, content_hash=None,
                   changed=False, error="", now=None):
    now = int(now or time.time())
    if ok:
        db.execute("""UPDATE sources SET last_try_ts=?, last_ok_ts=?, fail_streak=0,
                      breaker_until=0, last_error='',
                      etag=COALESCE(?,etag), last_modified=COALESCE(?,last_modified),
                      content_hash=COALESCE(?,content_hash),
                      last_change_ts=CASE WHEN ? THEN ? ELSE last_change_ts END
                      WHERE id=?""",
                   (now, now, etag, last_modified, content_hash, 1 if changed else 0, now, sid))
    else:
        row = db.execute("SELECT fail_streak FROM sources WHERE id=?", (sid,)).fetchone()
        streak = (row["fail_streak"] if row else 0) + 1
        # Exponential backoff, capped at 12h. A source that is down stops being
        # retried aggressively but is never silently dropped — monitor.py lists it.
        breaker = now + min(12 * 3600, 900 * (2 ** min(streak - 1, 5))) if streak >= 3 else 0
        db.execute("""UPDATE sources SET last_try_ts=?, fail_streak=?, breaker_until=?,
                      last_error=? WHERE id=?""", (now, streak, breaker, error[:300], sid))
    db.commit()


def upsert_item(db, key, source_id, url, title, summary, published_ts, content_hash,
                kind="item", now=None):
    """Returns True if this is the first time we have ever seen this item.

    first_seen_ts is written on insert only. The ON CONFLICT clause deliberately
    updates nothing — a re-observed item must not have its provenance rewritten."""
    now = int(now or time.time())
    cur = db.execute("""INSERT INTO items (key,source_id,url,title,summary,published_ts,
                                           first_seen_ts,content_hash,kind)
                        VALUES (?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(key) DO NOTHING""",
                     (key, source_id, url, title[:500], summary[:2000], published_ts,
                      now, content_hash, kind))
    return cur.rowcount > 0


def start_run(db, note=""):
    cur = db.execute("INSERT INTO runs (started_ts,note) VALUES (?,?)", (int(time.time()), note))
    db.commit()
    return cur.lastrowid


def finish_run(db, run_id, tried, changed, new_items, errors):
    db.execute("""UPDATE runs SET finished_ts=?, tried=?, changed=?, new_items=?, errors=?
                  WHERE id=?""",
               (int(time.time()), tried, changed, new_items, errors, run_id))
    db.commit()
