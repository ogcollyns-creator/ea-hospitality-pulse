# EA Hospitality Pulse — Website

A zero-backend static site: the homepage plus a searchable, filterable archive of every Pulse edition. No database, no server code, near-zero running cost.

## Files
- `index.html` — the whole site (home, archive, About, subscribe). Self-contained.
- `data.js` — generated file holding every edition. **Do not edit by hand.**
- `build_site.py` — regenerates `data.js` from the markdown editions.
- `editions-src/` — one markdown file per edition (the `pulse-*.md` / `foresight-*.md` files the scheduled task produces). Drop new ones here.

## How new editions appear
1. A new edition markdown lands in `editions-src/`.
2. Run `python build_site.py` — it rebuilds `data.js`.
3. The change is deployed (see below). The archive updates itself; the newest edition sorts to the top.

The scheduled Pulse tasks are already set to do steps 1–2 automatically each run. Step 3 (pushing live) depends on which host you choose.

## Preview locally
Because the page loads `data.js`, just open `index.html` in a browser — it works from a double-click (no server needed).

## Deploy — free options (pick one)

### Cloudflare Pages / Netlify (drag-and-drop — easiest)
1. Go to the host's dashboard → "Add site" / "Deploy manually".
2. Drag this whole folder in. Done — you get a live URL in ~30 seconds.
3. To publish updates, drag the folder again (or connect a Git repo for automatic deploys).

### GitHub Pages
1. Create a repo, push this folder.
2. Settings → Pages → deploy from `main` / root.
3. Every `git push` republishes. This is the path to make publishing fully automatic — the scheduled task can commit + push after each build.

## Custom domain
Any of the above lets you point a domain (e.g. `eahospitalitypulse.com`) at the site later, free of charge on the hosting side.

## To make publishing 100% hands-off
Connect a Git repo (GitHub Pages, or Netlify/Cloudflare "connect to Git"). Then the scheduled task's final step becomes: write edition → `build_site.py` → `git commit` → `git push`, and the site is live within a minute of each Telegram post. Ask and this can be wired up once the repo exists.
