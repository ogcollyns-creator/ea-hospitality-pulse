"""Offline tests for the post-publish content audit (US/UK context precision)."""
import os, sys, tempfile, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import content_audit as C

def test_us_context_mismatch_flagged():
    claims=list(C.claims_in("US: Kenya L2, Tanzania/Zanzibar L2, Uganda L4"))
    d={(c,ctx):l for c,ctx,l,_ in claims}
    assert d[("TZ","us")]==2 and d[("ZNZ","us")]==2 and d[("KE","us")]==2

def test_uk_context_not_confused_with_us():
    claims=list(C.claims_in("US: Tanzania L3. UK: Tanzania L1"))
    got={(c,ctx):l for c,ctx,l,_ in claims}
    assert got[("TZ","us")]==3 and got[("TZ","uk")]==1

def test_unmarked_defaults_to_us():
    claims=list(C.claims_in("Tanzania L3 confirmed this week"))
    assert ("TZ","us",3) in [(c,ctx,l) for c,ctx,l,_ in claims]

def test_board_parse_reads_us_and_uk():
    b=C.board_levels()
    assert b["TZ"]["us"]==3 and b["KE"]["us"]==2   # reflects corrected board

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ",fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")
