#!/usr/bin/env python3
"""Render radar.js — the data file behind radar.html.

Deliberately writes a JS global rather than JSON, matching the existing site
convention (data.js, rules.js, advisories.js) so the page works from a static
host with no fetch, no CORS and no build step."""
import os, sys, json, time, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import store

EAT = datetime.timezone(datetime.timedelta(hours=3))


def iso(ts):
    return datetime.datetime.fromtimestamp(ts, EAT).isoformat(timespec="minutes") if ts else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.path.join(HERE, "radar.db"))
    p.add_argument("--candidates", default=os.path.join(HERE, "out", "candidates.json"))
    p.add_argument("--out", default=os.path.join(REPO, "radar.js"))
    a = p.parse_args()

    db = store.connect(a.db)
    now = int(time.time())

    srcs = []
    for r in db.execute("SELECT * FROM sources WHERE enabled=1 ORDER BY tier, country, name"):
        srcs.append({
            "id": r["id"], "name": r["name"], "url": r["url"], "tier": r["tier"],
            "country": r["country"], "category": r["category"],
            "method": r["resolved_method"] or r["method_hint"],
            "cadence_min": r["cadence_min"], "lead_days": r["lead_days"],
            "why": r["why"],
            "last_ok": iso(r["last_ok_ts"]), "last_change": iso(r["last_change_ts"]),
            "fails": r["fail_streak"], "error": r["last_error"][:160],
            "items": db.execute("SELECT COUNT(*) c FROM items WHERE source_id=?",
                                (r["id"],)).fetchone()["c"],
            "healthy": bool(r["last_ok_ts"]) and r["fail_streak"] == 0,
        })

    runs = [{"id": r["id"], "started": iso(r["started_ts"]), "tried": r["tried"],
             "changed": r["changed"], "new": r["new_items"], "errors": r["errors"],
             "slot": r["note"]}
            for r in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 24")]

    cands, meta = [], {}
    if os.path.exists(a.candidates):
        payload = json.load(open(a.candidates))
        meta = {k: payload.get(k) for k in
                ("generated", "slot", "window_start", "observations_in_window", "deduped_against")}
        cands = payload.get("candidates", [])[:40]

    recent = [{"title": r["title"][:180], "url": r["url"], "source": r["source_name"],
               "country": r["country"], "tier": r["tier"], "kind": r["kind"],
               "first_seen": iso(r["first_seen_ts"]),
               "published": (datetime.datetime.fromtimestamp(r["published_ts"], EAT).date().isoformat()
                             if r["published_ts"] else None)}
              for r in db.execute("""SELECT i.*, s.name source_name, s.country, s.tier
                                     FROM items i JOIN sources s ON s.id=i.source_id
                                     WHERE s.enabled=1
                                     ORDER BY i.first_seen_ts DESC LIMIT 120""")]

    data = {
        "generated": iso(now),
        "meta": meta,
        "stats": {
            "sources": len(srcs),
            "healthy": sum(1 for s in srcs if s["healthy"]),
            "never": sum(1 for s in srcs if not s["last_ok"]),
            "tier1": sum(1 for s in srcs if s["tier"] == 1),
            "items_total": db.execute("SELECT COUNT(*) c FROM items").fetchone()["c"],
            "items_24h": db.execute("SELECT COUNT(*) c FROM items WHERE first_seen_ts>?",
                                    (now - 86400,)).fetchone()["c"],
            "changed_24h": sum(1 for s in srcs if s["last_change"] and
                               time.mktime(datetime.datetime.fromisoformat(s["last_change"]).timetuple()) > now - 86400),
        },
        "sources": srcs, "runs": runs, "candidates": cands, "recent": recent,
    }
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("window.RADAR = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"wrote {a.out} — {len(srcs)} sources, {len(cands)} candidates, {len(recent)} recent items")


if __name__ == "__main__":
    main()
