#!/usr/bin/env python3
"""EA Pulse whole-pipeline self-audit — runs daily, grades effectiveness.

Motivation: two consecutive misses (a recycled advisory, then a missed US
Embassy dengue alert) shared a cause nobody was watching for — a subsystem
degrading silently while aggregate counters looked fine. This audit checks
EVERY moving part each day and fails loudly when any of them stops earning a
sensitive client's time.

Checks (each -> PASS / WARN / FAIL, weighted into a health score):
  1  source coverage        tier-1 sources that are MUTE or SILENT
  2  source staleness       tier-1 HEALTHY sources gone quiet
  3  radar feed freshness   newest observation age + in-window volume
  4  edition cadence        are slots actually being published
  5  signal quality         share of recent editions that were thin (Tier 2/3)
  6  ledger hygiene         overdue-open calls, missing sources, resolve rate
  7  data freshness         rules/costs/calendar/advisories/mice/pipeline age
  8  rate-index integrity   never expose a median with n<3 or confident=false
  9  forecast throughput    are we still making falsifiable calls

Offline by design: it audits the repo's own committed state, which is exactly
what a client sees. Network-dependent liveness (source reachability) stays in
scan.py health; this grades the record.

Usage:
  python3 radar/self_audit.py                # human report to stdout
  python3 radar/self_audit.py --json         # machine readable
  python3 radar/self_audit.py --write        # write radar/out/self-audit-latest.{md,json} + append history
  python3 radar/self_audit.py --strict       # exit 1 if any check FAILs (CI gate)
"""
import os, sys, re, json, csv, time, glob, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT  = os.path.join(HERE, "out")
EAT  = datetime.timezone(datetime.timedelta(hours=3))
NOW  = time.time()
TODAY = datetime.datetime.now(EAT).date()

MONTHS = {m:i for i,m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}

def parse_date(s):
    """'29 July 2026 (morning)' -> date(2026,7,29). Tolerant; None on failure."""
    if not s: return None
    m = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', s)
    if m and m.group(2).lower() in MONTHS:
        return datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m: return datetime.date(*map(int, m.groups()))
    return None

def R(name, status, detail, fix="", score=None):
    if score is None: score = {"PASS":1.0,"WARN":0.5,"FAIL":0.0}[status]
    return {"name":name, "status":status, "detail":detail, "fix":fix, "score":score}

# ---- shared: source classification (mirrors audit_sources.py) --------------
def source_coverage():
    reg = json.load(open(os.path.join(HERE,"registry.json")))
    srcs = reg if isinstance(reg,list) else reg.get("sources",[])
    srcs = {s["id"]:s for s in srcs if s.get("id")}
    led = collections.defaultdict(lambda:{"item":0,"doc":0,"pc":0,"last":0})
    p = os.path.join(OUT,"items.jsonl")
    if os.path.exists(p):
        for line in open(p):
            try: r=json.loads(line)
            except: continue
            sid=r.get("source_id");
            if not sid: continue
            k=r.get("kind"); d=led[sid]
            if k in ("item","doc"): d["item" if k=="item" else "doc"]+=1
            elif k=="page-change": d["pc"]+=1
            ts=r.get("first_seen_ts") or 0
            if ts>d["last"]: d["last"]=ts
    rows=[]
    for sid,s in srcs.items():
        d=led.get(sid)
        if d and (d["item"] or d["doc"]): st="HEALTHY"
        elif d and d["pc"]: st="MUTE"
        else: st="SILENT"
        age=(NOW-d["last"])/86400 if d and d["last"] else None
        rows.append({"id":sid,"tier":s.get("tier"),"category":s.get("category"),
                     "status":st,"age":age})
    return rows

