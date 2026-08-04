#!/usr/bin/env python3
"""Post-publish content audit — re-check what we already shipped against current truth.

Catches the 4 Aug failure: Tanzania was published at US Level 2 in the morning AND
midday editions while the real level had been 3 since 31 Oct 2025, and nothing
flagged the live editions for hours. A brief is a claim that stays on the record;
this re-reads recent editions and flags advisory-level claims that contradict the
current status board (advisories.js), respecting US-vs-UK context so it is precise.

  python3 radar/content_audit.py [--days 3] [--strict]
"""
import os, re, sys, glob, datetime

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
NAME2CODE={"kenya":"KE","tanzania":"TZ","zanzibar":"ZNZ","uganda":"UG","rwanda":"RW",
           "ke":"KE","tz":"TZ","znz":"ZNZ","ug":"UG","rw":"RW"}

def board_levels():
    """{code: {'us':N,'uk':M}} from advisories.js."""
    s=open(os.path.join(REPO,"advisories.js")).read(); out={}
    for m in re.finditer(r'code:"(\w+)".*?us:\{\s*level:\s*(\d).*?uk:\{\s*level:\s*(\d)', s, re.S):
        out[m.group(1)]={"us":int(m.group(2)),"uk":int(m.group(3))}
    return out

# one regex that matches EITHER a context marker OR a country-level claim, in order
TOKEN=re.compile(
    r'(?P<ctx>\b(?:U\.?S\.?|American)\s*:|\bUK\s*:|\bBritish\s*:)'
    r'|(?P<c>Kenya|Tanzania|Zanzibar|Uganda|Rwanda|KE|TZ|ZNZ|UG|RW)'
    r'\s*(?:/\s*(?P<c2>Zanzibar|ZNZ))?\s*[-–:]?\s*(?:Level\s*|L)\s*(?P<lvl>[1-4])\b')

def claims_in(text):
    ctx="us"  # default: unmarked advisory mentions are US
    for m in TOKEN.finditer(text):
        if m.group("ctx"):
            ctx = "uk" if m.group("ctx").upper().startswith(("UK","BRIT")) else "us"; continue
        code=NAME2CODE.get(m.group("c").lower()); lvl=int(m.group("lvl"))
        snip=text[max(0,m.start()-24):m.end()+8].replace("\n"," ").strip()
        if code: yield code, ctx, lvl, snip
        if m.group("c2"):
            c2=NAME2CODE.get(m.group("c2").lower())
            if c2: yield c2, ctx, lvl, snip

def find_conflicts(days=3):
    board=board_levels(); today=datetime.date.today()
    files=[p for p in sorted(glob.glob(os.path.join(REPO,"editions-src","pulse-*.md")))
           if (m:=re.search(r'(\d{4}-\d{2}-\d{2})',os.path.basename(p))) and
              (today-datetime.date.fromisoformat(m.group(1))).days<=days]
    conflicts=[]  # (file, code, CTX, published, current, snippet)
    for p in files:
        seen=set()
        for code,ctx,lvl,snip in claims_in(open(p).read()):
            cur=board.get(code,{}).get(ctx)
            if cur is not None and lvl!=cur and (code,ctx,lvl) not in seen:
                seen.add((code,ctx,lvl))
                conflicts.append((os.path.basename(p),code,ctx.upper(),lvl,cur,snip))
    return files, conflicts

def main():
    days=int(sys.argv[sys.argv.index("--days")+1]) if "--days" in sys.argv else 3
    strict="--strict" in sys.argv
    files, conflicts = find_conflicts(days)
    print(f"CONTENT AUDIT — {len(files)} editions in last {days}d vs current board")
    if not conflicts:
        print("  🟢 No published advisory claim contradicts the current status board.")
    else:
        print(f"  🔴 {len(conflicts)} published claim(s) now contradicted — correction needed:")
        for f,code,ctx,pub,cur,snip in conflicts:
            print(f"   {f}: {ctx} {code} published L{pub}, board now L{cur}  «{snip[:60]}»")
    if strict and conflicts: sys.exit(1)
    return conflicts

if __name__=="__main__": main()
