#!/usr/bin/env python3
"""
Build the two text deliverables that accompany the weekly PDF:

  newsletter/weekly-YYYY-MM-DD.linkedin.md  — paste-ready LinkedIn newsletter issue
  newsletter/weekly-YYYY-MM-DD.email.html   — Buttondown-ready HTML email body

    python3 make_newsletter_outputs.py editions-src/foresight-2026-09-20.md

Why LinkedIn is a file and not an API call: LinkedIn has no public endpoint for
publishing newsletter issues. Articles and newsletters can only be posted from
the UI. So the pipeline produces a finished issue that is pasted once a week —
about a minute of work — rather than pretending it is automated.

The email links the PDF rather than attaching it. A 150–200KB attachment on a
weekly send measurably hurts deliverability and gets stripped by some corporate
filters; a link to the copy already hosted on the site does not, and it tells us
who actually opens the issue.
"""
import sys, os, re, json, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from make_weekly_newsletter import (        # noqa: E402  (shared parsing)
    section, clean, big_reads_for_week, ledger_this_week, CONFIG)

# ---------------------------------------------------------------- helpers ---
def parse_foresight(tele):
    """Split the Telegram body into the parts an issue needs."""
    thesis, theme, missing = "", [], ""
    signals, calendar, closer = [], [], ""
    state = None
    cur = None

    for raw in tele.split("\n"):
        l = raw.strip()
        if not l:
            continue
        if "EA HOSPITALITY PULSE" in l.upper() and "cont." not in l:
            continue
        if l.startswith(("\U0001F4C5", "\U0001F517", "\U0001F4BC", "— EA")):
            continue
        if set(l) <= set("━─—–-_ "):
            continue

        if clean(l).upper() == "THE WEEK'S SIGNALS":
            state = "signals"
            continue
        if l.startswith("\U0001F4E1"):
            state = "calendar"
            continue

        c = clean(l)
        if not c:
            continue

        if state == "signals":
            if re.match(r"^[0-9]️?⃣", l):
                n, _, rest = c.partition(" ")
                cur = {"n": n.strip(), "head": rest.strip(), "body": "",
                       "sowhat": "", "tag": ""}
                signals.append(cur)
            elif l.startswith("\U0001F3AF") and cur:
                cur["sowhat"] = re.sub(r"^So what:\s*", "", c, flags=re.I)
            elif l.startswith("\U0001F3F7") and cur:
                cur["tag"] = c
            elif cur:
                cur["body"] = (cur["body"] + " " + c).strip()
        elif state == "calendar":
            if c.endswith("?") and len(c) > 40:
                closer = c
            else:
                calendar.append(c)
        else:
            if raw.strip().startswith("**") and not thesis:
                thesis = c
            elif c.lower().startswith("what everyone is missing"):
                missing = re.sub(r"^What everyone is missing\.?\s*", "", c, flags=re.I)
            else:
                theme.append(c)

    return {"thesis": thesis, "theme": theme, "missing": missing,
            "signals": signals, "calendar": calendar, "closer": closer}


def first_sentences(text, n=2):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n]).strip()


