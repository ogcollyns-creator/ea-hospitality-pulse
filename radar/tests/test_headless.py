"""Offline tests for the gated production headless path. No browser required:
every assertion covers the inert / wiring behaviour that must hold on a normal
runner where Playwright is absent."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import scan, extract as X

def _src(**kw):
    d = dict(id="x", name="X", url="https://example.com/news", method_hint="headless",
             frag="", min_len=12, etag="E", last_modified="L", content_hash="H")
    d.update(kw); return d

def test_scanners_include_headless():
    assert "headless" in scan.SCANNERS and scan.SCANNERS["headless"] is scan.scan_headless

def test_negotiate_returns_headless_for_hint():
    m, feed = scan.negotiate(None, _src(), b"<html></html>", {}, "https://example.com/news")
    assert m == "headless"

def test_scan_headless_inert_when_flag_off():
    os.environ.pop("RADAR_HEADLESS", None)
    new, etag, lm, chash = scan.scan_headless(None, _src(), None)
    assert new == 0 and etag == "E" and lm == "L" and chash == "H"   # no change reported

def test_scan_headless_inert_without_playwright():
    os.environ["RADAR_HEADLESS"] = "1"
    try:
        # Playwright is not installed in this test env -> HL.available() False -> no-op
        new, etag, lm, chash = scan.scan_headless(None, _src(), None)
        assert new == 0 and chash == "H"
    finally:
        os.environ.pop("RADAR_HEADLESS", None)

if __name__ == "__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ", fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")
