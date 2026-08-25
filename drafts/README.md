# Staged editions (not yet published)

Files here are **fully drafted and editorially signed off** but deliberately held
back so the Telegram GitHub Action fires one post per slot instead of several at once.

The Action watches `editions-src/**.md`. Nothing in `drafts/` publishes.

## To publish a staged edition

    cp drafts/pulse-YYYY-MM-DD-special.md editions-src/
    python3 build_site.py
    git add -A && git commit -m "Publish edition" && git push origin main

Before publishing, re-check the date in the H1 and the EDITION_URL inside the file
still match the slot you are publishing into. If the slot has moved, rename the file
and update both.

## Currently staged

| File | Series | Publish slot |
|---|---|---|
| `pulse-2026-08-26-special.md` | TRI 2025 report, Part 2 of 3 — MICE arithmetic & 26.8% bed occupancy | 26 Aug 2026 |
| `pulse-2026-08-27-special.md` | TRI 2025 report, Part 3 of 3 — park fee elasticity, receiverships, linear forecast | 27 Aug 2026 |

Part 1 (`pulse-2026-08-25-special.md`) published 25 Aug 2026.
