# Press-kit images

Vetted tourism-board and hotel-group press-kit photography, used per each kit's
terms. This folder is **not** auto-scraped — every image here was checked by a human
and its usage grant recorded in `registry.json` (`grant` field).

## Add an image
1. Confirm the kit's terms permit editorial reuse (many are destination-restricted).
2. Save the JPEG here.
3. Add an entry to `registry.json` (see `_schema`), including the `grant` audit note.
4. Tag it so it matches relevant editions; or pin specific `editions` ids.

`hero_extra.py --press-kit` (run before the Wikimedia fetch) then assigns a matching
image to any edition that lacks a hero, and logs the attribution into
`img/edition-credits.json` with `source_kind: "press-kit"`. See `docs/image-policy.md`.
