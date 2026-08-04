"""Offline tests for the pre-publish quality gate."""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import prepublish_gate as G

GOOD = """# E
## TELEGRAM
Body with link {BASE}/editions/x.html
## WHATSAPP
top. NUMBER OF THE DAY: *2* things. more words to pad the count so the warn does not fire here okay good enough now yes.
## LINKEDIN
A clean body with no links at all here.

We track this daily at EA Hospitality Pulse.

#Hospitality #Kenya #TravelRisk #MICE

### FIRST COMMENT
{BASE}/editions/x.html
""".replace("{BASE}", G.BASE)

def _w(txt):
    f=tempfile.NamedTemporaryFile("w",suffix=".md",delete=False); f.write(txt); f.close(); return f.name

def test_good_edition_passes():
    b,w,_,_=G.check(_w(GOOD), do_fix=False)
    assert b==[], b

def test_missing_number_of_day_blocks():
    b,_,_,_=G.check(_w(GOOD.replace("NUMBER OF THE DAY: *2*","just text")), do_fix=False)
    assert any("NUMBER OF THE DAY" in x for x in b)

def test_three_hashtags_blocks():
    b,_,_,_=G.check(_w(GOOD.replace(" #MICE","")), do_fix=False)
    assert any("hashtags" in x for x in b)

def test_url_in_linkedin_body_blocks_without_fix():
    bad=GOOD.replace("no links at all here.","a link https://x.com/t here.")
    b,_,_,_=G.check(_w(bad), do_fix=False)
    assert any("URL(s) in post body" in x for x in b)

def test_url_in_body_autofixed():
    bad=GOOD.replace("no links at all here.","a link https://x.com/t here.")
    p=_w(bad); b,w,_,fixes=G.check(p, do_fix=True)
    assert not any("URL(s) in post body" in x for x in b), b
    assert "https://x.com/t" not in open(p).read()

def test_missing_first_comment_autofixed():
    bad=GOOD.split("### FIRST COMMENT")[0]
    p=_w(bad); b,w,_,fixes=G.check(p, do_fix=True)
    assert "### FIRST COMMENT" in open(p).read()

def test_placeholder_blocks():
    b,_,_,_=G.check(_w(GOOD.replace("clean body","clean body TODO finish this")), do_fix=False)
    assert any("placeholder" in x for x in b)

def test_missing_telegram_blocks():
    b,_,_,_=G.check(_w(GOOD.replace("## TELEGRAM","## NOPE")), do_fix=False)
    assert any("TELEGRAM" in x for x in b)

if __name__=="__main__":
    fns=[v for k,v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns: fn(); print("  ok ",fn.__name__)
    print(f"\n{len(fns)}/{len(fns)} passed")
