#!/usr/bin/env python3
"""
Build the EA Hospitality Pulse WEEKLY EDITION — a designed, forwardable PDF
carrying the Sunday Foresight plus every Big Read published that week.

    python3 make_weekly_newsletter.py editions-src/foresight-2026-09-20.md \
            pdf/weekly-2026-09-20.pdf

Why this exists separately from make_foresight_pdf.py: that script renders one
edition as a one-off handout. This is an ISSUE — cover, contents, long-form
articles, the ledger, a back page — and it is the artefact that goes to email
and LinkedIn subscribers, who never see the Telegram channel.

Design register: FT / Economist. Serif body on a generous measure, hairline
rules, sans kickers in letterspaced caps, one accent colour used sparingly.
Single column throughout, because most subscribers open this on a phone.

Fonts are vendored in fonts/ so the runner and the sandbox render identically.
Deps: fpdf2  (pip install fpdf2 --break-system-packages)
"""
import sys, os, re, json, datetime, unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "fonts")
GUIDES_DIR = os.path.join(ROOT, "guides-src")
LEDGER = os.path.join(ROOT, "ledger", "predictions.csv")
CONFIG = os.path.join(ROOT, "site_config.json")

# ---------------------------------------------------------------- palette ---
INK   = (31, 36, 33)      # body text
TEAL  = (10, 79, 72)      # masthead, headlines
GOLD  = (168, 111, 31)    # the single accent
MUTED = (107, 102, 86)    # captions, tags, furniture
RULE  = (214, 205, 186)   # hairlines
SAND  = (245, 240, 229)   # sidebar / cover panel fill
WHITE = (255, 255, 255)

PAGE_W, PAGE_H = 210, 297          # A4 mm
ML = MR = 22                       # side margins — a newspaper measure
MT, MB = 24, 20

# ------------------------------------------------------------- text utils ---
FLAGS = {
    "\U0001F1F0\U0001F1EA": "KE", "\U0001F1FA\U0001F1EC": "UG",
    "\U0001F1F9\U0001F1FF": "TZ", "\U0001F1F7\U0001F1FC": "RW",
    "\U0001F1EA\U0001F1F9": "ET", "\U0001F1EB\U0001F1F7": "FR",
    "\U0001F1EC\U0001F1E7": "UK", "\U0001F1FA\U0001F1F8": "US",
    "\U0001F1E9\U0001F1EA": "DE", "\U0001F1EE\U0001F1F9": "IT",
    "\U0001F1E8\U0001F1E6": "CA", "\U0001F1E6\U0001F1FA": "AU",
}
DIGIT_KEYCAPS = {f"{d}️⃣": str(d) for d in range(10)}
DIGIT_KEYCAPS.update({f"{d}⃣": str(d) for d in range(10)})


def demoji(t):
    """Replace flags and keycaps with their meaning, then drop the rest.

    The PDF has no emoji font. Silently deleting a flag loses information the
    tag line depends on, so country flags become ISO codes and numbered-signal
    keycaps become plain digits before the general strip runs."""
    for k, v in FLAGS.items():
        t = t.replace(k, v)
    for k, v in DIGIT_KEYCAPS.items():
        t = t.replace(k, v)
    t = re.sub(
        r"[\U0001F000-\U0001FAFF\U00002190-\U000021FF\U00002460-\U000024FF"
        r"\U00002500-\U00002BFF\U0000FE0F\U0000200D\U000026A0-\U000027BF]",
        "", t)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def strip_md(t):
    t = re.sub(r"\*\*([^*\n]+?)\*\*", r"\1", t)
    t = re.sub(r"(?<!\w)\*([^*\n]+?)\*(?!\w)", r"\1", t)
    t = re.sub(r"(?<![\w/])_([^_\n]+?)_(?![\w/])", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t


def clean(t):
    return strip_md(demoji(t))


def tracked(s, spaces=1):
    """Poor-man's letterspacing for kickers. fpdf2's char spacing applies to
    the whole cell including the font's own sidebearings, which looks loose at
    small sizes; inserting thin gaps between letters reads tighter in print."""
    return (" " * spaces).join(s)


def section(md, *names):
    """Body of the first '## NAME…' block. Splitting on '##+' means a nested
    '### FIRST COMMENT' terminates the section, which is what we want."""
    for part in re.split(r"\n##+\s*", "\n" + md):
        head = part.strip().split("\n", 1)[0].strip().upper()
        for n in names:
            if head.startswith(n):
                return (part.split("\n", 1)[1] if "\n" in part else "").strip()
    return ""


def frontmatter(path):
    s = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", s, re.S)
    if not m:
        return {}, s
    fm = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M))
    return fm, m.group(2).strip()


