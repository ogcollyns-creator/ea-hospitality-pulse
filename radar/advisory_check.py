#!/usr/bin/env python3
"""Advisory integrity — cross-check advisories.js against the live State Dept RSS.

The 4 Aug Tanzania error (board said US L2, source said L3 since Oct 2025) was a
maintenance miss no freshness check could catch — the file was 'recently updated',
just wrong. This fetches the working US Travel Advisories RSS (adv-us-ea) and
compares the level for each EA country to what the status board claims. A mismatch
is a hard finding. Runs where there is network (the daily self-audit workflow).

  python3 radar/advisory_check.py [--strict]
Exit 1 (with --strict) on any mismatch or if the source is unreachable.
"""
import os, re, sys
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.dirname(HERE)
sys.path.insert(0, HERE)
RSS="https://travel.state.gov/_res/rss/TAsTWs.xml"
COUNTRIES={"Kenya":"KE","Tanzania":"TZ","Uganda":"UG","Rwanda":"RW"}

def board_us():
    s=open(os.path.join(REPO,"advisories.js")).read(); out={}
    for m in re.finditer(r'code:"(\w+)".*?us:\{\s*level:\s*(\d)', s, re.S):
        out[m.group(1)]=int(m.group(2))
    return out

def source_levels():
    import store, fetcher, extract as X
    db=store.connect(os.path.join(HERE,"radar.db"))
    raw,h,furl=fetcher.fetch(db, RSS)
    items=X.parse_feed(raw); out={}
    for it in items:
        t=it.get("title","")
        for name,code in COUNTRIES.items():
            m=re.search(rf'{name}\s*[-–]\s*Level\s*(\d)', t)
            if m: out[code]=int(m.group(1))
    return out

def main():
    strict="--strict" in sys.argv
    board=board_us()
    try:
        src=source_levels()
    except Exception as e:
        print(f"⚠️  advisory source unreachable: {type(e).__name__}: {str(e)[:80]}")
        if strict: sys.exit(1)
        return
    if not src:
        print("⚠️  parsed 0 advisories from RSS — feed format may have changed")
        if strict: sys.exit(1)
        return
    bad=[]
    for code,lvl in src.items():
        b=board.get(code)
        flag = "OK" if b==lvl else "MISMATCH"
        if b!=lvl: bad.append((code,b,lvl))
        print(f"  {code}: board L{b}  source L{lvl}  {flag}")
    if bad:
        print("\n🔴 ADVISORY MISMATCH — update advisories.js:")
        for code,b,lvl in bad: print(f"   {code}: board says L{b}, State Dept says L{lvl}")
        if strict: sys.exit(1)
    else:
        print("\n🟢 Status board matches the State Department source.")

if __name__=="__main__": main()