# ---- checks -----------------------------------------------------------------
def check_source_coverage(rows):
    t1=[r for r in rows if r["tier"]==1]
    mute=[r for r in t1 if r["status"]=="MUTE"]
    silent=[r for r in t1 if r["status"]=="SILENT"]
    blind=len(mute)+len(silent)
    detail=(f"{len(t1)} tier-1 sources: {len(t1)-blind} HEALTHY, {len(mute)} MUTE, "
            f"{len(silent)} SILENT. Blind examples: "
            + ", ".join(r['id'] for r in (mute+silent)[:6]))
    fix="Give each blind tier-1 source an RSS/feed URL or frag selector; validate on the runner."
    if blind==0: return R("source coverage","PASS",detail)
    if blind<=5: return R("source coverage","WARN",detail,fix)
    return R("source coverage","FAIL",detail,fix)

def check_source_staleness(rows):
    stale=[r for r in rows if r["tier"]==1 and r["status"]=="HEALTHY" and (r["age"] or 0)>=14]
    if not stale: return R("source staleness","PASS","No tier-1 HEALTHY source silent >14d.")
    detail=f"{len(stale)} tier-1 HEALTHY sources quiet >14d: "+", ".join(r['id'] for r in stale[:8])
    return R("source staleness","WARN" if len(stale)<=6 else "FAIL",detail,
             "Confirm the source still publishes; fix URL if it moved.")

def check_feed_freshness():
    p=os.path.join(OUT,"candidates.md")
    if not os.path.exists(p): return R("radar feed freshness","FAIL","candidates.md missing.","Run radar/rank.py.")
    txt=open(p).read()
    obs=re.search(r'(\d+)\s+observations in window',txt)
    seen=[datetime.datetime.fromisoformat(m) for m in re.findall(r'First seen:\*\*\s*([0-9T:\-+]+)',txt)]
    n=int(obs.group(1)) if obs else 0
    if not seen:
        return R("radar feed freshness","WARN",f"{n} obs in window but no first-seen stamps parsed.","")
    newest=max(seen); age_h=(datetime.datetime.now(EAT)-newest).total_seconds()/3600
    detail=f"{n} in-window obs; newest observation {age_h:.1f}h old ({newest.isoformat()})."
    if age_h<=6 and n>=20: return R("radar feed freshness","PASS",detail)
    if age_h<=12: return R("radar feed freshness","WARN",detail,"Top up with a bounded scan before the edition.")
    return R("radar feed freshness","FAIL",detail,"Radar pipeline may be down — check scan workflow.")

def _editions():
    out=[]
    for p in sorted(glob.glob(os.path.join(REPO,"editions-src","pulse-*.md"))):
        b=os.path.basename(p)
        m=re.match(r'pulse-(\d{4}-\d{2}-\d{2})-(\w+)\.md',b)
        if not m: continue
        d=datetime.date.fromisoformat(m.group(1)); slot=m.group(2)
        head=open(p).read()[:600]
        tm=re.search(r'Tier\s*([123])',head)
        out.append({"date":d,"slot":slot,"tier":int(tm.group(1)) if tm else None})
    return out

def check_cadence(eds):
    recent=[e for e in eds if (TODAY-e["date"]).days<=2]
    got={(e["date"],e["slot"]) for e in recent}
    # expected: morning+midday+evening for each of the last 2 full days
    missing=[]
    for dd in [TODAY-datetime.timedelta(days=1), TODAY-datetime.timedelta(days=2)]:
        for slot in ("morning","midday","evening"):
            if (dd,slot) not in got: missing.append(f"{dd} {slot}")
    if not missing: return R("edition cadence","PASS",f"{len(recent)} editions in last 2d; no slot gaps.")
    return R("edition cadence","WARN" if len(missing)<=2 else "FAIL",
             f"Missing slots (last 2 full days): {', '.join(missing)}",
             "Confirm the scheduled Pulse task fired for each slot.")

