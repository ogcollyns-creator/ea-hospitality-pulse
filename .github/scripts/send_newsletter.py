#!/usr/bin/env python3
"""
Deliver the weekly edition: the PDF to the Telegram channel, the HTML issue to
Buttondown.

Runs in GitHub Actions, where outbound internet is open. The authoring sandbox
cannot reach api.telegram.org or api.buttondown.email, so nothing here is ever
run locally.

Environment
-----------
NEWSLETTER_DATE     YYYY-MM-DD of the Sunday edition (required)
TG_TOKEN            Telegram bot token. Absent -> the Telegram step is skipped.
TG_CHAT             Channel handle (default @eahospitalitypulse)
BUTTONDOWN_API_KEY  Absent -> the email step is skipped, loudly but non-fatally.
BUTTONDOWN_STATUS   'draft' (default) or 'about_to_send'.

On BUTTONDOWN_STATUS: the default is deliberately 'draft'. Sending mail to a
list is the one step in this pipeline that cannot be undone — there is no
unpublish, no amended push, no correction that reaches an inbox already opened.
A draft costs one click a week and buys a last look. Flip it to 'about_to_send'
in the workflow once you have seen an issue land correctly.

Idempotent: before creating anything it asks Buttondown whether an email with
this subject already exists, so a re-run of the workflow cannot double-send.
"""
import os, sys, json, time
import urllib.request, urllib.parse, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
DATE = os.environ.get("NEWSLETTER_DATE", "").strip()
TG_TOKEN = os.environ.get("TG_TOKEN", "").strip()
TG_CHAT = os.environ.get("TG_CHAT", "@eahospitalitypulse").strip()
BD_KEY = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
BD_STATUS = os.environ.get("BUTTONDOWN_STATUS", "draft").strip() or "draft"

BD_API = "https://api.buttondown.email/v1"

if not DATE:
    print("::error::NEWSLETTER_DATE is not set")
    sys.exit(1)

META = os.path.join(ROOT, "newsletter", f"weekly-{DATE}.json")
HTML = os.path.join(ROOT, "newsletter", f"weekly-{DATE}.email.html")
PDF = os.path.join(ROOT, "pdf", f"weekly-{DATE}.pdf")

for p in (META, HTML):
    if not os.path.exists(p):
        print(f"::error::missing build artefact {p} — did the build step run?")
        sys.exit(1)

meta = json.load(open(META, encoding="utf-8"))
body = open(HTML, encoding="utf-8").read()


# --------------------------------------------------------------- Telegram ---
def telegram_document():
    """Post the designed PDF to the channel as a downloadable document.

    The channel already has the edition as text. This is the artefact people
    forward to a GM or an owner who is not on Telegram, so it is worth the
    second notification."""
    if not TG_TOKEN:
        print("::warning::TG_TOKEN not set — skipping the Telegram document post")
        return False
    if not os.path.exists(PDF):
        print(f"::warning::{PDF} not found — skipping the Telegram document post")
        return False

    caption = (f"\U0001F4D5 WEEKLY EDITION · Issue {meta['issue']} · "
               f"{meta['window']}\n\n"
               f"{meta['subject']}\n\n"
               f"The Sunday Foresight and {len(meta['big_reads'])} Big Read"
               f"{'s' if len(meta['big_reads']) != 1 else ''} in one designed "
               f"issue. Free to forward.")[:1024]

    boundary = "----EAPulseDoc" + str(int(time.time() * 1000))
    with open(PDF, "rb") as fh:
        blob = fh.read()

    def field(name, value):
        return (f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{value}\r\n").encode()

    payload = field("chat_id", TG_CHAT) + field("caption", caption)
    payload += (f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"document\"; "
                f"filename=\"EA-Hospitality-Pulse-Weekly-{DATE}.pdf\"\r\n"
                f"Content-Type: application/pdf\r\n\r\n").encode()
    payload += blob + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                res = json.loads(r.read().decode())
            if res.get("ok"):
                print(f"Telegram: PDF posted -> message_id "
                      f"{res['result']['message_id']}")
                return True
            print(f"::warning::sendDocument attempt {attempt} not ok: {res}")
        except Exception as e:
            print(f"::warning::sendDocument attempt {attempt} failed: {e}")
        time.sleep(4 * attempt)
    print("::warning::PDF not delivered to Telegram after 3 attempts")
    return False


# -------------------------------------------------------------- Buttondown ---
def bd_request(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        BD_API + path, data=data, method=method,
        headers={"Authorization": f"Token {BD_KEY}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
    return json.loads(raw) if raw.strip() else {}


def already_sent(subject):
    """True if an email with this subject is already in the account.

    Guards against a workflow re-run, a force-push, or a manual dispatch
    delivering the same issue twice."""
    try:
        q = urllib.parse.urlencode({"subject": subject})
        res = bd_request("GET", f"/emails?{q}")
        for e in res.get("results", []):
            if (e.get("subject") or "").strip() == subject.strip():
                print(f"Buttondown: an email with this subject already exists "
                      f"({e.get('id')}, status={e.get('status')}) — not creating "
                      f"another.")
                return True
    except urllib.error.HTTPError as e:
        print(f"::warning::could not check for duplicates (HTTP {e.code}) — "
              f"continuing")
    except Exception as e:
        print(f"::warning::could not check for duplicates ({e}) — continuing")
    return False


def buttondown_email():
    if not BD_KEY:
        print("::warning::BUTTONDOWN_API_KEY not set — the email issue was "
              "built but not delivered. Add the secret to enable email.")
        return False
    subject = meta["subject"]
    if already_sent(subject):
        return True
    payload = {
        "subject": subject,
        "body": body,
        "status": BD_STATUS,
        "email_type": "public",
    }
    try:
        res = bd_request("POST", "/emails", payload)
        print(f"Buttondown: created email {res.get('id')} with status "
              f"'{BD_STATUS}'.")
        if BD_STATUS == "draft":
            print("::notice::The issue is a DRAFT. Open Buttondown and press "
                  "send, or set BUTTONDOWN_STATUS=about_to_send in the workflow "
                  "to deliver automatically.")
        return True
    except urllib.error.HTTPError as e:
        print(f"::error::Buttondown returned HTTP {e.code}: "
              f"{e.read().decode()[:400]}")
    except Exception as e:
        print(f"::error::Buttondown request failed: {e}")
    return False


def main():
    print(f"Weekly edition {DATE} — issue {meta['issue']}, "
          f"{len(meta['big_reads'])} Big Read(s), subject: {meta['subject']!r}")
    tg = telegram_document()
    bd = buttondown_email()
    # Delivery failures are reported, never fatal: the website and the Telegram
    # text edition have already shipped by this point, and failing the job here
    # would only make a partial success look like a total one.
    print(f"\nDelivery summary — Telegram PDF: "
          f"{'sent' if tg else 'not sent'} | Buttondown: "
          f"{'created' if bd else 'not created'}")


if __name__ == "__main__":
    main()
