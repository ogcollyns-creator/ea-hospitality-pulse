# The Weekly Edition — how it is built and delivered

A weekly issue carrying the **Sunday Foresight** and **every Big Read published
that week**, as a designed PDF, an email, and a LinkedIn newsletter issue.

It exists because the daily pipeline only ever fed Telegram. The Foresight PDF
had been generated every Sunday since 26 July 2026 and delivered to nobody: it
was written to `pdf/` and left there. The homepage promised "the weekly
Foresight to your inbox" with a Mailchimp form behind it, and no send was ever
wired up.

---

## What runs, and when

```
Sunday task writes editions-src/foresight-YYYY-MM-DD.md
        │
        ├─► post-to-telegram.yml   (seconds)  text edition + Big Read → channel
        │
        └─► weekly-newsletter.yml  (minutes)  the weekly issue
                 ├─ make_weekly_newsletter.py   → pdf/weekly-<date>.pdf
                 ├─ make_newsletter_outputs.py  → newsletter/<date>.linkedin.md
                 │                               newsletter/<date>.email.html
                 │                               newsletter/<date>.json
                 ├─ commit artefacts + pdf.js
                 └─ .github/scripts/send_newsletter.py
                          ├─ Telegram  sendDocument (the PDF)
                          └─ Buttondown  POST /v1/emails
```

Two workflows, not one, on purpose. Telegram delivery has to be fast and must
never wait on a 13-page render or an email API. If the weekly job fails, the
edition has already reached the channel and the website.

## The three deliverables

| File | What it is | How it ships |
|---|---|---|
| `pdf/weekly-<date>.pdf` | The designed issue: cover, contents, Foresight, every Big Read, the ledger, a back page | Hosted on the site; posted to Telegram as a document; linked from the email |
| `newsletter/<date>.email.html` | Inline-CSS HTML email body | Buttondown |
| `newsletter/<date>.linkedin.md` | A finished LinkedIn newsletter issue | **Manual paste — see below** |

`newsletter/<date>.json` carries the subject line, issue number, PDF URL and
Big Read list. `send_newsletter.py` reads it rather than re-parsing the edition.

## LinkedIn is the one manual step

LinkedIn has no public API for publishing newsletter issues — articles and
newsletters can only be posted from the UI. So the pipeline produces a finished
issue and you paste it once a week. About a minute. The alternative was
pretending it is automated and quietly not publishing, which is the failure mode
this whole document exists to fix.

Open `newsletter/weekly-<date>.linkedin.md`, paste into a new issue of the
LinkedIn newsletter, publish. The GitHub Actions job summary reminds you every
week.

## Setup — three things only you can do

1. **Create the Buttondown account** at the username in `site_config.json`
   (`newsletter.username`, currently `eahospitalitypulse`). If you pick a
   different name, change it there — `build_site.py` and the signup forms both
   read it from that one field.

2. **Add the API key** as a repository secret named `BUTTONDOWN_API_KEY`
   (Settings → Secrets and variables → Actions). Without it the email is built
   and committed but not delivered, and the run logs a warning rather than
   failing.

3. **Migrate the Mailchimp list.** This is the one that will bite. All three
   signup forms on the site used to post to a Mailchimp audience
   (`gmail.us1.list-manage.com`, list `cce993cca2`) and now post to Buttondown.
   Anyone who subscribed before today is in Mailchimp and **will not receive the
   weekly edition** until you export that audience and import it into Buttondown.
   Export from Mailchimp → Audience → All contacts → Export; import in Buttondown
   → Subscribers → Import.

## Sending is a draft by default

`BUTTONDOWN_STATUS` in `weekly-newsletter.yml` is set to `draft`. The issue is
created in Buttondown each Sunday and waits for you to press send.

Email is the only step in this pipeline that cannot be undone. A bad push to the
website is a force-push; a bad Telegram post can be deleted; a bad email is in
someone's inbox forever, and a correction reaches fewer people than the error
did. One click a week buys a last look.

Once you have seen an issue land correctly, change that line to
`about_to_send` and it delivers itself.

## Rebuilding by hand

```bash
python3 make_weekly_newsletter.py editions-src/foresight-2026-09-20.md \
        pdf/weekly-2026-09-20.pdf
python3 make_newsletter_outputs.py editions-src/foresight-2026-09-20.md
```

Or re-run the workflow from the Actions tab: **Weekly newsletter** →
*Run workflow* → set `date`, and `deliver: false` if you only want the files.

Delivery is idempotent. `send_newsletter.py` asks Buttondown whether an email
with this subject already exists before creating one, so a re-run cannot
double-send.

## Fonts

`fonts/` carries Liberation Serif, Liberation Sans and DejaVu Sans, committed to
the repo rather than pulled from the runner's system paths. A runner without
`fonts-liberation` would otherwise fall back to a different face and the issue
would silently change shape. Liberation is SIL OFL; DejaVu is under its own free
licence. Both permit redistribution. See `fonts/README.md`.

## What changed on the website

- All three signup forms (hero, footer, PDF gate) now post to Buttondown.
- A signup block was added to the bottom of every edition page.
- The homepage download slot now offers the weekly issue, not the
  Foresight-only PDF.
- **Fixed:** the Telegram links in `index.html`, `survey.html`, `republish.html`
  and `faq.html` pointed at `t.me/africabusinessriskreview` — a channel handle
  from before the rebrand. Every reader who clicked "Telegram channel" from the
  homepage landed in the wrong place. Also corrected in the `post_telegram.py`
  and `build_site.py` fallback defaults.
- The homepage's claim that subscribers get "the weekly Foresight to your inbox"
  is now true.