def check_signal_quality(eds):
    wk=[e for e in eds if (TODAY-e["date"]).days<=7 and e["tier"]]
    if len(wk)<3: return R("signal quality","WARN",f"Only {len(wk)} tier-tagged editions in 7d — too few to judge.","")
    thin=[e for e in wk if e["tier"] in (2,3)]
    share=len(thin)/len(wk)
    detail=f"{len(thin)}/{len(wk)} editions in last 7d were Tier 2/3 (thin). Share {share:.0%}."
    fix="A high thin share means sourcing isn't finding real stories — widen scope / fix blind sources."
    if share<=0.5: return R("signal quality","PASS",detail)
    if share<=0.75: return R("signal quality","WARN",detail,fix)
    return R("signal quality","FAIL",detail,fix)

def check_ledger():
    p=os.path.join(REPO,"ledger","predictions.csv")
    if not os.path.exists(p): return R("ledger hygiene","FAIL","predictions.csv missing.","")
    rows=list(csv.DictReader(open(p)))
    openc=[r for r in rows if r.get("status")=="open"]
    overdue=[r for r in openc if r.get("resolve_by") and parse_date(r["resolve_by"]) and parse_date(r["resolve_by"])<TODAY]
    nosrc=[r for r in rows if not r.get("source_url","").strip()]
    resolved=[r for r in rows if r.get("status") in ("correct","incorrect","partial")]
    detail=(f"{len(rows)} calls: {len(openc)} open, {len(resolved)} resolved. "
            f"Overdue-open: {len(overdue)}. Missing source_url: {len(nosrc)}.")
    fix=""
    if overdue: fix+=f"Resolve overdue calls now: {', '.join(r['id'] for r in overdue[:8])}. "
    if len(nosrc)>len(rows)*0.25: fix+="Backfill source_url on early calls."
    if overdue: return R("ledger hygiene","FAIL",detail,fix)
    if len(nosrc)>len(rows)*0.25: return R("ledger hygiene","WARN",detail,fix)
    return R("ledger hygiene","PASS",detail)

def check_data_freshness():
    limits={"advisories.js":4,"costs.js":10,"rules.js":21,"calendar.js":21,
            "mice.js":14,"pipeline.js":21}
    stale=[]
    for f,lim in limits.items():
        p=os.path.join(REPO,f)
        if not os.path.exists(p): stale.append(f"{f}(missing)"); continue
        m=re.search(r'updated:\s*"([^"]+)"',open(p).read())
        d=parse_date(m.group(1)) if m else None
        if d is None: stale.append(f"{f}(no date)"); continue
        age=(TODAY-d).days
        if age>lim: stale.append(f"{f} {age}d>{lim}")
    if not stale: return R("data freshness","PASS","All tracked data files within their freshness limits.")
    return R("data freshness","WARN" if len(stale)<=3 else "FAIL",
             "Stale/again-verify: "+", ".join(stale),
             "Re-verify each dataset's values and bump its 'updated:' field, or note it in-edition.")

def check_rate_index():
    p=os.path.join(REPO,"rates.js")
    if not os.path.exists(p): return R("rate-index integrity","PASS","No rates.js yet — nothing to mis-publish.")
    txt=open(p).read()
    ns=[int(x) for x in re.findall(r'"?n"?\s*:\s*(\d+)',txt)]
    thin = ns and min(ns)<3
    confT = len(re.findall(r'"confident"\s*:\s*true', txt)); confF = len(re.findall(r'"confident"\s*:\s*false', txt))
    detail=f"n values seen: {sorted(set(ns))[:6] or 'none'}; confident true={confT} false={confF}."
    if thin or confF:
        return R("rate-index integrity","WARN",detail,
                 "Index still thin — never quote a median where n<3 or confident:false. Enforced in copy.")
    return R("rate-index integrity","PASS",detail)

def check_forecast_throughput():
    p=os.path.join(REPO,"ledger","predictions.csv")
    rows=list(csv.DictReader(open(p))) if os.path.exists(p) else []
    recent=[r for r in rows if parse_date(r.get("made_date","")) and (TODAY-parse_date(r["made_date"])).days<=7]
    detail=f"{len(recent)} new falsifiable calls logged in last 7d."
    if len(recent)>=3: return R("forecast throughput","PASS",detail)
    if len(recent)>=1: return R("forecast throughput","WARN",detail,"Log more falsifiable calls — the ledger is the moat.")
    return R("forecast throughput","FAIL",detail,"No new calls in a week — the differentiator is going cold.")

