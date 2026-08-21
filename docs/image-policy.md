# EA Hospitality Pulse — Image Sourcing & Attribution Policy

The golden rule: **a credit line is not a licence.** Attribution satisfies one
condition of *some* licences; it does not grant permission. Most images online are
"all rights reserved" copyright, and crediting them does not make reuse lawful —
publishers get billed for exactly this (Getty / PicRights / Pixsy). We only publish
an image when its **licence** permits the use; the credit is on top of that, not
instead of it. (This is operational guidance, not legal advice.)

## Approved sources (only these)

1. **CC0 / public domain** — Wikimedia Commons (PD), Unsplash, Pexels, Pixabay.
   Credit optional but we still show it.
1b. **Openverse** (openverse.org) — a broad aggregator of CC0 / public-domain /
   CC-BY / BY-SA images from Flickr, Wikimedia, museums, Rawpixel, Nappy and more.
   Filtered to commercial-safe licences only (no NC/ND). Each result carries creator,
   source and licence, rendered in the credit as `Openverse · <source>`.
2. **Creative Commons BY / BY-SA** — Wikimedia Commons, Flickr Creative Commons.
   Reusable commercially **with correct attribution** (BY-SA also requires share-alike).
3. **Tourism-board / brand press kits** — official destination and hotel-group media
   libraries. Great relevance, but **read each kit's terms**: many licence images only
   for editorial use or only to promote that destination. Log the grant.
4. **AI-generated** — a bespoke image with no third-party rights. Label as illustrative;
   never imply it is a photograph of a real, named place or event where that would mislead.

## Never use

- **CC "NC" (non-commercial)** — the Pulse is a commercial product.
- **CC "ND" (no-derivatives)** — we crop and overlay branding.
- **News / wire photos** (Reuters, AP, AFP, getty editorial) — licensed, never free.
- **Other hotels' or operators' marketing photos**, or anything off **Google Images**
  without tracing it to a licence.

## Attribution format (TASL)

`Title — Author — Source (link) — Licence (link)`
e.g. *Green Kigali* by Dushime rw, via Wikimedia Commons, CC BY-SA 4.0.

## Licence log — non-negotiable

Every published image is logged with source URL, author, licence and date so any
challenge is answerable in seconds. On the website this is automatic:
`fetch_edition_images.py` captures author + licence + source straight from the
Wikimedia Commons API into `img/edition-credits.json`, and `build_site.py` renders the
credit under each hero and on `credits.html`. Tourism-board and AI images added by hand
must be logged the same way before publishing.

## Where images appear

- **Website** — automatic, licence-clear Wikimedia photo per edition, credited by
  construction (already live).
- **Telegram** — the same hero image + attribution caption, posted by
  `.github/scripts/post_telegram.py` (best-effort; falls back to text-only on any
  image problem so a photo issue never blocks the edition).
- **LinkedIn / WhatsApp** — posted by hand: attach the edition's hero from
  `img/editions/<edition-id>.jpg` and carry the credit line from
  `img/edition-credits.json`.
