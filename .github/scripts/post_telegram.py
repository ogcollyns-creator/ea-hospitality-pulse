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

# --- Hero image (best-effort) ------------------------------------------------
# The website already assigns a licence-clear Wikimedia photo to every edition
# (fetch_edition_images.py) with author + licence captured from the Commons API.
# We reuse that exact image and credit here so Telegram carries the same picture
# and the same attribution as the web edition. Everything below is best-effort:
# any missing image, credit or API failure falls back silently to text-only,
# so a photo problem can never block or delay the edition post.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EDIMG = os.path.join(ROOT, "img", "editions")
CREDITS_PATH = os.path.join(ROOT, "img", "edition-credits.json")
CAPTION_MAX = 1024  # Telegram hard limit for a photo caption

try:
    CREDITS = json.load(open(CREDITS_PATH, encoding="utf-8"))
except Exception as _e:
    print(f"::warning::could not load edition credits: {_e}")
    CREDITS = {}

def edition_id(path):
    return os.path.splitext(os.path.basename(path))[0]

def hero_for(path):
    """(image_path, credit_dict|None) if a licence-clear hero exists, else (None, None)."""
    eid = edition_id(path)
    img = os.path.join(EDIMG, eid + ".jpg")
    if not os.path.exists(img):
        return None, None
    return img, CREDITS.get(eid)

def _headline(body):
    """The lead STORY headline of the Telegram body, as plain text — the first
    bold line that is not the masthead. Falls back to the first bold line."""
    bolds = []
    for line in body.splitlines():
        m = re.search(r"\*\*(.+?)\*\*", line)
        if m:
            bolds.append(re.sub(r"\s+", " ", m.group(1)).strip())
    for b in bolds:
        if "HOSPITALITY PULSE" not in b.upper():
            return b
    return bolds[0] if bolds else ""

def build_caption(body, credit):
    """Short plain-text caption: headline + attribution. No parse_mode (plain
    text) so no HTML-entity escaping is needed and the API can never reject it."""
    parts = []
    h = _headline(body)
    if h:
        parts.append(h)
    if credit:
        art = credit.get("artist") or "Unknown"
        lic = credit.get("license") or "see source"
        parts.append(f"\U0001F4F7 {art} \u00b7 {lic} \u00b7 via Wikimedia Commons")
    else:
        parts.append("\U0001F4F7 via Wikimedia Commons (licence-clear)")
    return ("\n\n".join(parts)).strip()[:CAPTION_MAX]

def send_photo(img_path, caption):
    """Upload the hero image via a multipart/form-data sendPhoto call."""
    boundary = "----EAPulse" + str(int(time.time() * 1000))
    with open(img_path, "rb") as fh:
        img = fh.read()
    def field(name, value):
        return (f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{value}\r\n").encode()
    body = field("chat_id", CHAT)
    if caption:
        body += field("caption", caption)
    body += (f"--{boundary}\r\n"
             f"Content-Disposition: form-data; name=\"photo\"; "
             f"filename=\"{os.path.basename(img_path)}\"\r\n"
             f"Content-Type: image/jpeg\r\n\r\n").encode()
    body += img + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def post_hero(path, body):
    """Best-effort: post the edition hero image with an attribution caption.
    Returns True if a photo was sent, False otherwise. Never raises."""
    img_path, credit = hero_for(path)
    if not img_path:
        print(f"::warning::no hero image for {edition_id(path)} — posting text only")
        return False
    caption = build_caption(body, credit)
    for attempt in (1, 2):
        try:
            res = send_photo(img_path, caption)
            if res.get("ok"):
                print(f"posted hero image for {path} -> message_id {res['result']['message_id']}")
                time.sleep(2)
                return True
            print(f"::warning::sendPhoto attempt {attempt} not ok: {res}")
        except Exception as e:
            print(f"::warning::sendPhoto attempt {attempt} failed: {e}")
        time.sleep(3 * attempt)
    print(f"::warning::hero image not sent for {path} — continuing with text only")
    return False


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
        # Hero image first (best-effort — never blocks the text post)
        post_hero(f, body)
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
