#!/usr/bin/env python3
"""Validation-gated feed remediation for blind sources.

Nothing goes live unvalidated. Candidates live in radar/feed_candidates.json and
are INERT until this script — on a live-network runner — fetches each one, proves
it parses into real items with the SAME parser the scanner uses, and only THEN
writes it into registry.json. A wrong guess simply fails to promote; it never
degrades a working source.

For every candidate the validator tries, in order:
  1. each explicit 'try' entry (rss: parse_feed>=1; html: extract_items>=1)
  2. auto-discovery: fetch the source's current page and follow its advertised
     <link rel=alternate> feed — so a source we gave no URL for can still self-heal
On the first success it promotes (sets method/url/frag). 'action:disable' entries
are applied offline (safe — the source produces nothing). 'needs:*' entries are
reported for headless/manual follow-up and never auto-promoted.

  python3 radar/validate_feeds.py --report              # offline: show the plan
  python3 radar/validate_feeds.py --apply-disables      # offline: disable redundant sources
  python3 radar/validate_feeds.py --promote             # runner: live-validate + promote
"""
import os, sys, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
REG  = os.path.join(HERE, "registry.json")
CAND = os.path.join(HERE, "feed_candidates.json")
OUT  = os.path.join(HERE, "out", "feed-validation.md")

def load_reg():
    reg = json.load(open(REG)); return reg, {s["id"]: s for s in reg["sources"]}
def save_reg(reg):
    json.dump(reg, open(REG, "w"), indent=1, ensure_ascii=True); open(REG,"a").write("\n")

# ---- live validation (only called under --promote) -------------------------
def _probe(url, method, frag, db, X, fetcher, min_len=None):
    """Return item count for a candidate, or -1 on fetch/parse failure."""
    try:
        raw, h, furl = fetcher.fetch(db, url)
    except Exception as e:
        return -1, f"fetch failed: {type(e).__name__}: {str(e)[:60]}"
    try:
        if method == "rss":
            return len(X.parse_feed(raw)), "ok"
        text = X.decode(raw, h.get("content-type", ""))
        if frag and frag in text: text = text.split(frag, 1)[1]
        return len(X.extract_items(text, furl, min_len=min_len or 28)), "ok"
    except Exception as e:
        return -1, f"parse failed: {type(e).__name__}: {str(e)[:60]}"

def _autodiscover(src_url, db, X, fetcher):
    """Fetch the page, follow its advertised feed. Returns (feed_url, count) or (None,0)."""
    try:
        raw, h, furl = fetcher.fetch(db, src_url)
        text = X.decode(raw, h.get("content-type", ""))
        feed = X.discover_feed(text, furl)
        if not feed: return None, 0
        fraw, fh, ffurl = fetcher.fetch(db, feed)
        return feed, len(X.parse_feed(fraw))
    except Exception:
        return None, 0

def promote(sid, src, method, url, frag=None, min_len=None):
    src["method"] = method; src["url"] = url
    if frag is not None: src["frag"] = frag
    if min_len is not None: src["min_len"] = min_len

def validate_plan(sid, src, plan, probe, discover):
    """Pure decision core (injectable probe/discover) — used by run_promote and tests.
    probe(url, method, frag) -> (item_count, msg);  discover(src_url) -> (feed_url, count).
    Mutates src on promotion/disable. Returns (status, detail)."""
    if plan.get("action") == "disable":
        src["enabled"] = False
        return "DISABLED", plan.get("reason", "")
    for c in plan.get("try", []):
        n, msg = probe(c["url"], c["method"], c.get("frag"), c.get("min_len"))
        if n >= 1:
            promote(sid, src, c["method"], c["url"], c.get("frag"), c.get("min_len"))
            return "PROMOTED", f"{c['method']} {c['url']} ({n} items)"
    feed, n = discover(src["url"])
    if feed and n >= 1:
        promote(sid, src, "rss", feed)
        return "PROMOTED", f"auto-discovered {feed} ({n} items)"
    return "UNRESOLVED", plan.get("needs") or plan.get("reason") or "no feed found"


def run_promote():
    import store, fetcher, extract as X
    db = store.connect(os.path.join(HERE, "radar.db"))
    reg, by = load_reg()
    cands = json.load(open(CAND))["candidates"]
    results = []
    for sid, plan in cands.items():
        src = by.get(sid)
        if not src: results.append((sid, "MISSING", "not in registry")); continue
        if plan.get("action") == "disable":
            src["enabled"] = False
            results.append((sid, "DISABLED", plan.get("reason", ""))); continue
        probe = lambda u, m, f, ml=None: _probe(u, m, f, db, X, fetcher, ml)
        discover = lambda u: _autodiscover(u, db, X, fetcher)
        st, detail = validate_plan(sid, src, plan, probe, discover)
        results.append((sid, st, detail))

    # NEW primary sources — created only after a live parse succeeds (same gate)
    existing = {s["id"] for s in reg["sources"]}
    for ns in json.load(open(CAND)).get("new_sources", []):
        sid = ns["id"]
        if sid in existing:
            results.append((sid, "SKIP-EXISTS", "already in registry")); continue
        probe = lambda u, m, f, ml=None: _probe(u, m, f, db, X, fetcher, ml)
        chosen = None
        for c in ns.get("try", []):
            n, msg = probe(c["url"], c["method"], c.get("frag"), c.get("min_len"))
            if n >= 1: chosen = (c["method"], c["url"], c.get("frag"), n, c.get("min_len")); break
        if not chosen:
            feed, n = _autodiscover(ns.get("page", ns.get("url","")), db, X, fetcher)
            if feed and n >= 1: chosen = ("rss", feed, None, n, None)
        if not chosen:
            results.append((sid, "UNRESOLVED-NEW", "no working feed — not created")); continue
        method, url, frag, n, min_len = chosen
        reg["sources"].append({
            "id": sid, "name": ns["name"], "url": url, "tier": ns.get("tier", 1),
            "country": ns.get("country", "Regional"), "category": ns.get("category", "health"),
            "method": method, "cadence_min": ns.get("cadence_min", 180),
            "lead_days": ns.get("lead_days", 2), "segments": ns.get("segments", ["city","bush","beach"]),
            "slots": ns.get("slots", ["morning","midday","evening"]),
            "why": ns.get("why", ""), "frag": frag or "", "min_len": min_len or 28, "enabled": True})
        results.append((sid, "CREATED", f"{method} {url} ({n} items)"))

    reg["updated"] = datetime.date.today().isoformat()
    save_reg(reg)
    write_report(results)
    for sid, st, msg in results: print(f"  {st:11} {sid:22} {msg}")
    promoted = sum(1 for _,s,_ in results if s=="PROMOTED")
    disabled = sum(1 for _,s,_ in results if s=="DISABLED")
    print(f"\n{promoted} promoted, {disabled} disabled, "
          f"{sum(1 for _,s,_ in results if s=='UNRESOLVED')} unresolved (headless/manual).")

