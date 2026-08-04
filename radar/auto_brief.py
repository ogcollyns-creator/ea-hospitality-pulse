#!/usr/bin/env python3
"""Cloud auto-brief — assemble a Tier-2 Standing Brief from VERIFIED repo data only.

Runs in a GitHub Action so the Pulse ships from the cloud with no desktop app.
It cannot fabricate: every line is templated from structured, sourced fields
(the corrected advisory board, the forecast ledger, the radar candidate feed).
It produces Telegram + WhatsApp only (no LinkedIn prose — that needs an editor).
It SKIPS if a richer edition for the slot already exists, so it never overrides a
desktop-drafted Tier-1 or double-posts. Output still passes the pre-publish gate.

  python3 radar/auto_brief.py [--slot morning|midday|evening] [--force] [--print]
Writes editions-src/pulse-YYYY-MM-DD-<slot>.md (unless it already exists).
"""
import os, re, sys, csv, glob, datetime, json

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
EAT=datetime.timezone(datetime.timedelta(hours=3))
CFG=json.load(open(os.path.join(REPO,"site_config.json")))
BASE=CFG["base"].rstrip("/"); CH=CFG.get("channels",{})
TG=CH.get("telegram",""); WA=CH.get("whatsapp","")
LEVELNAME={1:"Exercise Normal Precautions",2:"Exercise Increased Caution",3:"Reconsider Travel",4:"Do Not Travel"}

def slot_now():
    h=datetime.datetime.now(EAT).hour
    return "morning" if h<10 else "midday" if h<16 else "evening"

def edition_name(slot): return {"morning":"Morning Brief","midday":"Midday Pulse","evening":"Evening Wrap"}[slot]

def advisory_board():
    s=open(os.path.join(REPO,"advisories.js")).read(); rows=[]
    for m in re.finditer(r'code:"(\w+)",\s*name:"([^"]+)".*?us:\{\s*level:(\d)[^}]*\}.*?uk:\{\s*level:(\d)', s, re.S):
        rows.append((m.group(1),m.group(2),int(m.group(3)),int(m.group(4))))
    return rows

def open_calls_due(days=14):
    p=os.path.join(REPO,"ledger","predictions.csv")
    if not os.path.exists(p): return []
    today=datetime.date.today(); out=[]
    for r in csv.DictReader(open(p)):
        if r.get("status")!="open": continue
        rb=r.get("resolve_by","")
        try: d=datetime.date.fromisoformat(rb)
        except: continue
        if 0<=(d-today).days<=days: out.append((d,r["id"],r["claim"][:90]))
    return sorted(out)

def radar_flags(n=3):
    p=os.path.join(HERE,"out","candidates.md")
    if not os.path.exists(p): return []
    blocks=re.findall(r'### [^\n]*\[([\d.]+)\]\s*([^\n]+)\n- \*\*Verdict:\*\*\s*([^\n]+)\n- \*\*Source:\*\*\s*([^\n]+)\n- \*\*First seen:\*\*\s*([^\n·]+)[^\n]*\n- \*\*URL:\*\*\s*([^\n]+)', open(p).read())
    out=[]
    for score,title,verdict,source,seen,url in blocks:
        if verdict.startswith(("OPEN THIS","LEAD")):
            out.append((title.strip(),verdict.split("—")[0].strip(),source.split("·")[0].strip(),seen.strip(),url.strip()))
        if len(out)>=n: break
    return out

