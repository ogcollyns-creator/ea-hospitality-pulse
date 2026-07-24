#!/usr/bin/env python3
"""
Render a branded, forwardable PDF from a Sunday Foresight edition markdown.
Usage: python make_foresight_pdf.py <foresight-YYYY-MM-DD.md> <out.pdf>
Deps: fpdf2 (pip install fpdf2 --break-system-packages). Uses DejaVu (Unicode).
Emojis are stripped (no emoji font); their meaning is rendered as styled text.
"""
import sys, re, os

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
TEAL=(10,79,72); GOLD=(168,111,31); INK=(31,36,33); MUTED=(107,102,86); SAND=(239,231,214)

def strip_emoji(t):
    return re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF️⃣←-⇿─-◿]", "", t).strip()

def extract_telegram(md):
    parts = re.split(r"\n##+\s*", "\n"+md)
    for p in parts:
        if p.strip().split("\n",1)[0].strip().upper().startswith("TELEGRAM"):
            return (p.split("\n",1)[1] if "\n" in p else "").strip()
    return md.strip()

def main():
    src, out = sys.argv[1], sys.argv[2]
    md = open(src, encoding="utf-8").read()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(src))
    date_iso = m.group(1) if m else ""
    tele = extract_telegram(md)

    from fpdf import FPDF
    pdf = FPDF(format="A4"); pdf.set_auto_page_break(True, margin=18)
    pdf.add_font("DJ","",os.path.join(FONT_DIR,"DejaVuSans.ttf"))
    pdf.add_font("DJ","B",os.path.join(FONT_DIR,"DejaVuSans-Bold.ttf"))
    pdf.add_font("DJ","I",os.path.join(FONT_DIR,"DejaVuSans-Oblique.ttf"))
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    # Masthead
    pdf.set_fill_color(*TEAL); pdf.rect(0,0,pdf.w,26,"F")
    pdf.set_xy(pdf.l_margin,7); pdf.set_font("DJ","B",16); pdf.set_text_color(255,255,255)
    pdf.cell(0,10,"EA HOSPITALITY PULSE")
    pdf.set_xy(pdf.l_margin,17); pdf.set_font("DJ","",8.5); pdf.set_text_color(232,224,190)
    pdf.cell(0,5,"Daily intelligence for city, bush & beach properties across East Africa")
    pdf.ln(22)
    pdf.set_font("DJ","B",13); pdf.set_text_color(*GOLD)
    pdf.cell(0,8,"Sunday Foresight",new_x="LMARGIN",new_y="NEXT")
    if date_iso:
        pdf.set_font("DJ","",9.5); pdf.set_text_color(*MUTED)
        pdf.cell(0,5,date_iso,new_x="LMARGIN",new_y="NEXT")
    pdf.ln(2); pdf.set_draw_color(*GOLD); pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin,pdf.get_y(),pdf.l_margin+W,pdf.get_y()); pdf.ln(4)

    def para(txt, style="", size=10.5, color=INK, gap=2.2, lh=5.2):
        pdf.set_font("DJ",style,size); pdf.set_text_color(*color)
        pdf.multi_cell(W, lh, txt); pdf.ln(gap)

    for raw in tele.split("\n"):
        l = raw.strip()
        if not l: continue
        up = l
        # skip the masthead/date lines from the telegram body
        if re.match(r"^[\U0001F000-\U0001FAFF].*EA HOSPITALITY PULSE", l): continue
        if l.startswith("📅"): continue
        if set(l) <= set("━—-–_ "):  # divider
            pdf.set_draw_color(225,216,196); pdf.set_line_width(0.2)
            pdf.line(pdf.l_margin,pdf.get_y(),pdf.l_margin+W,pdf.get_y()); pdf.ln(3); continue
        clean = strip_emoji(l)
        if not clean: continue
        if re.match(r"^[0-9]️?⃣", l):                       # numbered signal headline
            pdf.ln(1); para(clean, "B", 11.5, TEAL, gap=1.5)
        elif l.startswith("🎯"):                            # So what
            para(clean, "B", 10, GOLD, gap=1.5)
        elif l.startswith("🏷"):                            # tags
            para(clean, "I", 9, MUTED, gap=3)
        elif l.startswith("📡"):                            # calendar header
            pdf.ln(1); para(clean.upper(), "B", 11, TEAL, gap=1.5)
        elif l.startswith("▪️") or l.startswith("•"):
            para("•  "+clean, "", 10, INK, gap=1.2)
        elif l.startswith("💬"):
            pdf.ln(1); para(clean, "I", 9.5, MUTED, gap=1)
        elif l.startswith("—") or "EA Hospitality Pulse |" in l:
            continue
        else:
            para(clean, "", 10.5, INK)

    # Footer
    pdf.ln(3); pdf.set_draw_color(*GOLD); pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin,pdf.get_y(),pdf.l_margin+W,pdf.get_y()); pdf.ln(3)
    pdf.set_font("DJ","",8.5); pdf.set_text_color(*MUTED)
    pdf.multi_cell(W,4.6,"Get every brief — Telegram: t.me/africabusinessriskreview  |  "
                        "LinkedIn: linkedin.com/company/ea-hospitality-pulse  |  Web: ogcollyns-creator.github.io/ea-hospitality-pulse\n"
                        "Kenya · Uganda · Tanzania · Zanzibar · Rwanda. Intelligence for city, bush & beach — so you can decide, not just react.")
    pdf.output(out)
    print("PDF written:", out)

if __name__ == "__main__":
    main()
