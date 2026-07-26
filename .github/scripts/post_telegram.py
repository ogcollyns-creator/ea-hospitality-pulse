#!/usr/bin/env python3
"""
Post newly added Pulse editions to Telegram.

Runs in GitHub Actions, where outbound internet is unrestricted — unlike the
authoring sandbox, which blocks api.telegram.org at the proxy allowlist.

Idempotent by design: only posts edition files ADDED in the triggering commit,
so re-runs and unrelated pushes never repost anything.
"""
import os, re, sys, subprocess, json, time
import urllib.request, urllib.parse, urllib.error

TOKEN = os.environ.get("TG_TOKEN", "").strip()
CHAT = os.environ.get("TG_CHAT", "@africabusinessriskreview").strip()
MAX = 3800  # safety margin under Telegram's 4096 limit

if not TOKEN:
    print("::error::TELEGRAM_BOT_TOKEN secret is not set — skipping post.")
    sys.exit(0)

def newest_edition():
    """
    Most recently COMMITTED edition — used for manual re-posts.
    Uses git history rather than filename sorting, because filenames don't sort
    chronologically ("evening" < "midday" < "morning" alphabetically).
    """
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=AM", "--name-only", "--format=", "--", "editions-src/"],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        print("::warning::git log failed:", e)
        return []
    for line in out.splitlines():
        line = line.strip()
        if line.endswith(".md") and os.path.exists(line):
            return [line]          # first hit = most recent commit touching an edition
    return []

def added_files():
    """Edition files added in this push."""
    try:
        base = subprocess.run(["git", "rev-parse", "HEAD~1"], capture_output=True, text=True)
        rng = ["HEAD~1", "HEAD"] if base.returncode == 0 else ["--root", "HEAD"]
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=A", *rng],
            capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        print("::warning::git diff failed:", e)
        return []
    return [f for f in out.splitlines()
            if f.startswith("editions-src/") and f.endswith(".md")]

def telegram_section(md):
    for part in re.split(r"\n##+\s*", "\n" + md):
        if part.strip().split("\n", 1)[0].strip().upper().startswith("TELEGRAM"):
            return (part.split("\n", 1)[1] if "\n" in part else "").strip()
    return ""

def to_html(text):
    """
    Convert editorial markdown to Telegram HTML.

    Why HTML and not Markdown: Telegram's MarkdownV2 requires escaping ~18 characters
    (- . ! ( ) etc). Editorial prose is full of them, and a single missed escape makes
    the API reject the whole message. HTML mode only needs & < > escaped, so it is far
    more robust for real writing.
    """
    # escape HTML first so user text can never inject tags
    t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **bold** then *bold*  (longest first)
    t = re.sub(r"\*\*([^*\n]+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"<b>\1</b>", t)
    # _italic_ — only when clearly delimited, so snake_case survives
    t = re.sub(r"(?<![\w/])_([^_\n]+?)_(?![\w/])", r"<i>\1</i>", t)
    return t

def chunk(text):
    """Split on blank lines, never mid-paragraph."""
    if len(text) <= MAX:
        return [text]
    parts, cur = [], ""
    for block in text.split("\n\n"):
        if len(cur) + len(block) + 2 > MAX and cur:
            parts.append(cur.rstrip()); cur = ""
        cur += block + "\n\n"
    if cur.strip():
        parts.append(cur.rstrip())
    total = len(parts)
    return [f"{p}" if total == 1 else
            (p if i == 0 else f"🏨 EA HOSPITALITY PULSE (cont. {i+1}/{total})\n\n{p}")
            for i, p in enumerate(parts)]

def send(text):
    data = urllib.parse.urlencode({
        "chat_id": CHAT,
        "text": to_html(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def main():
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "workflow_dispatch":
        # Manual run from the Actions tab: post the most recent edition.
        # Use this to catch up after a failed run, or to test the pipeline.
        files = newest_edition()
        print(f"Manual dispatch — posting most recent edition: {files}")
    else:
        files = added_files()
    if not files:
        print("No new edition files in this push — nothing to post.")
        return
    for f in files:
        try:
            md = open(f, encoding="utf-8").read()
        except OSError as e:
            print(f"::warning::could not read {f}: {e}")
            continue
        body = telegram_section(md)
        if not body:
            print(f"::warning::no TELEGRAM section in {f} — skipped.")
            continue
        for i, part in enumerate(chunk(body)):
            for attempt in (1, 2, 3):
                try:
                    res = send(part)
                    if res.get("ok"):
                        print(f"posted {f} part {i+1} -> message_id {res['result']['message_id']}")
                        break
                    print(f"::warning::attempt {attempt} not ok: {res}")
                except urllib.error.HTTPError as e:
                    detail = e.read().decode()[:300]
                    print(f"::warning::attempt {attempt} HTTP {e.code}: {detail}")
                    if e.code == 429:
                        time.sleep(5 * attempt); continue
                except Exception as e:
                    print(f"::warning::attempt {attempt} failed: {e}")
                time.sleep(3 * attempt)
            else:
                print(f"::error::failed to post {f} part {i+1} after 3 attempts")
                sys.exit(1)
            time.sleep(2)   # be gentle between parts

if __name__ == "__main__":
    main()
