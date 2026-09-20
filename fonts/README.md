# Vendored fonts

These are committed to the repo so the weekly newsletter PDF renders identically
in the authoring sandbox and on the GitHub Actions runner. Relying on system font
paths meant a runner without `fonts-liberation` would silently fall back to a
different face — or crash the build.

| File | Family | Licence |
|---|---|---|
| LiberationSerif-*.ttf | Liberation Serif (Times-metric) | SIL Open Font License 1.1 |
| LiberationSans-*.ttf  | Liberation Sans  (Arial-metric) | SIL Open Font License 1.1 |
| DejaVuSans.ttf        | DejaVu Sans | DejaVu Fonts License (free, MIT-like) |

Liberation Serif carries the body text and headlines; Liberation Sans carries
kickers, tag lines and page furniture. DejaVu Sans is registered only as a
glyph fallback, for arrows, dashes and symbols Liberation lacks.

Both licences permit redistribution. Do not rename the files — the renderer
looks them up by name.
