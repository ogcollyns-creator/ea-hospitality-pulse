# Feed validation — 2026-08-05

## PROMOTED (11)
- `who-don` — rss https://www.who.int/rss-feeds/news-english.xml (25 items)
- `us-fedreg-cdc` — rss https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bagencies%5D%5B%5D=centers-for-disease-control-and-prevention&order=newest (25 items)
- `air-ug` — html https://www.ugandairlines.com/news (1 items)
- `ug-moh` — rss https://health.go.ug/feed/ (10 items)
- `ke-gazettes-africa` — html https://gazettes.africa/gazettes/ke (2 items)
- `ug-gazette` — html https://gazettes.africa/gazettes/ug (2 items)
- `tz-gazette` — html https://gazettes.africa/gazettes/tz (2 items)
- `rw-gazette` — html https://gazettes.africa/gazettes/rw (2 items)
- `tz-tanapa` — html https://www.tanzaniaparks.go.tz/ (1 items)
- `zn-zrb` — html https://www.zrb.go.tz/ (1 items)
- `ug-ucaa` — html https://caa.go.ug/ (18 items)

## DISABLED (4)
- `adv-us-kenya` — Redundant: covered by adv-us-ea RSS (travel.state.gov/_res/rss/TAsTWs.xml), which already works. The rendered HTML page is a JS shell that yields nothing.
- `adv-us-uganda` — Redundant: covered by adv-us-ea RSS.
- `adv-us-tanzania` — Redundant: covered by adv-us-ea RSS.
- `adv-us-rwanda` — Redundant: covered by adv-us-ea RSS.

## UNRESOLVED (28)
- `ke-usembassy-alerts` — headless
- `ug-mediacentre` — headless
- `cdc-travel-notices` — browser-fetch
- `sm-unwto` — deprioritise
- `sm-wttc` — deprioritise
- `dev-marriott` — browser-fetch
- `dev-kempinski` — browser-fetch
- `rw-visitrwanda` — headless
- `air-jambojet` — headless
- `air-precision` — headless
- `air-airlink` — headless
- `air-tc` — headless
- `air-tk` — headless
- `adv-au-kenya` — headless
- `adv-au-tanzania` — headless
- `osac-kenya` — headless
- `ke-epra-press` — headless
- `ke-epra-fuel` — headless
- `ke-tenders` — headless
- `tz-tenders` — headless
- `ke-kaa-tenders` — inspect | tries: html n=-1 fetch failed: FetchError: HTTP 404
- `ug-bou` — headless
- `rw-bnr` — headless
- `tz-mnrt` — headless
- `tz-immigration` — headless
- `zn-moh` — headless
- `zn-ocgs` — inspect | tries: html n=-1 fetch failed: FetchError: RemoteDisconnected: Remote end closed connection without res
- `zn-tourism` — inspect | tries: html n=-1 fetch failed: FetchError: URLError: timed out