# ------------------------------------------------------------- LinkedIn -----
def linkedin_issue(cfg, date_h, window_h, issue_no, fs, reads, urls):
    L = []
    A = L.append
    A(f"# {fs['thesis']}")
    A("")
    A(f"*EA Hospitality Pulse — Weekly Edition, issue {issue_no}. "
      f"{window_h}. Kenya, Uganda, Tanzania, Zanzibar and Rwanda.*")
    A("")
    A("---")
    A("")
    for p in fs["theme"]:
        A(p)
        A("")
    if fs["missing"]:
        A("**What everyone is missing**")
        A("")
        A(fs["missing"])
        A("")
    A("---")
    A("")
    A("## The week's signals")
    A("")
    for s in fs["signals"]:
        A(f"**{s['n']}. {s['head']}**")
        A("")
        if s["body"]:
            A(s["body"])
            A("")
        if s["sowhat"]:
            A(f"*So what — {s['sowhat']}*")
            A("")
        if s["tag"]:
            A(f"`{s['tag']}`")
            A("")
    A("---")
    A("")
    A("## 30/90-day demand calendar")
    A("")
    for c in fs["calendar"]:
        A(f"- {c}")
    A("")
    if fs["closer"]:
        A(f"**{fs['closer']}**")
        A("")
    if reads:
        A("---")
        A("")
        A("## This week's Big Reads")
        A("")
        for fm, _body, d in reads:
            A(f"**{clean(fm.get('title',''))}**")
            A("")
            A(clean(fm.get("description", "")))
            A("")
            A(f"Read it: {cfg['base']}/guides/{fm.get('slug','')}")
            A("")
    A("---")
    A("")
    A(f"**Download this week's edition as a PDF** — the Foresight and all "
      f"{len(reads)} Big Read{'s' if len(reads) != 1 else ''} in one designed "
      f"issue, free to forward: {urls['pdf']}")
    A("")
    A("We publish three briefs a day across the five markets, and this weekly "
      "edition every Sunday. Every figure traces to a named, dated source; "
      "every forecast carries resolution criteria and gets scored in public.")
    A("")
    A(f"Daily on Telegram: {cfg['channels']['telegram']}")
    A(f"Full archive: {cfg['base']}")
    A("")
    A("#EastAfricaTourism #HospitalityStrategy #RevenueManagement "
      "#TravelRisk #HotelIndustry")
    return "\n".join(L)


# ---------------------------------------------------------------- email -----
CSS_BODY = ("margin:0;padding:0;background:#f6f4ef;"
            "font-family:Georgia,'Times New Roman',serif;color:#1f2421;")
CSS_WRAP = ("max-width:640px;margin:0 auto;background:#ffffff;"
            "padding:0 0 32px 0;")
CSS_P = "font-size:16px;line-height:1.62;margin:0 0 16px 0;color:#1f2421;"
CSS_KICK = ("font-family:Helvetica,Arial,sans-serif;font-size:11px;"
            "letter-spacing:.14em;text-transform:uppercase;font-weight:700;"
            "color:#a86f1f;margin:0 0 10px 0;")
CSS_RULE = "border:0;border-top:1px solid #d6cdba;margin:26px 0;"