def run_disables():
    reg, by = load_reg()
    cands = json.load(open(CAND))["candidates"]
    done = []
    for sid, plan in cands.items():
        if plan.get("action") == "disable" and by.get(sid):
            by[sid]["enabled"] = False; done.append(sid)
    save_reg(reg)
    print(f"Disabled {len(done)} redundant sources (safe, no network): {', '.join(done)}")

def write_report(results):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    by = {}
    for sid, st, msg in results: by.setdefault(st, []).append((sid, msg))
    L = [f"# Feed validation — {datetime.date.today().isoformat()}", ""]
    for st in ("PROMOTED", "DISABLED", "UNRESOLVED", "MISSING"):
        if st in by:
            L.append(f"## {st} ({len(by[st])})")
            for sid, msg in by[st]: L.append(f"- `{sid}` — {msg}")
            L.append("")
    open(OUT, "w").write("\n".join(L))

def run_report():
    cands = json.load(open(CAND))["candidates"]
    _, by = load_reg()
    buckets = {"has feed candidate": [], "disable (redundant)": [], "needs headless": [], "needs inspection": []}
    for sid, plan in cands.items():
        if plan.get("try"): buckets["has feed candidate"].append(sid)
        elif plan.get("action") == "disable": buckets["disable (redundant)"].append(sid)
        elif plan.get("needs") == "headless": buckets["needs headless"].append(sid)
        else: buckets["needs inspection"].append(sid)
    print(f"Feed remediation plan for {len(cands)} blind tier-1 sources (offline preview):\n")
    for k, v in buckets.items():
        print(f"  {k:22} {len(v):2}  {', '.join(v)}")
    print("\nAuto-discovery will ALSO be attempted for every source under --promote,")
    print("so 'needs inspection' entries may still self-heal if the page advertises a feed.")
    print("\nRun on a live-network runner:  python3 radar/validate_feeds.py --promote")


def run_probe_headless():
    """Diagnostic (non-mutating): render each 'try_headless' target on a live
    runner and report whether it yields items. Never writes registry.json. Its
    purpose is to tell us which JS-walled sources are worth wiring a production
    headless path for, and which are hopeless (session-gated, hard bot walls)."""
    import store, fetcher, extract as X
    try:
        import headless_fetch as HL
    except Exception as e:
        print("headless_fetch unavailable:", e); return
    if not HL.available():
        print("Playwright is not installed on this runner \u2014 nothing to probe.")
        print("Install with:  pip install playwright && python -m playwright install chromium")
        return
    cands = json.load(open(CAND))["candidates"]
    rows = []
    for sid, plan in cands.items():
        for t in plan.get("try_headless", []):
            url, ml = t["url"], t.get("min_len", 28)
            try:
                html = HL.render(url)
                n = len(X.extract_items(html, url, min_len=ml))
                rows.append((sid, n, "ok" if n >= 1 else "rendered, 0 items", url))
            except Exception as e:
                rows.append((sid, -1, f"{type(e).__name__}: {str(e)[:60]}", url))
    rows.sort(key=lambda r: (-r[1], r[0]))
    L = [f"# Headless probe \u2014 {datetime.date.today().isoformat()}",
         "", "Diagnostic only \u2014 registry NOT modified. Counts are items a rendered",
         "fetch would extract; >=1 means a production headless path is worth wiring.", ""]
    for sid, n, msg, url in rows:
        mark = "OK " if n >= 1 else ("0  " if n == 0 else "ERR")
        L.append(f"- [{mark}] `{sid}` ({n if n>=0 else 'x'}) \u2014 {msg} \u2014 {url}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(os.path.join(HERE, "out", "headless-probe.md"), "w").write("\n".join(L) + "\n")
    for sid, n, msg, url in rows:
        print(f"  {('OK ' if n>=1 else '0  ' if n==0 else 'ERR')} {sid:20} {msg}")
    ok = sum(1 for _, n, _, _ in rows if n >= 1)
    print(f"\n{ok}/{len(rows)} headless targets would yield items. Report: radar/out/headless-probe.md")


def main():
    if "--promote" in sys.argv: run_promote()
    elif "--probe-headless" in sys.argv: run_probe_headless()
    elif "--apply-disables" in sys.argv: run_disables()
    else: run_report()

if __name__ == "__main__":
    main()
