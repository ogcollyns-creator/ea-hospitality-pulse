# Approved photo sources

Photographs are the exception, not the default. Most editions lead with a data card
(`hero_extra.py --data-card`). Reach for a photograph only when the story has a genuine
visual subject — a named property, park, aircraft, ceremony or venue. Never to fill a slot.

## Approved — publish freely, credit as shown

| Source | Use | Credit line |
|---|---|---|
| Kenya Tourism Board / Magical Kenya media centre | Kenya destinations, KTB events | `Kenya Tourism Board` |
| Rwanda Development Board / Visit Rwanda media library | Rwanda, Kwita Izina, Volcanoes | `Rwanda Development Board` |
| Tanzania Tourist Board | Tanzania mainland, parks | `Tanzania Tourist Board` |
| Zanzibar Commission for Tourism | Zanzibar, Stone Town | `Zanzibar Commission for Tourism` |
| KWS · UWA · TANAPA · NCAA | Parks, wildlife, fee stories | e.g. `Uganda Wildlife Authority` |
| Marriott · Accor · Hilton · Radisson · Kempinski newsrooms | Property and signing stories | e.g. `Marriott International` |
| Kenya Airways · RwandAir · Uganda Airlines · Air Tanzania media kits | Route and fleet stories | e.g. `RwandAir` |
| WHO · Africa CDC | Outbreak and health stories | `WHO` / `Africa CDC` |

These bodies publish images expressly for editorial reuse and *want* them republished.
For our stories — which are about named properties, parks, airlines and agencies — they
are also a far better match than any wire photo.

## Not approved

- **Press-agency and news-outlet photography** (AFP, Reuters, AP, Getty, Citizen TV,
  Nation Media). Attribution is not a licence, and a "courtesy" credit on an unlicensed
  agency photo documents that we knew whose it was. Not used, regardless of credit.
- **Hot-linking any third party's image URL.** It serves someone else's bandwidth and
  breaks the moment they move the file. Five such entries were removed from
  `editorial-picks.json` on 28 Aug 2026.
- **Wikimedia Commons**, retired 28 Aug 2026. Not a licensing problem — a relevance one.
  It supplied regional scenery unrelated to the story: an edition on Zanzibar package
  yield was topped with a baby elephant in the Serengeti.

## Adding an image

1. Download from the source's own media library (do not hot-link).
2. Save to `img/press-kit/<slug>.jpg`.
3. Add an entry to `registry.json` with `artist`, `source`, `descurl`, `license`,
   `grant` (where the permission comes from) and `tags`.
4. `python3 hero_extra.py --press-kit` assigns it to any matching edition.
