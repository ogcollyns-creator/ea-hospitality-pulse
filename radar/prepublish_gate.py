#!/usr/bin/env python3
"""Pre-publish quality gate for an EA Pulse edition.

Runs BEFORE the site builds and BEFORE Telegram posts. Philosophy for sensitive
clients: nothing broken ships. Mechanically-safe defects are auto-repaired
(--fix); anything that cannot be safely repaired BLOCKS the publish (--strict
exits non-zero) with a precise reason, rather than shipping a guess.

  python3 radar/prepublish_gate.py editions-src/pulse-2026-08-04-midday.md
  python3 radar/prepublish_gate.py --fix --strict <files...>
  python3 radar/prepublish_gate.py --changed --fix --strict   # files changed in last commit

Exit code: 0 = clean (or all defects auto-fixed); 1 = a blocker remains (--strict).
"""
import os, sys, re, json, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
CFG  = json.load(open(os.path.join(REPO, "site_config.json")))
BASE = CFG["base"].rstrip("/"); CH = CFG.get("channels", {})
TG   = CH.get("telegram", ""); WA = CH.get("whatsapp", "")

TG_HARD_CHARS = 3800
PLACEHOLDERS  = ("TODO", "TKTK", "TK ", "XXX", "PLACEHOLDER", "LOREM", "{{", "}}", "<insert", "FIXME")

def section(txt, name):
    """Return the body of a '## NAME' section up to the next '## ' header."""
    m = re.search(rf'^##\s+{re.escape(name)}\s*$(.*?)(?=^##\s+|\Z)', txt, re.S | re.M)
    return m.group(1).strip() if m else None

def edition_url(path):
    stem = os.path.basename(path)[:-3] if path.endswith(".md") else os.path.basename(path)
    return f"{BASE}/editions/{stem}.html"

def linkedin_blocks(txt):
    """Return list of (header, body) for ## LINKEDIN and ## LINKEDIN BIG READ."""
    out = []
    for name in ("LINKEDIN", "LINKEDIN BIG READ"):
        b = section(txt, name)
        if b is not None:
            # strip a trailing '### FIRST COMMENT' out of the post body for checks
            post = re.split(r'^###\s+FIRST COMMENT\s*$', b, maxsplit=1, flags=re.M)[0]
            out.append((name, b, post))
    return out

def first_comment_block(path):
    return ("### FIRST COMMENT\n\n"
            f"📖 This edition in full: {edition_url(path)}\n"
            f"📣 Daily briefs on Telegram: {TG}\n"
            f"💬 The 15-second version on WhatsApp: {WA}\n"
            f"🗂 Archive: {BASE}")

def check(path, do_fix):
    txt0 = open(path).read(); txt = txt0
    blockers, fixes, warns = [], [], []

    tg = section(txt, "TELEGRAM"); wa = section(txt, "WHATSAPP")
    if tg is None: blockers.append("missing ## TELEGRAM section")
    if wa is None: blockers.append("missing ## WHATSAPP section")

    # placeholders anywhere = never ship
    for ph in PLACEHOLDERS:
        if ph.lower() in txt.lower():
            blockers.append(f"placeholder text present: '{ph.strip()}'")

    # Telegram hard char limit
    if tg and len(tg) > TG_HARD_CHARS:
        blockers.append(f"Telegram section {len(tg)} chars > {TG_HARD_CHARS} hard limit")
    if tg and BASE not in tg:
        warns.append("Telegram section has no web link line")

    # WhatsApp must carry a NUMBER OF THE DAY
    if wa and "NUMBER OF THE DAY" not in wa.upper():
        blockers.append("WhatsApp section missing 'NUMBER OF THE DAY'")

    # LinkedIn blocks: hashtags, no URLs in body, FIRST COMMENT present
    for name, body, post in linkedin_blocks(txt):
        tags = re.findall(r'(?m)^#\w[\w]*', post) or re.findall(r'#\w+', post.strip().splitlines()[-1] if post.strip() else "")
        last = [l for l in post.strip().splitlines() if l.strip()]
        tag_line = last[-1] if last else ""
        n_tags = len(re.findall(r'#\w+', tag_line))
        if n_tags < 4 or n_tags > 5:
            blockers.append(f"{name}: must end with 4-5 hashtags (found {n_tags}) — cannot safely auto-generate")
        urls = re.findall(r'https?://\S+', post)
        if urls:
            if do_fix:
                for u in urls: txt = txt.replace(u, "").rstrip()
                fixes.append(f"{name}: removed {len(urls)} URL(s) from post body (reach-killer)")
                # ensure they survive in FIRST COMMENT (added below if missing)
            else:
                blockers.append(f"{name}: {len(urls)} URL(s) in post body — LinkedIn suppresses reach")
        if "### FIRST COMMENT" not in body:
            if do_fix:
                # append a FIRST COMMENT block right after this section
                anchor = f"## {name}"
                idx = txt.find(anchor)
                nxt = txt.find("\n## ", idx + len(anchor))
                insert_at = nxt if nxt != -1 else len(txt)
                txt = txt[:insert_at] + "\n\n" + first_comment_block(path) + "\n" + txt[insert_at:]
                fixes.append(f"{name}: inserted missing FIRST COMMENT block")
            else:
                blockers.append(f"{name}: missing '### FIRST COMMENT' block")

    # soft length warnings
    if wa:
        wn = len(wa.split())
        if not (80 <= wn <= 170): warns.append(f"WhatsApp {wn} words (target 90-150)")

    if do_fix and txt != txt0:
        if not txt.endswith("\n"): txt += "\n"
        open(path, "w").write(txt)
        # re-run once to see if fixes cleared blockers (e.g., URL/FIRST COMMENT)
        return check(path, do_fix=False)[:3] + (fixes,)
    return blockers, warns, fixes if do_fix else [], (fixes if do_fix else [])

def changed_editions():
    try:
        out = subprocess.check_output(["git","diff","--name-only","HEAD~1","HEAD"], cwd=REPO, text=True)
    except Exception:
        return []
    return [os.path.join(REPO,f) for f in out.split() if f.startswith("editions-src/") and f.endswith(".md")]

def main():
    do_fix = "--fix" in sys.argv
    strict = "--strict" in sys.argv
    files = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--changed" in sys.argv: files = changed_editions()
    if not files:
        eds = sorted(glob.glob(os.path.join(REPO,"editions-src","pulse-*.md")))
        files = eds[-1:] if eds else []
    if not files:
        print("no edition files to check"); return
    any_block = False
    for f in files:
        res = check(f, do_fix)
        blockers, warns = res[0], res[1]
        fixes = res[-1] if do_fix else []
        name = os.path.basename(f)
        status = "🔴 BLOCKED" if blockers else "🟢 OK"
        print(f"{status}  {name}")
        for x in fixes:    print(f"   🔧 fixed:   {x}")
        for x in blockers: print(f"   ⛔ blocker: {x}")
        for x in warns:    print(f"   🟡 warn:    {x}")
        any_block = any_block or bool(blockers)
    if strict and any_block:
        print("\nPUBLISH BLOCKED — fix the blockers above; nothing shipped.")
        sys.exit(1)
    print("\nGate passed — safe to publish." if not any_block else "\nBlockers remain.")

if __name__ == "__main__":
    main()
