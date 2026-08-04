"""Offline tests: promotion only happens on a successful live parse; disables are safe."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import validate_feeds as V

def src(**kw):
    d=dict(id="x", url="https://example.com/news", method="html", frag="", enabled=True); d.update(kw); return d

def test_promote_on_working_feed():
    s=src()
    probe=lambda u,m,f:(5,"ok")           # feed parses -> 5 items
    disc=lambda u:(None,0)
    st,_=V.validate_plan("x", s, {"try":[{"method":"rss","url":"https://example.com/feed"}]}, probe, disc)
    assert st=="PROMOTED"
    assert s["method"]=="rss" and s["url"]=="https://example.com/feed"

def test_no_promote_when_feed_empty():
    s=src(); before=dict(s)
    probe=lambda u,m,f:(0,"ok")           # feed returns 0 items -> reject
    disc=lambda u:(None,0)
    st,_=V.validate_plan("x", s, {"try":[{"method":"rss","url":"https://example.com/feed"}],"needs":"headless"}, probe, disc)
    assert st=="UNRESOLVED"
    assert s["method"]==before["method"] and s["url"]==before["url"]   # untouched

def test_no_promote_when_fetch_fails():
    s=src(); before=dict(s)
    probe=lambda u,m,f:(-1,"fetch failed")
    disc=lambda u:(None,0)
    st,_=V.validate_plan("x", s, {"try":[{"method":"rss","url":"https://x/feed"}]}, probe, disc)
    assert st=="UNRESOLVED"
    assert s==before

def test_autodiscovery_promotes():
    s=src()
    probe=lambda u,m,f:(-1,"no explicit try")
    disc=lambda u:("https://example.com/auto.xml", 3)
    st,_=V.validate_plan("x", s, {"try":[]}, probe, disc)
    assert st=="PROMOTED" and s["method"]=="rss" and s["url"]=="https://example.com/auto.xml"

def test_disable_action_is_offline_and_disables():
    s=src()
    st,_=V.validate_plan("x", s, {"action":"disable","reason":"redundant"}, None, None)
    assert st=="DISABLED" and s["enabled"] is False

def test_first_working_candidate_wins():
    s=src(); calls=[]
    def probe(u,m,f):
        calls.append(u); return (2,"ok") if u.endswith("b") else (0,"ok")
    st,_=V.validate_plan("x", s, {"try":[
        {"method":"rss","url":"https://x/a"},{"method":"rss","url":"https://x/b"}]}, probe, lambda u:(None,0))
    assert st=="PROMOTED" and s["url"]=="https://x/b"

# --- config integrity for refined candidates + new primary sources ---
def test_new_sources_wellformed():
    import json, os
    d=json.load(open(os.path.join(os.path.dirname(__file__),"..","feed_candidates.json")))
    for ns in d.get("new_sources", []):
        for k in ("id","name","tier","country","category","try"):
            assert k in ns, (ns.get("id"), k)
        for t in ns["try"]:
            assert t["method"] in ("rss","html") and t["url"].startswith("http")

def test_candidates_have_action_try_or_needs():
    import json, os
    d=json.load(open(os.path.join(os.path.dirname(__file__),"..","feed_candidates.json")))
    for sid,plan in d["candidates"].items():
        assert plan.get("try") or plan.get("action") or plan.get("needs"), sid

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ",fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")