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
4. **AI-generated** — a bespoke image with no third-party rights. House style is
   **photorealistic** (owner decision, 7 Sep 2026), disclosed on every hero as
   `AI-generated: EA Hospitality Pulse`. See "AI heroes" below for the limits that
   make photorealism safe to publish.

## Never use

- **CC "NC" (non-commercial)** — the Pulse is a commercial product.
- **CC "ND" (no-derivatives)** — we crop and overlay branding.
- **News / wire photos** (Reuters, AP, AFP, getty editorial) — licensed, never free.
- **Other hotels' or operators' marketing photos**, or anything off **Google Images**
  without tracing it to a licence. Google Images may be used for DISCOVERY only —
  see "Google as a discovery layer" below for the one sanctioned route.

## Google as a discovery layer (the only sanctioned route)

Google Images is a **search index, not a licence source**. The photographs in it
belong to photographers and agencies, and a result appearing there grants nothing.
Agencies run reverse-image enforcement (Getty / PicRights / Pixsy) on exactly this
pattern and invoice per image.

There is, however, a legitimate way to use Google here, and `image_sources.py`
implements it:

1. **Query only through the Google Programmable Search JSON API**, never by
   scraping `images.google.com` (which also breaches Google's terms).
2. **Always pass the `rights` parameter**, set to
   `cc_publicdomain|cc_attribute|cc_sharealike`. NC and ND are deliberately
   omitted so the API cannot return material we could not lawfully use.
3. **Treat that filter as a hint, never as proof.** Google infers licence
   metadata from host-page markup and gets it wrong often enough that publishing
   on its say-so would be reckless.
4. **Trace every candidate back to an authoritative API** — Wikimedia Commons or
   Openverse — and accept only the licence *that API* returns.
5. **Quarantine anything unverifiable** to `img/quarantine.json`. It is recorded,
   not published.

So Google widens what we *find*; Commons and Openverse remain the only things
that decide what we may *use*. A Google result that cannot be traced never ships.

### Credentials

    GOOGLE_CSE_KEY   API key           — console.cloud.google.com
    GOOGLE_CSE_CX    Search engine ID  — programmablesearchengine.google.com
                                         ("Search the entire web" + Image search on)

Set both as GitHub Actions repository secrets. Never commit them. If either is
absent the Google source is skipped and Wikimedia + Openverse still run, so the
build never depends on it. The free tier is 100 queries/day.

### Tooling

    python3 fetch_pool_images.py --dry-run    # discover + verify, download nothing
    python3 fetch_pool_images.py gorilla mara # grow the curated pool for these topics

Credits land in `img/credits.json` in the existing schema, so `credits.html` and
the hero captions render them with no further change.

## AI heroes — photorealistic, disclosed, and fenced

Photorealism raises the stakes on subject matter rather than lowering them. A
generated photograph of generic savannah is decoration. A generated photograph of
a real incident is fabricated evidence, and on a brief whose whole claim is that
every number traces to a source, that would cost more than a plain hero ever saves.

So the fence, enforced in `hero_extra.py`:

**Never generated.** Editions whose LEAD is a real news event — crashes,
strikes, protests, attacks, arrests, outbreaks, deaths, court and parliamentary
proceedings, elections — get a data card instead. The rule is not "is the topic
sensitive" but "would a photorealistic image imply we hold footage of a real event
we do not hold". The check reads the lead headline, plus a dominance test so an
edition genuinely about an outbreak is still caught when its headline is oblique.
Roughly 51 of 91 editions in the current archive fall on this side.

**Never depicted, in any image.** Identifiable individuals or faces; real company
logos, airline liveries, brand marks or signage; named landmarks; any text,
numbers or watermarks inside the frame; documents, screens or charts. These are
written into the prompt, not left to the model's discretion.

**Always disclosed.** The credit under the hero reads `AI-generated` rather than
`Photo`, and the licence line records it as original artwork with no third-party
rights. A reader scanning the page can tell what they are looking at without
opening `credits.html`.

**Where it sits in the chain.** Press-kit image → licence-verified photograph →
AI image → data card. A real photograph of a real place always wins; the AI pass
exists to replace typographic cards on editions that have no photographable
subject, not to replace photography.

### Credentials

    IMAGE_API_KEY     required to attempt generation
    IMAGE_API_URL     defaults to the OpenAI images endpoint
    IMAGE_API_MODEL   defaults to gpt-image-1

Set as GitHub Actions secrets. With no key the pass falls back to a drawn
illustration, and failing that the data card, so the build never breaks.

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
