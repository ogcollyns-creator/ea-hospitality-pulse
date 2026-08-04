"""Offline unit tests for the must-open escalation (no DB, no network).

Guards the 2026-08-04 regression: a tier-1 advisory page that moved but whose
content wasn't auto-parsed must surface as OPEN THIS and sort to the top."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import rank

def cand(**kw):
    d = dict(components={}, kind="item", tier=1, category="advisory",
             score=50, shock_terms=[], verdict=None)
    d.update(kw); return d

def test_tier1_advisory_pagechange_is_open_this():
    # the exact dengue shape: embassy alerts page moved, not parsed, low score
    c = cand(kind="page-change", category="advisory", tier=1, score=62)
    assert rank.assign_verdict(c).startswith("OPEN THIS"), rank.assign_verdict(c)

def test_tier1_health_pagechange_is_open_this():
    c = cand(kind="page-change", category="health", tier=1, score=40)
    assert rank.assign_verdict(c).startswith("OPEN THIS")

def test_tier2_pagechange_not_escalated():
    c = cand(kind="page-change", category="health", tier=2, score=80)
    assert not rank.assign_verdict(c).startswith("OPEN THIS")

def test_low_value_category_pagechange_not_escalated():
    c = cand(kind="page-change", category="research", tier=1, score=80)
    assert not rank.assign_verdict(c).startswith("OPEN THIS")

def test_covered_today_still_wins_over_escalation():
    c = cand(kind="page-change", category="advisory", tier=1,
             components={"already_covered": -80})
    assert rank.assign_verdict(c).startswith("DROP — covered today")

def test_stale_trap_still_wins_over_escalation():
    c = cand(kind="page-change", category="gazette", tier=1,
             components={"stale_trap": -60})
    assert rank.assign_verdict(c).startswith("DROP — stale trap")

def test_open_this_sorts_above_higher_scored_item():
    lead = cand(kind="page-change", category="advisory", tier=1, score=61)
    other = cand(kind="item", category="aviation", tier=1, score=96)
    cands = [other, lead]
    for c in cands: c["verdict"] = rank.assign_verdict(c)
    cands.sort(key=lambda c: (0 if c["verdict"].startswith(("OPEN THIS","LEAD")) else 1, -c["score"]))
    assert cands[0] is lead, "OPEN THIS must float above a higher-scored ordinary item"

def test_normal_strong_still_works():
    c = cand(kind="item", category="advisory", tier=1, score=95)
    assert rank.assign_verdict(c).startswith("STRONG")

if __name__ == "__main__":
    fns = [v for k,v in sorted(globals().items()) if k.startswith("test_")]
    passed=0
    for fn in fns:
        fn(); passed+=1; print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")
