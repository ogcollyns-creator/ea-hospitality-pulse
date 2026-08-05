# Workflow changes (apply via GitHub web editor)

The push token lacks `workflow` scope, so these `.github/workflows/` edits are
shipped here as reference targets. Apply each by opening the file on GitHub →
pencil/Edit → paste the matching `*.target.yml` content → Commit. (Editing in the
web UI uses your session, which has workflow permission.)

1. `.github/workflows/validate-feeds.yml`  ⟵  `validate-feeds.target.yml`
   Adds two run modes: `probe-headless` (diagnostic, non-mutating) and
   `promote-headless` (renders try_headless targets and promotes any that yield
   items to method=headless). Installs Playwright only for those two modes.

2. `.github/workflows/radar-scan.yml`  ⟵  `radar-scan.target.yml`
   Installs Playwright and sets RADAR_HEADLESS=1 so scheduled scans actually
   fetch the promoted headless sources. Headless code is inert without this flag.

## Recommended order once applied
1. Run **Validate & promote source feeds** → mode `promote-headless`.
   Renders the 20 headless candidates; promotes the ones that yield items,
   writes radar/out/headless-probe.md so you can see which paid off and which
   are hopeless (e.g. OSAC needs a login session).
2. The next scheduled **Source radar scan** collects items from them.
3. Next daily self-audit reflects the coverage gain.
