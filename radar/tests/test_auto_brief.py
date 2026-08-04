"""Offline tests for the cloud auto-brief — verified data only, gate-compliant."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import auto_brief as A

def test_has_required_sections():
    d=A.build("morning")
    assert "## TELEGRAM" in d and "## WHATSAPP" in d
    assert "NUMBER OF THE DAY" in d

def test_board_matches_source_of_truth():
    # the brief must reflect the CURRENT corrected board, never a stale number
    d=A.build("evening")
    assert "Tanzania L3" in d and "Zanzibar L3" in d and "Kenya L2" in d and "Uganda L4" in d

def test_labeled_as_standing_brief_not_analysis():
    d=A.build("midday")
    assert "Tier 2 Standing Brief" in d and "verified" in d.lower()

def test_slot_names():
    assert A.edition_name("evening")=="Evening Wrap"

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ",fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")
