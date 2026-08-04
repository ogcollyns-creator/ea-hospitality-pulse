#!/usr/bin/env python3
"""Source coverage audit — find radar sources that are configured but mute.

Motivation: a source can be tier-1 and correctly registered yet never produce a
usable signal, because its index page isn't parseable into headline anchors and
scan_html falls back to a contentless "[page changed]" observation (see the
2026-08-04 US Embassy dengue miss). The live scan reports an aggregate obs count
and looks healthy while such a source is silently blind.

This audit needs no network. It classifies every source purely on ledger
evidence (radar/out/items.jsonl):
  HEALTHY  - has ever produced parsed item/doc rows
  MUTE     - has ONLY page-change rows (the blind fallback)
  SILENT   - has zero rows at all
and reports days since the source's most recent observation (staleness).

Usage:  python3 radar/audit_sources.py [--json] [--stale-days N]
"""
import json, time, sys, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REG  = os.path.join(HERE, "registry.json")
LED  = os.path.join(HERE, "out", "items.jsonl")

def load_sources():
    reg = json.load(open(REG))
    srcs = reg if isinstance(reg, list) else reg.get("sources", [])
    return {s["id"]: s for s in srcs if s.get("id")}

def load_ledger():
    by = collections.defaultdict(lambda: {"item":0,"doc":0,"page-change":0,"other":0,"last":0})
    if not os.path.exists(LED):
        return by
    for line in open(LED):
        try: r = json.loads(line)
        except: continue
        sid = r.get("source_id");  k = r.get("kind","other")
        if not sid: continue
        d = by[sid]
        d[k if k in ("item","doc","page-change") else "other"] += 1
        ts = r.get("first_seen_ts") or 0
        if ts and ts > d["last"]: d["last"] = ts
    return by

def classify(led):
    if led is None: return "SILENT"
    if led["item"] or led["doc"]: return "HEALTHY"
    if led["page-change"]: return "MUTE"
    return "SILENT"

def main():
    as_json = "--json" in sys.argv
    stale_days = 14
    if "--stale-days" in sys.argv:
        stale_days = int(sys.argv[sys.argv.index("--stale-days")+1])
    srcs = load_sources()
    led  = load_ledger()
    now  = time.time()
    rows = []
    for sid, s in srcs.items():
        d = led.get(sid)
        status = classify(d)
        last = d["last"] if d else 0
        age_d = round((now-last)/86400,1) if last else None
        rows.append({
            "id": sid, "tier": s.get("tier"), "country": s.get("country"),
            "category": s.get("category"), "method": s.get("method"),
            "has_frag": bool(s.get("frag")), "status": status,
            "items": (d["item"]+d["doc"]) if d else 0,
            "page_changes": d["page-change"] if d else 0,
            "age_days": age_d, "url": s.get("url"),
        })
    # criticality: tier-1 first, then MUTE/SILENT before stale-HEALTHY
    sev = {"SILENT":0, "MUTE":1, "HEALTHY":2}
    rows.sort(key=lambda r:(r["tier"] or 9, sev[r["status"]],
                            -(r["age_days"] or 0) if r["status"]=="HEALTHY" else 0))
    if as_json:
        print(json.dumps(rows, indent=1)); return
    tot = collections.Counter(r["status"] for r in rows)
    print(f"SOURCE COVERAGE AUDIT  ({len(rows)} sources)  ledger={os.path.basename(LED)}")
    print(f"  HEALTHY {tot['HEALTHY']}   MUTE {tot['MUTE']}   SILENT {tot['SILENT']}")
    print()
    def show(title, pred):
        sel = [r for r in rows if pred(r)]
        if not sel: return
        print(f"── {title} ({len(sel)}) " + "─"*max(0,40-len(title)))
        for r in sel:
            age = f"{r['age_days']}d" if r["age_days"] is not None else "never"
            print(f"  [T{r['tier']}] {r['id']:<26} {r['status']:<7} "
                  f"items={r['items']:<4} pc={r['page_changes']:<3} last={age:<7} {r['category']}")
        print()
    show("CRITICAL — tier-1 MUTE (blind fallback)", lambda r:r["tier"]==1 and r["status"]=="MUTE")
    show("CRITICAL — tier-1 SILENT (no data ever)", lambda r:r["tier"]==1 and r["status"]=="SILENT")
    show("WATCH — tier-1 HEALTHY but stale", lambda r:r["tier"]==1 and r["status"]=="HEALTHY" and (r["age_days"] or 0)>=stale_days)
    show("tier-2+ MUTE or SILENT", lambda r:(r["tier"] or 9)>1 and r["status"]!="HEALTHY")

if __name__ == "__main__":
    main()