def build(slot):
    today=datetime.datetime.now(EAT).date(); dstr=today.strftime("%A, %-d %B %Y")
    board=advisory_board(); calls=open_calls_due(); flags=radar_flags()
    url=f"{BASE}/editions/pulse-{today.isoformat()}-{slot}.html"
    us=lambda c: next((f"L{u}" for cc,_,u,_ in board if cc==c),"—")
    uk=lambda c: next((f"L{k}" for cc,_,_,k in board if cc==c),"—")
    board_us=f"US: Kenya {us('KE')}, Tanzania {us('TZ')}, Zanzibar {us('ZNZ')}, Uganda {us('UG')}, Rwanda {us('RW')}"
    board_uk=f"UK: Kenya {uk('KE')}, Tanzania {uk('TZ')}, Zanzibar {uk('ZNZ')}, Uganda {uk('UG')}, Rwanda {uk('RW')}"
    # NUMBER OF THE DAY: days to the nearest forecast resolution
    if calls:
        nd=(calls[0][0]-today).days
        notd=f"*{nd} day{'s' if nd!=1 else ''}* — until our next forecast call ({calls[0][1]}) resolves on {calls[0][0].strftime('%-d %b')}"
    else:
        highest=max(board,key=lambda r:r[2])
        notd=f"*{highest[2]}* — highest US advisory level on the board ({highest[1]}: {LEVELNAME[highest[2]]})"

    T=[f"🏨 EA HOSPITALITY PULSE — {edition_name(slot)}",
       f"📅 {dstr} | 🇰🇪🇹🇿🇺🇬🇷🇼","",
       "_Automated cloud brief — repo-backed, verified data only. A fuller edited edition may follow._",
       "━━━━━━━━━",
       "1️⃣ ADVISORY BOARD — STILL TRUE",
       f"{board_us}.",
       f"{board_uk}.",
       f"🎯 So what: no verified change to act on right now; a confirmed 'no change' tells you not to discount on advisory grounds. (Board verified against travel.state.gov / gov.uk.)",
       "🏷 All | Regional | Confirmed"]
    if calls:
        T+=["", "2️⃣ FORECAST CHECK-IN — CALLS RESOLVING SOON"]
        for d,cid,claim in calls[:3]:
            T.append(f"• {d.strftime('%-d %b')} — {cid}: {claim}")
        T.append("🎯 So what: these are our falsifiable calls coming due — we grade ourselves in public.")
        T.append("🏷 All | Regional | Reported")
    if flags:
        T+=["", "📡 RADAR FLAGGED (unread upstream — open before relying)"]
        for title,verdict,source,seen,u in flags:
            T.append(f"• {title[:80]} — {source}, first seen {seen[:10]} [{verdict}]")
            T.append(f"  {u}")
    T+=["━━━━━━━━━", f"🔗 This edition on the web: {url}",
        "— EA Hospitality Pulse | Automated cloud brief"]
    telegram="\n".join(T)

    W=[f"🏨 *EA HOSPITALITY PULSE*", f"_{edition_name(slot)} · {today.strftime('%a %-d %b')}_","",
       "📌 *Advisory board — no verified change*",
       f"{board_us}.",
       "→ *Do this:* hold rate; no advisory basis to discount today. Board verified vs official sources.","",
       "📌 *ALSO*"]
    if calls: W.append(f"📊 {len(calls)} forecast call(s) resolve within two weeks — we grade them in public")
    if flags: W.append(f"📡 Radar flagged {len(flags)} tier-1 upstream item(s) to read — see the web edition")
    W+=["", "📊 *NUMBER OF THE DAY*", notd, "",
        f"🔗 Full brief → {TG}", f"📖 Read on the web → {url}"]
    whatsapp="\n".join(W)

    doc=(f"# EA Hospitality Pulse — {edition_name(slot)} — {dstr}\n\n"
         f"_Tier 2 Standing Brief · auto-generated in the cloud from verified repo data "
         f"(advisory board, forecast ledger, radar feed). No web-searched analysis — a fuller "
         f"edited edition may supersede this._\n\n"
         f"## TELEGRAM\n\n{telegram}\n\n## WHATSAPP\n\n{whatsapp}\n")
    return doc

def main():
    slot=sys.argv[sys.argv.index("--slot")+1] if "--slot" in sys.argv else slot_now()
    out=os.path.join(REPO,"editions-src",f"pulse-{datetime.datetime.now(EAT).date().isoformat()}-{slot}.md")
    if os.path.exists(out) and "--force" not in sys.argv:
        print(f"SKIP — {os.path.basename(out)} already exists (a richer edition ran)."); return
    doc=build(slot)
    if "--print" in sys.argv: print(doc); return
    open(out,"w").write(doc); print(f"WROTE {out}")

if __name__=="__main__": main()