def esc(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def email_html(cfg, date_h, window_h, issue_no, fs, reads, urls):
    H = []
    A = H.append
    A(f'<div style="{CSS_BODY}">')
    A(f'<div style="{CSS_WRAP}">')

    # masthead
    A('<div style="background:#0a4f48;padding:26px 28px 20px 28px;">')
    A('<div style="font-size:23px;font-weight:700;color:#ffffff;'
      'letter-spacing:-.01em;">EA Hospitality Pulse</div>')
    A('<div style="font-family:Helvetica,Arial,sans-serif;font-size:10px;'
      'letter-spacing:.14em;text-transform:uppercase;color:#e8e0be;'
      'margin-top:7px;">' + esc(cfg["tagline"]) + '</div>')
    A('</div>')

    A('<div style="padding:26px 28px 0 28px;">')
    A('<div style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
      'letter-spacing:.12em;text-transform:uppercase;color:#6b6656;'
      f'margin-bottom:18px;">Weekly edition &middot; Issue {issue_no} '
      f'&middot; {esc(window_h)}</div>')

    A(f'<div style="{CSS_KICK}">The Sunday Foresight</div>')
    A('<h1 style="font-size:27px;line-height:1.24;font-weight:700;'
      'color:#0a4f48;margin:0 0 18px 0;">' + esc(fs["thesis"]) + '</h1>')

    for p in fs["theme"]:
        A(f'<p style="{CSS_P}">{esc(p)}</p>')

    if fs["missing"]:
        A('<table width="100%" cellpadding="0" cellspacing="0" '
          'style="margin:22px 0;"><tr>'
          '<td style="width:3px;background:#a86f1f;"></td>'
          '<td style="background:#f5f0e5;padding:16px 18px;">'
          f'<div style="{CSS_KICK}">What everyone is missing</div>'
          f'<p style="{CSS_P}margin-bottom:0;">{esc(fs["missing"])}</p>'
          '</td></tr></table>')

    # PDF call to action, high up — it is the thing subscribers came for
    A(f'<table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">'
      f'<tr><td align="center" style="background:#0a4f48;padding:15px 18px;">'
      f'<a href="{urls["pdf"]}" style="color:#ffffff;text-decoration:none;'
      f'font-family:Helvetica,Arial,sans-serif;font-size:13px;font-weight:700;'
      f'letter-spacing:.07em;text-transform:uppercase;">'
      f'Download the full issue (PDF)</a>'
      f'</td></tr></table>')
    A('<p style="font-family:Helvetica,Arial,sans-serif;font-size:12px;'
      'line-height:1.5;color:#6b6656;margin:-10px 0 20px 0;text-align:center;">'
      f'The Foresight and {len(reads)} Big Read'
      f'{"s" if len(reads) != 1 else ""} in one designed issue. Free to forward.</p>')

    A(f'<hr style="{CSS_RULE}">')
    A(f'<div style="{CSS_KICK}">The week\'s signals</div>')
    for s in fs["signals"]:
        A('<table width="100%" cellpadding="0" cellspacing="0" '
          'style="margin:0 0 18px 0;"><tr>'
          '<td valign="top" style="width:26px;font-family:Helvetica,Arial,sans-serif;'
          'font-size:17px;font-weight:700;color:#a86f1f;line-height:1.35;">'
          f'{esc(s["n"])}</td><td valign="top">'
          f'<div style="font-size:17px;font-weight:700;color:#0a4f48;'
          f'line-height:1.32;margin-bottom:8px;">{esc(s["head"])}</div>')
        if s["body"]:
            A(f'<p style="{CSS_P}font-size:15px;">{esc(s["body"])}</p>')
        if s["sowhat"]:
            A(f'<p style="{CSS_P}font-size:15px;font-style:italic;color:#a86f1f;">'
              f'So what — {esc(s["sowhat"])}</p>')
        if s["tag"]:
            A('<div style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
              'color:#6b6656;letter-spacing:.04em;">'
              + esc(s["tag"].replace("|", " · ")) + '</div>')
        A('</td></tr></table>')

    A(f'<hr style="{CSS_RULE}">')
    A(f'<div style="{CSS_KICK}">30/90-day demand calendar</div>')
    for c in fs["calendar"]:
        A(f'<p style="{CSS_P}font-size:15px;margin-bottom:10px;">{esc(c)}</p>')
    if fs["closer"]:
        A(f'<p style="{CSS_P}font-size:17px;font-style:italic;font-weight:700;'
          f'color:#0a4f48;margin-top:20px;">{esc(fs["closer"])}</p>')

    if reads:
        A(f'<hr style="{CSS_RULE}">')
        A(f'<div style="{CSS_KICK}">This week\'s Big Reads</div>')
        for fm, _b, d in reads:
            url = f"{cfg['base']}/guides/{fm.get('slug','')}"
            A('<div style="margin:0 0 20px 0;">')
            A(f'<a href="{url}" style="font-size:18px;font-weight:700;'
              f'color:#0a4f48;text-decoration:none;line-height:1.3;">'
              f'{esc(clean(fm.get("title","")))}</a>')
            A(f'<p style="{CSS_P}font-size:15px;color:#6b6656;margin-top:7px;">'
              f'{esc(clean(fm.get("description","")))}</p>')
            A('</div>')

    # footer
    A(f'<hr style="{CSS_RULE}">')
    A('<p style="font-family:Helvetica,Arial,sans-serif;font-size:12px;'
      'line-height:1.6;color:#6b6656;">'
      'Every figure in this issue traces to a named, dated source. Claims are '
      'graded Confirmed, Reported or Early signal. Forecasts carry resolution '
      'criteria and are scored in public. Corrections are published, not '
      'quietly edited.</p>')
    A('<p style="font-family:Helvetica,Arial,sans-serif;font-size:12px;'
      'line-height:1.8;color:#6b6656;">'
      f'<a href="{cfg["base"]}" style="color:#a86f1f;">Archive</a> &nbsp;·&nbsp; '
      f'<a href="{cfg["channels"]["telegram"]}" style="color:#a86f1f;">Telegram</a>'
      f' &nbsp;·&nbsp; '
      f'<a href="{cfg["channels"]["whatsapp"]}" style="color:#a86f1f;">WhatsApp</a>'
      f' &nbsp;·&nbsp; '
      f'<a href="{cfg["channels"]["linkedin"]}" style="color:#a86f1f;">LinkedIn</a>'
      '</p>')
    A('<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
      'line-height:1.6;color:#8d8877;">Written by Onyango George. You are '
      'receiving this because you subscribed at eahospitalitypulse.com. '
      '{{ unsubscribe_url }}</p>')
    A('</div></div></div>')
    return "\n".join(H)


# ------------------------------------------------------------------ main ----
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    src = sys.argv[1]
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    md = open(src, encoding="utf-8").read()

    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(src))
    date_iso = m.group(1)
    d_end = datetime.date.fromisoformat(date_iso)
    d_start = d_end - datetime.timedelta(days=6)
    date_h = d_end.strftime("%-d %B %Y")
    window_h = (f"{d_start.strftime('%-d')}–{d_end.strftime('%-d %B %Y')}"
                if d_start.month == d_end.month else
                f"{d_start.strftime('%-d %b')}–{d_end.strftime('%-d %b %Y')}")
    issue_no = max(1, (d_end - datetime.date(2026, 7, 26)).days // 7 + 1)

    fs = parse_foresight(section(md, "TELEGRAM"))
    reads = big_reads_for_week(date_iso)
    urls = {
        "pdf": f"{cfg['base']}/pdf/weekly-{date_iso}.pdf",
        "edition": f"{cfg['base']}/editions/foresight-{date_iso}.html",
    }

    outdir = os.path.join(ROOT, "newsletter")
    os.makedirs(outdir, exist_ok=True)

    li = linkedin_issue(cfg, date_h, window_h, issue_no, fs, reads, urls)
    li_path = os.path.join(outdir, f"weekly-{date_iso}.linkedin.md")
    open(li_path, "w", encoding="utf-8").write(li)

    html = email_html(cfg, date_h, window_h, issue_no, fs, reads, urls)
    html_path = os.path.join(outdir, f"weekly-{date_iso}.email.html")
    open(html_path, "w", encoding="utf-8").write(html)

    # Subject line: inbox previews cut at roughly 60 characters, so the whole
    # thesis is useless as a subject. Prefer the shortest sentence that still
    # carries a number — that is the sentence the issue is actually about.
    subject = fs["thesis"]
    if len(subject) > 78:
        cands = [x.strip() for x in re.split(r"(?<=[.!?])\s+", fs["thesis"])
                 if x.strip()]
        numbered = [c for c in cands if re.search(r"\d", c) and len(c) <= 95]
        subject = (min(numbered, key=len) if numbered
                   else (cands[-1] if cands else fs["thesis"]))
        subject = subject.rstrip(".") if len(subject) < 40 else subject
    meta = {
        "date": date_iso, "issue": issue_no, "window": window_h,
        "subject": subject,
        "preview": first_sentences(fs["theme"][0] if fs["theme"] else "", 1),
        "pdf_url": urls["pdf"], "edition_url": urls["edition"],
        "big_reads": [{"title": clean(f.get("title", "")),
                       "slug": f.get("slug", ""),
                       "updated": f.get("updated", "")} for f, _b, _d in reads],
        "signals": len(fs["signals"]),
    }
    meta_path = os.path.join(outdir, f"weekly-{date_iso}.json")
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"LinkedIn issue : {li_path}  ({len(li.split())} words)")
    print(f"Email body     : {html_path}  ({len(html)} chars)")
    print(f"Metadata       : {meta_path}")
    print(f"Subject        : {subject}")


if __name__ == "__main__":
    main()
