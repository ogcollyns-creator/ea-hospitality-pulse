#!/usr/bin/env python3
"""
Tell search engines a page changed, the moment it changes.

IndexNow is honoured by Bing, Yandex, Seznam, Naver and Yep. Bing's index feeds
ChatGPT search and Microsoft Copilot, so this is the fastest route into two of
the answer engines that were not citing the site. Google does not take IndexNow:
it reads sitemap.xml / sitemap-news.xml once the property is verified in Search
Console (set google_site_verification in site_config.json).

Sends every sitemap URL whose lastmod is within the last `--days` (default 2),
plus the home page, archive and topic hubs. Never fails the build.
"""
import os, re, sys, json, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "site_config.json"), encoding="utf-8"))
BASE = CFG.get("base", "https://eahospitalitypulse.com").rstrip("/")
KEY = CFG.get("indexnow_key")


def main():
    if not KEY:
        print("indexnow: no key configured, skipped"); return
    days = 2
    if "--days" in sys.argv:
        days = int(sys.argv[sys.argv.index("--days") + 1])
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    sm = open(os.path.join(HERE, "sitemap.xml"), encoding="utf-8").read()
    urls = [loc for loc, lm in re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", sm)
            if lm >= cutoff or "/topics/" in loc or loc.rstrip("/") in (BASE, BASE + "/archive")]
    urls = sorted(set(urls))[:10000]
    body = json.dumps({"host": BASE.split("//", 1)[1], "key": KEY,
                       "keyLocation": f"{BASE}/{KEY}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"indexnow: submitted {len(urls)} URLs, HTTP {r.status}")
    except Exception as e:
        print(f"indexnow: submission failed ({e}); {len(urls)} URLs not sent")


if __name__ == "__main__":
    main()