def big_reads_for_week(end_iso, days=7):
    """Big Reads whose `updated` date falls in the seven days ending on the
    Foresight's own date, oldest first."""
    end = datetime.date.fromisoformat(end_iso)
    start = end - datetime.timedelta(days=days - 1)
    out = []
    for fn in sorted(os.listdir(GUIDES_DIR)):
        if not fn.endswith(".md"):
            continue
        fm, body = frontmatter(os.path.join(GUIDES_DIR, fn))
        if (fm.get("category", "").strip().lower() != "big read"):
            continue
        try:
            d = datetime.date.fromisoformat(fm.get("updated", "").strip())
        except ValueError:
            continue
        if start <= d <= end:
            out.append((d, fm, body))
    return [(fm, body, d) for d, fm, body in sorted(out, key=lambda r: r[0])]


def ledger_this_week(end_iso, days=7, edition_filter="foresight"):
    """(made, resolved) prediction rows dated inside the window.

    `made` is narrowed to calls from the Sunday Foresight itself. The daily
    briefs make a dozen-plus calls a week; reprinting all of them buried the
    weekly ones and made the back page unreadable. Resolved calls are NOT
    filtered — a call scored this week matters whichever edition made it."""
    if not os.path.exists(LEDGER):
        return [], []
    import csv
    end = datetime.date.fromisoformat(end_iso)
    start = end - datetime.timedelta(days=days - 1)

    def inwin(v):
        try:
            return start <= datetime.date.fromisoformat((v or "").strip()) <= end
        except ValueError:
            return False

    made, resolved = [], []
    with open(LEDGER, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if inwin(row.get("made_date")) and (
                    not edition_filter
                    or edition_filter in (row.get("edition") or "").lower()):
                made.append(row)
            if inwin(row.get("resolved_date")) and row.get("status") in ("correct", "incorrect"):
                resolved.append(row)
    return made, resolved


# ------------------------------------------------------------------- PDF ----
from fpdf import FPDF
from fpdf.enums import XPos, YPos


class Issue(FPDF):
    def __init__(self, brand, issue_label, date_human):
        super().__init__(format="A4", unit="mm")
        self.brand = brand
        self.issue_label = issue_label
        self.date_human = date_human
        self.running = ""          # right-hand running head, set per section
        self.chrome = False        # suppress furniture on the cover
        self.set_margins(ML, MT, MR)
        self.set_auto_page_break(True, margin=MB)
        for style, fn in (("", "LiberationSerif-Regular"),
                          ("B", "LiberationSerif-Bold"),
                          ("I", "LiberationSerif-Italic"),
                          ("BI", "LiberationSerif-BoldItalic")):
            self.add_font("Serif", style, os.path.join(FONT_DIR, fn + ".ttf"))
        for style, fn in (("", "LiberationSans-Regular"),
                          ("B", "LiberationSans-Bold")):
            self.add_font("Sans", style, os.path.join(FONT_DIR, fn + ".ttf"))
        self.add_font("Fallback", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.set_fallback_fonts(["Fallback"])

    # -- furniture ----------------------------------------------------------
    def header(self):
        if not self.chrome:
            return
        self.set_y(11)
        self.set_font("Sans", "B", 6.6)
        self.set_text_color(*MUTED)
        self.cell(self.eff_w() / 2, 4, tracked(self.brand.upper()),
                  new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Sans", "", 6.6)
        self.cell(self.eff_w() / 2, 4, self.running.upper(), align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(16.5)
        self.hairline()
        self.set_y(MT)

    def footer(self):
        if not self.chrome:
            return
        self.set_y(-15)
        self.set_draw_color(*RULE)
        self.set_line_width(0.15)
        self.line(ML, self.get_y(), PAGE_W - MR, self.get_y())
        self.set_y(-12)
        self.set_font("Sans", "", 6.6)
        self.set_text_color(*MUTED)
        self.cell(self.eff_w() / 2, 4, self.date_human,
                  new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font("Sans", "B", 6.6)
        self.cell(self.eff_w() / 2, 4, str(self.page_no()), align="R")

    # -- primitives ---------------------------------------------------------
    def eff_w(self):
        return PAGE_W - ML - MR

    def hairline(self, weight=0.15, color=RULE, pad=0.0, width=None):
        self.set_draw_color(*color)
        self.set_line_width(weight)
        y = self.get_y() + pad
        self.line(ML, y, ML + (width or self.eff_w()), y)

    def rule(self, weight=0.15, color=RULE, space_before=3, space_after=3, width=None):
        self.ln(space_before)
        self.hairline(weight, color, width=width)
        self.ln(space_after)

    def keep(self, need):
        """Start a new page rather than orphan `need` mm of a block."""
        if self.get_y() + need > PAGE_H - MB:
            self.add_page()

    def para(self, text, *, font="Serif", style="", size=10.2, lh=5.0,
             color=INK, gap=2.6, align="J", indent=0, width=None):
        if not text:
            return
        self.set_font(font, style, size)
        self.set_text_color(*color)
        self.set_x(ML + indent)
        self.multi_cell(width or (self.eff_w() - indent), lh, text, align=align,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if gap:
            self.ln(gap)

    def kicker(self, text, color=GOLD, size=7.2, gap=1.8):
        self.set_font("Sans", "B", size)
        self.set_text_color(*color)
        self.set_x(ML)
        self.cell(0, 4, tracked(text.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(gap)

    def headline(self, text, size=17, color=TEAL, lh=7.4, gap=2.4):
        self.para(text, style="B", size=size, lh=lh, color=color, gap=gap, align="L")

    def standfirst(self, text, size=11, gap=3.2):
        self.para(text, style="I", size=size, lh=5.4, color=MUTED, gap=gap, align="L")

    def panel(self, lines, *, fill=SAND, pad=4.5, accent=GOLD):
        """A tinted sidebar with a rule down its left edge. `lines` is a list of
        (text, kwargs) understood by para(). Measured first, then drawn, so the
        fill sits behind the text rather than over it."""
        inner = self.eff_w() - pad * 2 - 1.2
        # measure
        h = pad
        for text, kw in lines:
            self.set_font(kw.get("font", "Serif"), kw.get("style", ""), kw.get("size", 10.2))
            n = len(self.multi_cell(inner, kw.get("lh", 5.0), text, dry_run=True,
                                    output="LINES", align=kw.get("align", "L")))
            h += n * kw.get("lh", 5.0) + kw.get("gap", 2.0)
        h += pad - 2.0
        self.keep(h + 4)
        y0 = self.get_y()
        self.set_fill_color(*fill)
        self.rect(ML, y0, self.eff_w(), h, "F")
        self.set_fill_color(*accent)
        self.rect(ML, y0, 1.2, h, "F")
        self.set_y(y0 + pad)
        for text, kw in lines:
            kw = dict(kw)
            kw["indent"] = pad + 1.2
            kw["width"] = inner
            kw.setdefault("align", "L")
            self.para(text, **kw)
        self.set_y(y0 + h)
        self.ln(4)


# ------------------------------------------------------- Foresight render ---
def render_foresight(pdf, tele, date_human):
    """Walk the Telegram body and typeset it as a magazine feature. The Telegram
    section is the canonical text of the Foresight — the same words subscribers
    read in the channel, re-set rather than rewritten."""
    state = {"in_signals": False, "in_calendar": False}
    thesis_done = False
    buffer_theme = []

    lines = [l.rstrip() for l in tele.split("\n")]
    i = 0
    while i < len(lines):
        raw = lines[i]
        l = raw.strip()
        i += 1
        if not l:
            continue

        # masthead / date lines from the channel post — the PDF has its own
        if "EA HOSPITALITY PULSE" in l.upper() and "cont." not in l:
            continue
        if l.startswith("\U0001F4C5"):          # 📅
            continue
        if set(l) <= set("━─—–-_ "):
            continue
        if l.startswith("\U0001F517") or l.startswith("\U0001F4BC"):   # 🔗 💼
            continue
        if l.startswith("— EA Hospitality Pulse"):
            continue

        # ---- the numbered signals block
        if l.upper().startswith("**THE WEEK'S SIGNALS**") or clean(l).upper() == "THE WEEK'S SIGNALS":
            state["in_signals"] = True
            pdf.rule(0.5, TEAL, 2, 3)
            pdf.kicker("The week's signals", TEAL)
            continue

        # ---- the calendar block
        if l.startswith("\U0001F4E1"):          # 📡
            state["in_signals"] = False
            state["in_calendar"] = True
            pdf.rule(0.5, TEAL, 3, 3)
            pdf.kicker(clean(l), TEAL)
            continue

        c = clean(l)
        if not c:
            continue

        # signal headline: "1 THE LABEL NOW HAS A PRICE…"
        if re.match(r"^[0-9]⃣|^[0-9]️⃣", l) or (
                state["in_signals"] and re.match(r"^[0-9]\s+[A-Z]", c)):
            n, _, rest = c.partition(" ")
            pdf.keep(20)
            pdf.ln(1.5)
            pdf.set_font("Sans", "B", 13)
            pdf.set_text_color(*GOLD)
            pdf.set_x(ML)
            pdf.cell(7, 6, n.strip(), new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Serif", "B", 11.6)
            pdf.set_text_color(*TEAL)
            pdf.multi_cell(pdf.eff_w() - 7, 5.4, rest.strip(), align="L",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.6)
            continue

        if l.startswith("\U0001F3AF"):          # 🎯 So what
            body = re.sub(r"^So what:\s*", "", c, flags=re.I)
            pdf.para("So what — " + body, style="I", size=10, lh=4.8,
                     color=GOLD, gap=1.4, align="L", indent=7)
            continue

        if l.startswith("\U0001F3F7"):          # 🏷 tag line
            pdf.set_font("Sans", "", 7.4)
            pdf.set_text_color(*MUTED)
            pdf.set_x(ML + 7)
            pdf.multi_cell(pdf.eff_w() - 7, 4, c.replace("|", "  ·  "),
                           align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2.2)
            pdf.hairline(0.1, RULE, pad=0)
            pdf.ln(3)
            continue

        # the closing question sits after the calendar — catch it first, or the
        # generic calendar row below would swallow it
        if state["in_calendar"] and c.endswith("?") and len(c) > 40:
            pdf.rule(0.5, GOLD, 3, 4)
            pdf.para(c, style="BI", size=11.5, lh=5.6, color=TEAL, gap=2, align="L")
            state["in_calendar"] = False
            continue

        # calendar entries begin with a country code (flags were demoji'd)
        if state["in_calendar"] and re.match(r"^(KE|UG|TZ|RW|ET|[A-Z]{2})\s", c):
            code, _, rest = c.partition(" ")
            pdf.keep(12)
            pdf.set_font("Sans", "B", 7.6)
            pdf.set_text_color(*TEAL)
            pdf.set_x(ML)
            pdf.cell(9, 4.8, code, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Serif", "", 9.8)
            pdf.set_text_color(*INK)
            pdf.multi_cell(pdf.eff_w() - 9, 4.8, rest.strip(), align="L",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.6)
            continue
        if state["in_calendar"]:
            # a dated entry with no country prefix is a global one (the source
            # line carried a globe emoji, which demoji() strips)
            pdf.keep(12)
            pdf.set_font("Sans", "B", 7.6)
            pdf.set_text_color(*MUTED)
            pdf.set_x(ML)
            pdf.cell(9, 4.8, "WLD", new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Serif", "", 9.8)
            pdf.set_text_color(*INK)
            pdf.multi_cell(pdf.eff_w() - 9, 4.8, c, align="L",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1.6)
            continue

        # ---- theme block, before the signals
        if not state["in_signals"] and not state["in_calendar"]:
            if raw.strip().startswith("**") and not thesis_done:
                pdf.headline(c, size=16.5, lh=7.0)
                pdf.rule(0.5, GOLD, 1, 3.5)
                thesis_done = True
                continue
            if c.lower().startswith("what everyone is missing"):
                body = re.sub(r"^What everyone is missing\.?\s*", "", c, flags=re.I)
                pdf.panel([("WHAT EVERYONE IS MISSING",
                            dict(font="Sans", style="B", size=7.2, lh=4, gap=1.8,
                                 color=GOLD)),
                           (body, dict(size=10, lh=4.9, gap=0, color=INK))])
                continue
            pdf.para(c, size=10.6, lh=5.2, gap=3.0)
            continue

        pdf.para(c, size=10.2, gap=2.4)


# -------------------------------------------------------- Big Read render ---
def render_markdown_body(pdf, body):
    """Typeset a Big Read body. Handles ##/### headings, bullets, numbered
    lists and pipe tables — the only constructs the guides actually use."""
    blocks = re.split(r"\n\s*\n", body)
    first_para = True
    for block in blocks:
        b = block.strip()
        if not b:
            continue

        # pipe table
        if b.startswith("|") and "\n" in b:
            rows = [r for r in b.split("\n") if r.strip().startswith("|")]
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
            if not rows:
                continue
            ncol = max(len(r) for r in rows)
            cw = pdf.eff_w() / ncol
            pdf.keep(8 + 6 * len(rows))
            pdf.ln(1)
            for ri, r in enumerate(rows):
                pdf.set_x(ML)
                pdf.set_font("Sans", "B" if ri == 0 else "", 8.4)
                pdf.set_text_color(*(TEAL if ri == 0 else INK))
                hs = []
                for c in r + [""] * (ncol - len(r)):
                    hs.append(len(pdf.multi_cell(cw, 4.4, clean(c), dry_run=True,
                                                 output="LINES", align="L")))
                h = max(hs) * 4.4
                y0 = pdf.get_y()
                for ci, c in enumerate(r + [""] * (ncol - len(r))):
                    pdf.set_xy(ML + ci * cw, y0)
                    pdf.multi_cell(cw, 4.4, clean(c), align="L",
                                   new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.set_y(y0 + h + 1)
                pdf.hairline(0.1)
                pdf.ln(1.2)
            pdf.ln(2.5)
            continue

        # headings
        m = re.match(r"^(#{2,6})\s+(.*)$", b)
        if m:
            txt = clean(m.group(2))
            pdf.keep(18)
            pdf.ln(2)
            if len(m.group(1)) == 2:
                pdf.kicker(txt, TEAL, size=7.6, gap=1.4)
            else:
                pdf.para(txt, style="B", size=10.6, color=INK, gap=1.6, align="L")
            first_para = False
            continue

        # lists
        if re.match(r"^([-*]|\d+\.)\s", b):
            for line in b.split("\n"):
                t = line.strip()
                if not t:
                    continue
                mm = re.match(r"^([-*]|\d+\.)\s+(.*)$", t)
                if not mm:
                    pdf.para(clean(t), size=10, lh=4.8, gap=1.2, indent=5)
                    continue
                mark = "•" if mm.group(1) in ("-", "*") else mm.group(1)
                pdf.keep(10)
                pdf.set_font("Sans", "B", 8.6)
                pdf.set_text_color(*GOLD)
                pdf.set_x(ML + 1)
                pdf.cell(6, 4.9, mark, new_x=XPos.RIGHT, new_y=YPos.TOP)
                pdf.set_font("Serif", "", 10.1)
                pdf.set_text_color(*INK)
                pdf.multi_cell(pdf.eff_w() - 7, 4.9, clean(mm.group(2)),
                               align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1.1)
            pdf.ln(1.6)
            first_para = False
            continue

        text = clean(" ".join(l.strip() for l in b.split("\n")))
        if not text:
            continue
        if first_para:
            # opening paragraph set a touch larger, as a lead-in
            pdf.para(text, size=11, lh=5.4, gap=2.8)
            first_para = False
        else:
            pdf.para(text, size=10.2, lh=5.0, gap=2.8)


def render_big_read(pdf, fm, body, d, index, total):
    pdf.running = "Big Read"          # set BEFORE add_page: header() runs on add
    pdf.add_page()
    pdf.kicker(f"Big Read {index} of {total}  ·  {d.strftime('%-d %B %Y')}", GOLD)
    pdf.headline(clean(fm.get("title", "Untitled")), size=16, lh=7.0, gap=2.2)
    if fm.get("description"):
        pdf.standfirst(clean(fm["description"]))
    pdf.rule(0.5, TEAL, 0.5, 4)
    render_markdown_body(pdf, body)


# ------------------------------------------------------------------ cover ---
def cover(pdf, cfg, date_h, window_h, issue_no, thesis, standfirst_txt, contents,
          number=None):
    pdf.chrome = False
    pdf.add_page()

    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, PAGE_W, 46, "F")
    pdf.set_xy(ML, 13)
    pdf.set_font("Serif", "B", 24)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 12, "EA Hospitality Pulse", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(ML)
    pdf.set_font("Sans", "", 7.6)
    pdf.set_text_color(232, 224, 190)
    pdf.cell(0, 5, tracked(cfg["tagline"].upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_xy(ML, 52)
    pdf.set_font("Sans", "B", 8)
    pdf.set_text_color(*GOLD)
    pdf.cell(pdf.eff_w() / 2, 5, tracked("WEEKLY EDITION"),
             new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("Sans", "", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(pdf.eff_w() / 2, 5, f"Issue {issue_no}  ·  {window_h}", align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.hairline(0.5, TEAL)
    pdf.ln(9)

    pdf.set_font("Sans", "B", 7.2)
    pdf.set_text_color(*GOLD)
    pdf.set_x(ML)
    pdf.cell(0, 4, tracked("THE SUNDAY FORESIGHT"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.para(thesis, style="B", size=21, lh=9.2, color=TEAL, gap=4, align="L")
    if standfirst_txt:
        pdf.para(standfirst_txt, style="I", size=11.4, lh=5.8, color=MUTED,
                 gap=5, align="L")

    pdf.ln(2)
    pdf.hairline(0.15)
    pdf.ln(6)
    pdf.set_font("Sans", "B", 7.2)
    pdf.set_text_color(*TEAL)
    pdf.set_x(ML)
    pdf.cell(0, 4, tracked("IN THIS ISSUE"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3.5)
    for label, title in contents:
        pdf.keep(14)
        pdf.set_x(ML)
        pdf.set_font("Sans", "B", 7.2)
        pdf.set_text_color(*GOLD)
        pdf.cell(26, 5, label.upper(), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Serif", "", 10.2)
        pdf.set_text_color(*INK)
        pdf.multi_cell(pdf.eff_w() - 26, 5, title, align="L",
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1.4)
        pdf.hairline(0.1)
        pdf.ln(2.4)

    # Number of the week — the one figure the issue turns on. Sits in the space
    # below the contents so the cover reads as an issue, not a title page.
    if number:
        figure, gloss = number
        pdf.ln(3)
        y0 = pdf.get_y()
        if y0 < PAGE_H - 72:
            pdf.set_fill_color(*SAND)
            pdf.set_font("Serif", "", 9.6)
            _fw = 6 + pdf.get_string_width(figure) + 4
            _n = len(pdf.multi_cell(pdf.eff_w() - 6 - _fw, 4.5, gloss,
                                    dry_run=True, output="LINES", align="L"))
            h = max(30.0, 15.0 + _n * 4.5)
            pdf.rect(ML, y0, pdf.eff_w(), h, "F")
            pdf.set_fill_color(*GOLD)
            pdf.rect(ML, y0, 1.2, h, "F")
            pdf.set_xy(ML + 6, y0 + 4.5)
            pdf.set_font("Sans", "B", 7)
            pdf.set_text_color(*GOLD)
            pdf.cell(0, 4, tracked("NUMBER OF THE WEEK"),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_xy(ML + 6, y0 + 10)
            pdf.set_font("Serif", "B", 20)
            pdf.set_text_color(*TEAL)
            w = pdf.get_string_width(figure) + 4
            pdf.cell(w, 10, figure, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Serif", "", 9.6)
            pdf.set_text_color(*INK)
            pdf.set_xy(ML + 6 + w, y0 + 11.2)
            pdf.multi_cell(pdf.eff_w() - 12 - w, 4.5, gloss, align="L",
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_y(y0 + h)

    # foot of cover. Auto page break off: this block is positioned against the
    # bottom of the sheet by design, and letting it break produced a blank p2.
    pdf.set_auto_page_break(False)
    pdf.set_y(PAGE_H - 34)
    pdf.hairline(0.15)
    pdf.ln(2.5)
    pdf.set_font("Sans", "", 7)
    pdf.set_text_color(*MUTED)
    pdf.set_x(ML)
    pdf.multi_cell(pdf.eff_w(), 3.8,
                   "Every figure in this issue traces to a named, dated source. "
                   "Claims are graded Confirmed, Reported or Early signal. "
                   "Corrections are published, not quietly edited.\n"
                   f"{cfg['base']}  ·  Free to forward and to republish with attribution.",
                   align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_auto_page_break(True, margin=MB)
    pdf.chrome = True


# -------------------------------------------------------------- back page ---
def back_page(pdf, cfg, made, resolved):
    pdf.running = "The ledger"
    pdf.add_page()
    pdf.kicker("The ledger", TEAL)
    pdf.para("We publish our forecasts with resolution criteria and a deadline, "
             "then score them in public. Open calls can be checked against the "
             "source on the date given.",
             style="I", size=10, color=MUTED, gap=4, align="L")

    if resolved:
        pdf.kicker("Resolved this week", GOLD, size=7)
        for r in resolved:
            verdict = "CORRECT" if r["status"] == "correct" else "INCORRECT"
            pdf.keep(20)
            pdf.set_x(ML)
            pdf.set_font("Sans", "B", 7.4)
            pdf.set_text_color(*(TEAL if r["status"] == "correct" else GOLD))
            pdf.cell(0, 4.4, f"{r['id']}  ·  {verdict}",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.para(clean(r["claim"]).replace("|", ","), size=9.6, lh=4.6, gap=1.4)
            pdf.hairline(0.1)
            pdf.ln(3)

    if made:
        pdf.ln(1)
        pdf.kicker("New calls this week", GOLD, size=7)
        for r in made:
            pdf.keep(20)
            pdf.set_x(ML)
            pdf.set_font("Sans", "B", 7.4)
            pdf.set_text_color(*TEAL)
            pdf.cell(0, 4.4,
                     f"{r['id']}  ·  RESOLVES BY {r['resolve_by']}  ·  "
                     f"{r['confidence'].upper()}",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.para(clean(r["claim"]).replace("|", ","), size=9.6, lh=4.6, gap=1.4)
            pdf.hairline(0.1)
            pdf.ln(3)

    if not made and not resolved:
        pdf.para("No calls made or resolved in this window.", style="I",
                 size=10, color=MUTED, gap=4)

    # colophon
    pdf.keep(60)
    pdf.ln(4)
    pdf.rule(0.5, TEAL, 2, 5)
    pdf.kicker("Where to find us", TEAL)
    ch = cfg["channels"]
    for label, url in (("Web", cfg["base"]),
                       ("Telegram", ch["telegram"]),
                       ("WhatsApp", ch["whatsapp"]),
                       ("LinkedIn", ch["linkedin"])):
        pdf.set_x(ML)
        pdf.set_font("Sans", "B", 7.6)
        pdf.set_text_color(*GOLD)
        pdf.cell(22, 4.8, label.upper(), new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("Serif", "", 9.4)
        pdf.set_text_color(*INK)
        pdf.cell(0, 4.8, url, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.para("EA Hospitality Pulse is written by Onyango George. Three briefs a "
             "day across Kenya, Uganda, Tanzania, Zanzibar and Rwanda, and this "
             "weekly edition every Sunday. Associations and trade press are "
             "welcome to republish free with attribution.",
             style="I", size=9.2, lh=4.6, color=MUTED, gap=0, align="L")


# ------------------------------------------------------------------- main ---
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    src, out = sys.argv[1], sys.argv[2]
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    md = open(src, encoding="utf-8").read()

    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(src))
    if not m:
        print("::error::could not read a date from the filename")
        sys.exit(2)
    date_iso = m.group(1)
    d_end = datetime.date.fromisoformat(date_iso)
    d_start = d_end - datetime.timedelta(days=6)
    date_h = d_end.strftime("%-d %B %Y")
    window_h = (f"{d_start.strftime('%-d')}–{d_end.strftime('%-d %B %Y')}"
                if d_start.month == d_end.month else
                f"{d_start.strftime('%-d %b')}–{d_end.strftime('%-d %b %Y')}")

    # Issue number: weeks since the first Sunday Foresight shipped.
    epoch = datetime.date(2026, 7, 26)
    issue_no = max(1, (d_end - epoch).days // 7 + 1)

    tele = section(md, "TELEGRAM")
    if not tele:
        print("::error::no TELEGRAM section in the edition")
        sys.exit(2)

    # thesis = first bold line that is not the masthead; standfirst = the
    # paragraph after it.
    thesis, standfirst_txt = "", ""
    tl = [l.strip() for l in tele.split("\n") if l.strip()]
    for idx, l in enumerate(tl):
        if l.startswith("**") and "HOSPITALITY PULSE" not in l.upper():
            thesis = clean(l)
            for nxt in tl[idx + 1:]:
                if nxt.startswith(("━", "**")) or not nxt:
                    break
                standfirst_txt = clean(nxt)
                break
            break
    if not thesis:
        thesis = "The Sunday Foresight"

    # Number of the week: the WhatsApp block already names the issue's key
    # figure, so it is lifted rather than re-derived.
    number = None
    wa = section(md, "WHATSAPP")
    mnum = re.search(
        r"NUMBER OF THE (?:DAY|WEEK)\*?[^\n]*\n+\*?([^*\n\u2014-]+?)\*?\s*[\u2014-]+\s*"
        r"((?:[^\n]+\n?)+?)(?:\n\s*\n|\Z)", wa)
    if mnum:
        gloss = clean(" ".join(mnum.group(2).split("\n"))).strip()
        # belt and braces: never let a URL block leak into the cover figure
        gloss = re.split(r"https?://", gloss)[0].strip().rstrip("\u2014-\u00b7 ")
        number = (clean(mnum.group(1)).strip(), gloss)

    reads = big_reads_for_week(date_iso)
    made, resolved = ledger_this_week(date_iso)

    # the full thesis is already the cover headline; the contents row carries a
    # trimmed version so the page does not say the same thing twice
    short = thesis.split(". ")
    contents = [("Foresight",
                 (". ".join(short[-2:]) if len(short) > 2 else thesis).strip())]
    for fm, _b, dd in reads:
        contents.append(("Big Read", clean(fm.get("title", ""))))
    if made or resolved:
        contents.append(("The ledger",
                         f"{len(made)} new call(s), {len(resolved)} resolved"))

    pdf = Issue(cfg["brand"], "Weekly Edition", f"{cfg['brand']} · {date_h}")
    pdf.set_title(f"EA Hospitality Pulse — Weekly Edition, {date_h}")
    pdf.set_author("Onyango George")
    pdf.set_subject("East African hospitality market intelligence")
    pdf.set_creator("make_weekly_newsletter.py")

    cover(pdf, cfg, date_h, window_h, issue_no, thesis,
          standfirst_txt if standfirst_txt != thesis else "", contents, number)

    pdf.add_page()
    pdf.kicker(f"The Sunday Foresight  ·  {date_h}", GOLD)
    render_foresight(pdf, tele, date_h)

    for i, (fm, body, dd) in enumerate(reads, 1):
        render_big_read(pdf, fm, body, dd, i, len(reads))

    back_page(pdf, cfg, made, resolved)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    pdf.output(out)
    print(f"Weekly edition written: {out}  "
          f"({pdf.page_no()} pages, {len(reads)} Big Read(s), "
          f"{len(made)} new call(s), {len(resolved)} resolved)")


if __name__ == "__main__":
    main()