def check_published_content():
    """Re-verify recent published editions against the current status board."""
    try:
        import content_audit
        files, conflicts = content_audit.find_conflicts(days=3)
    except Exception as e:
        return R("published content","WARN",f"content audit unavailable: {e}")
    if not conflicts:
        return R("published content","PASS",f"{len(files)} recent editions; no advisory claim contradicts the board.")
    ex="; ".join(f"{f.split('pulse-')[-1][:-3]} {c} L{p}->L{cur}" for f,c,_,p,cur,_ in conflicts[:4])
    return R("published content","FAIL",
             f"{len(conflicts)} published claim(s) now contradicted: {ex}",
             "Publish a correction and fix advisories.js; a live edition is stating a wrong level.")

WEIGHTS={"source coverage":2.0,"radar feed freshness":2.0,"signal quality":2.0,
         "ledger hygiene":1.5,"edition cadence":1.5,"data freshness":1.0,
         "source staleness":1.0,"rate-index integrity":1.0,"forecast throughput":1.0,"published content":2.0}

def run():
    rows=source_coverage(); eds=_editions()
    checks=[check_source_coverage(rows),check_source_staleness(rows),
            check_feed_freshness(),check_cadence(eds),check_signal_quality(eds),
            check_ledger(),check_data_freshness(),check_rate_index(),
            check_forecast_throughput(),check_published_content()]
    tw=sum(WEIGHTS.get(c["name"],1) for c in checks)
    score=sum(c["score"]*WEIGHTS.get(c["name"],1) for c in checks)/tw
    grade="A" if score>=.9 else "B" if score>=.75 else "C" if score>=.6 else "D" if score>=.4 else "F"
    return {"generated":datetime.datetime.now(EAT).isoformat(timespec="minutes"),
            "health":round(score,3),"grade":grade,
            "fails":[c["name"] for c in checks if c["status"]=="FAIL"],
            "warns":[c["name"] for c in checks if c["status"]=="WARN"],
            "checks":checks}

def to_md(a):
    ic={"PASS":"🟢","WARN":"🟡","FAIL":"🔴"}
    L=[f"# EA Pulse self-audit — {a['generated']} EAT",
       f"**Health {a['health']:.0%} · grade {a['grade']}** — "
       f"{len(a['fails'])} FAIL, {len(a['warns'])} WARN, "
       f"{sum(1 for c in a['checks'] if c['status']=='PASS')} PASS","",
       "| | Check | Status | Detail |","|-|-|-|-|"]
    for c in a["checks"]:
        L.append(f"| {ic[c['status']]} | {c['name']} | {c['status']} | {c['detail']} |")
    L.append("")
    acts=[c for c in a["checks"] if c["status"]!="PASS" and c["fix"]]
    if acts:
        L.append("## Actions")
        for c in sorted(acts,key=lambda c:c['status']):
            L.append(f"- **{c['name']}** ({c['status']}): {c['fix']}")
    return "\n".join(L)

def main():
    a=run()
    if "--json" in sys.argv:
        print(json.dumps(a,indent=1))
    else:
        print(to_md(a))
    if "--write" in sys.argv:
        os.makedirs(OUT,exist_ok=True)
        open(os.path.join(OUT,"self-audit-latest.md"),"w").write(to_md(a))
        json.dump(a,open(os.path.join(OUT,"self-audit-latest.json"),"w"),indent=1)
        with open(os.path.join(OUT,"self-audit-history.csv"),"a") as h:
            if h.tell()==0: h.write("generated,health,grade,fails,warns\n")
            h.write(f"{a['generated']},{a['health']},{a['grade']},"
                    f"{'|'.join(a['fails'])},{'|'.join(a['warns'])}\n")
    if "--strict" in sys.argv and a["fails"]:
        sys.exit(1)

if __name__=="__main__":
    main()
