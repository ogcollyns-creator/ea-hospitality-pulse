"""Offline tests for the self-audit's pure logic (no repo state needed)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import self_audit as SA

def test_parse_date_forms():
    assert SA.parse_date("29 July 2026 (morning)").isoformat()=="2026-07-29"
    assert SA.parse_date("2026-08-03 14:01").isoformat()=="2026-08-03"
    assert SA.parse_date("no date here") is None

def test_signal_quality_warns_at_75pct():
    eds=[{"date":SA.TODAY,"slot":"morning","tier":2},
         {"date":SA.TODAY,"slot":"midday","tier":2},
         {"date":SA.TODAY,"slot":"evening","tier":3},
         {"date":SA.TODAY,"slot":"x","tier":1}]
    assert SA.check_signal_quality(eds)["status"]=="WARN"   # 3/4 = 75%

def test_signal_quality_fails_when_mostly_thin():
    eds=[{"date":SA.TODAY,"slot":str(i),"tier":2} for i in range(4)]+[{"date":SA.TODAY,"slot":"x","tier":1}]
    assert SA.check_signal_quality(eds)["status"]=="FAIL"   # 4/5 = 80%

def test_signal_quality_pass_when_rich():
    eds=[{"date":SA.TODAY,"slot":"m","tier":1},
         {"date":SA.TODAY,"slot":"d","tier":1},
         {"date":SA.TODAY,"slot":"e","tier":2}]
    assert SA.check_signal_quality(eds)["status"]=="PASS"

def test_source_coverage_fail_when_many_blind():
    rows=[{"id":f"s{i}","tier":1,"category":"advisory","status":"MUTE","age":1} for i in range(9)]
    rows+=[{"id":"ok","tier":1,"category":"x","status":"HEALTHY","age":1}]
    assert SA.check_source_coverage(rows)["status"]=="FAIL"

def test_source_coverage_pass_when_none_blind():
    rows=[{"id":"ok","tier":1,"category":"x","status":"HEALTHY","age":1}]
    assert SA.check_source_coverage(rows)["status"]=="PASS"

def test_run_returns_grade_and_checks():
    a=SA.run()
    assert set(["health","grade","checks","fails","warns"]).issubset(a)
    assert len(a["checks"])==10

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ",fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")
