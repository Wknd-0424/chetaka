"""Build an editable PowerPoint version of the Chetaka deck.

Every element is a real PowerPoint object — text boxes, rounded rectangles, tables and
pictures — so the text can be edited in PowerPoint. Layout mirrors chetaka_deck.html
(1920x1080 design grid mapped onto a 13.333 x 7.5 inch slide).

Output: chetaka_deck_editable.pptx
"""

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Emu, Pt

HERE = Path(__file__).parent
ASSETS = HERE / "assets"
OUTPUT = HERE / "chetaka_deck_editable.pptx"

PX = 6350  # EMU per design pixel (12192000 EMU / 1920 px)

# Light theme palette, same values as the HTML deck
INK = RGBColor(0x0F, 0x13, 0x19)
TEXT = RGBColor(0x33, 0x3A, 0x45)
MUTED = RGBColor(0x5C, 0x64, 0x70)
HINT = RGBColor(0x8A, 0x92, 0xA0)
LINE = RGBColor(0xD7, 0xDC, 0xE4)
PANEL = RGBColor(0xFF, 0xFF, 0xFF)
PANEL2 = RGBColor(0xEE, 0xF1, 0xF6)
SLIDE_BG = RGBColor(0xF7, 0xF8, 0xFA)
SKY = RGBColor(0x15, 0x80, 0xC4)
BLUE = RGBColor(0x1E, 0x3C, 0x96)
RED = RGBColor(0xD2, 0x2B, 0x20)
SAFE = RGBColor(0x1B, 0x8A, 0x50)
AMBER = RGBColor(0xB9, 0x74, 0x07)
SKY_SOFT = RGBColor(0xEA, 0xF4, 0xFB)
RED_SOFT = RGBColor(0xFD, 0xEC, 0xEA)
BLUE_SOFT = RGBColor(0xE8, 0xEE, 0xFB)

# Fonts that ship with Windows, so the deck looks the same on any machine.
HEAVY = "Segoe UI Black"       # big headlines and figures
DISPLAY = "Segoe UI Semibold"  # card titles
BODY = "Segoe UI"              # body copy
MONO = "Consolas"              # labels, kickers, code


def px(value: float) -> Emu:
    return Emu(int(value * PX))


# ---------------------------------------------------------------- motion & depth
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def parse_xml(xml: str):
    return etree.fromstring(xml.encode("utf-8"))


def shadow(shape, *, blur=180000, dist=45000, alpha=9000):
    """Soft drop shadow, matching the card shadow used in the HTML deck."""
    spPr = shape._element.spPr
    for existing in spPr.findall(qn("a:effectLst")):
        spPr.remove(existing)
    spPr.append(parse_xml(
        f'<a:effectLst xmlns:a="{A_NS}">'
        f'<a:outerShdw blurRad="{blur}" dist="{dist}" dir="5400000" rotWithShape="0">'
        f'<a:srgbClr val="0F1319"><a:alpha val="{alpha}"/></a:srgbClr>'
        f"</a:outerShdw></a:effectLst>"))


def gradient_fade(slide, x, y, w, h, colour="F7F8FA", angle=0):
    """Rectangle fading from the slide colour to transparent — used over the hero photo."""
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x), px(y), px(w), px(h))
    box.line.fill.background()
    box.shadow.inherit = False
    spPr = box._element.spPr
    for tag in ("a:solidFill", "a:noFill", "a:gradFill"):
        for existing in spPr.findall(qn(tag)):
            spPr.remove(existing)
    spPr.insert(1, parse_xml(
        f'<a:gradFill xmlns:a="{A_NS}" rotWithShape="1">'
        f"<a:gsLst>"
        f'<a:gs pos="0"><a:srgbClr val="{colour}"><a:alpha val="100000"/></a:srgbClr></a:gs>'
        f'<a:gs pos="55000"><a:srgbClr val="{colour}"><a:alpha val="45000"/></a:srgbClr></a:gs>'
        f'<a:gs pos="100000"><a:srgbClr val="{colour}"><a:alpha val="0"/></a:srgbClr></a:gs>'
        f"</a:gsLst>"
        f'<a:lin ang="{angle}" scaled="0"/>'
        f"</a:gradFill>"))
    return box


def fade_transition(slide, duration="slow"):
    """Smooth fade between slides."""
    sldElm = slide._element
    for existing in sldElm.findall(qn("p:transition")):
        sldElm.remove(existing)
    transition = parse_xml(f'<p:transition xmlns:p="{P_NS}" spd="{duration}"><p:fade/></p:transition>')
    timing = sldElm.find(qn("p:timing"))
    if timing is not None:
        sldElm.insert(list(sldElm).index(timing), transition)
    else:
        sldElm.append(transition)


def animate(slide, *, skip=1, delay_ms=140, duration_ms=520):
    """Give every shape a staggered fade-in entrance, in z-order."""
    shapes = [s for s in slide.shapes][skip:]
    if not shapes:
        return
    effects = []
    cid = 10
    for index, shape in enumerate(shapes):
        start = 0 if index == 0 else delay_ms
        node = "afterEffect" if index else "afterEffect"
        effects.append(
            f'<p:par><p:cTn id="{cid}" presetID="10" presetClass="entr" presetSubtype="0" '
            f'fill="hold" grpId="0" nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="{start}"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{cid + 1}" dur="1" fill="hold">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{shape.shape_id}"/></p:tgtEl>'
            f"<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>"
            f'</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr>'
            f'<p:cTn id="{cid + 2}" dur="{duration_ms}"/>'
            f'<p:tgtEl><p:spTgt spid="{shape.shape_id}"/></p:tgtEl>'
            f"</p:cBhvr></p:animEffect>"
            f"</p:childTnLst></p:cTn></p:par>")
        cid += 3

    xml = (
        f'<p:timing xmlns:p="{P_NS}"><p:tnLst>'
        f'<p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst><p:par><p:cTn id="3" fill="hold">'
        f'<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
        f'<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
        f"<p:childTnLst>{''.join(effects)}</p:childTnLst>"
        f"</p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>"
        f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f"</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>")

    sldElm = slide._element
    for existing in sldElm.findall(qn("p:timing")):
        sldElm.remove(existing)
    sldElm.append(parse_xml(xml))


def textbox(slide, x, y, w, h, *, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    return frame


def write(frame, text, *, size=22, bold=False, color=TEXT, font=BODY, align=PP_ALIGN.LEFT,
          spacing=1.2, space_before=0, space_after=0, caps=False, first=False):
    """Add a paragraph (or fill the first, empty one) and return it."""
    para = frame.paragraphs[0] if first else frame.add_paragraph()
    para.alignment = align
    para.line_spacing = spacing
    para.space_before = Pt(space_before)
    para.space_after = Pt(space_after)
    run = para.add_run()
    run.text = text.upper() if caps else text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = font
    return para


def rect(slide, x, y, w, h, *, fill=PANEL, line=LINE, radius=0.035,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    box = slide.shapes.add_shape(shape, px(x), px(y), px(w), px(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        box.adjustments[0] = radius
    if fill is None:
        box.fill.background()
    else:
        box.fill.solid()
        box.fill.fore_color.rgb = fill
    if line is None:
        box.line.fill.background()
    else:
        box.line.color.rgb = line
        box.line.width = Pt(1)
    box.shadow.inherit = False
    frame = box.text_frame
    frame.word_wrap = True
    # PowerPoint shrinks the text if an edit makes it longer than the panel
    frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    frame.margin_left = frame.margin_right = px(18)
    frame.margin_top = frame.margin_bottom = px(14)
    if fill is not None:
        shadow(box)
    return box


def stripe(slide, x, y, w=180, h=6):
    for i, colour in enumerate((SKY, BLUE, RED)):
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x + i * w / 3), px(y), px(w / 3), px(h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = colour
        bar.line.fill.background()
        bar.shadow.inherit = False


def arrow(slide, x, y, size=21):
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, px(x), px(y), px(size), px(size * 0.6))
    shape.fill.solid()
    shape.fill.fore_color.rgb = HINT
    shape.line.fill.background()
    shape.shadow.inherit = False


def slide_base(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    background = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    background.fill.solid()
    background.fill.fore_color.rgb = SLIDE_BG
    background.line.fill.background()
    background.shadow.inherit = False
    return slide


def header(slide, kicker, title, page, total=10):
    frame = textbox(slide, 110, 70, 1400, 40)
    write(frame, kicker, size=10, color=SKY, font=MONO, caps=True, spacing=1.0, first=True)
    frame = textbox(slide, 110, 110, 1560, 150)
    for i, line in enumerate(title):
        write(frame, line, size=25, bold=True, color=INK, font=HEAVY, spacing=1.08, first=(i == 0))
    frame = textbox(slide, 1600, 116, 210, 40)
    write(frame, f"{page:02d} / {total:02d}", size=10, color=HINT, font=MONO,
          align=PP_ALIGN.RIGHT, first=True)
    stripe(slide, 1690, 150, w=120, h=4)


def footer(slide, right="FINTECH & COMMERCE · FRAUD PREVENTION"):
    frame = textbox(slide, 110, 1000, 600, 30)
    write(frame, "CHETAKA", size=8.5, color=HINT, font=MONO, first=True)
    frame = textbox(slide, 1110, 1000, 700, 30)
    write(frame, right, size=8.5, color=HINT, font=MONO, align=PP_ALIGN.RIGHT, first=True)


def label(slide, x, y, w, text, color=MUTED):
    frame = textbox(slide, x, y, w, 26)
    write(frame, text, size=10, color=color, font=MONO, caps=True, first=True)


def card(slide, x, y, w, h, title, body, *, accent=None, fill=PANEL, title_size=13.5,
         body_size=10.5, tag=None, tag_color=SKY):
    """Panel with an optional colour bar on top, a small tag, a heading and body copy."""
    box = rect(slide, x, y, w, h, fill=fill)
    frame = box.text_frame
    first = True
    if tag:
        write(frame, tag, size=8, color=tag_color, font=MONO, caps=True, spacing=1.0,
              space_after=4, first=True)
        first = False
    if title:
        write(frame, title, size=title_size, bold=True, color=INK, font=DISPLAY, spacing=1.1,
              space_after=4, first=first)
        first = False
    if body:
        write(frame, body, size=body_size, color=MUTED, spacing=1.25, first=first)
    if accent is not None:
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x + 6), px(y), px(w - 12), px(4))
        bar.fill.solid()
        bar.fill.fore_color.rgb = accent
        bar.line.fill.background()
        bar.shadow.inherit = False
    return box


def bullets(frame, items, *, size=11, color=TEXT, space=6, first_para=True):
    for i, item in enumerate(items):
        write(frame, "— " + item, size=size, color=color, spacing=1.3, space_after=space,
              first=first_para and i == 0)


def table(slide, x, y, w, h, data, *, col_widths=None, font_size=8.5, highlight_col=None):
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, px(x), px(y), px(w), px(h))
    tbl = shape.table
    if col_widths:
        for i, width in enumerate(col_widths):
            tbl.columns[i].width = px(width)
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = ""
            cell.margin_left = cell.margin_right = px(10)
            cell.margin_top = cell.margin_bottom = px(6)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = PANEL2
            elif highlight_col is not None and c == highlight_col:
                cell.fill.fore_color.rgb = SKY_SOFT
            else:
                cell.fill.fore_color.rgb = PANEL
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            run = para.add_run()
            run.text = value
            run.font.size = Pt(font_size if r else font_size - 1)
            run.font.name = MONO if r == 0 else BODY
            run.font.bold = r == 0 or (highlight_col is not None and c == highlight_col)
            if r == 0:
                run.font.color.rgb = SKY if c == highlight_col else MUTED
            elif value == "Yes":
                run.font.color.rgb = SAFE
            elif value in ("No", "—", "Limited", "After"):
                run.font.color.rgb = HINT
            elif value in ("Varies", "Partly"):
                run.font.color.rgb = AMBER
            else:
                run.font.color.rgb = TEXT
    return tbl


# ---------------------------------------------------------------- slides
def slide_title(prs):
    slide = slide_base(prs)
    if (ASSETS / "hero_shield.jpg").exists():
        frame_box = rect(slide, 1040, 130, 770, 820, fill=PANEL)
        slide.shapes.add_picture(str(ASSETS / "hero_shield.jpg"), px(1054), px(144), px(742), px(792))
    frame = textbox(slide, 110, 150, 880, 40)
    write(frame, "iQOO Hackathon 2026 · Hyderabad City Battle", size=11, color=MUTED, font=MONO,
          caps=True, first=True)
    frame = textbox(slide, 110, 205, 880, 200)
    write(frame, "Chetaka", size=92, bold=True, color=INK, font=HEAVY, spacing=0.9, first=True)
    stripe(slide, 110, 430)
    frame = textbox(slide, 110, 470, 840, 160)
    write(frame, "The on-device scam shield that follows the call into the payment app.",
          size=22, bold=True, color=INK, font=DISPLAY, spacing=1.15, first=True)

    for i, text in enumerate(("Track · FinTech & Commerce", "Fraud prevention")):
        chip = rect(slide, 110 + i * 330, 640, 310, 54, fill=SKY_SOFT if i == 0 else PANEL)
        write(chip.text_frame, text, size=9, color=SKY if i == 0 else TEXT, font=MONO,
              caps=True, first=True)

    label(slide, 110, 736, 760, "Team Matrix · Mahatma Gandhi Institute of Technology")
    members = [("Stephen Raj", "Team lead · Android & call pipeline", "ystephenraj24@gmail.com"),
               ("Pranav", "On-device AI & scam dataset", "pranavbaddam17@gmail.com"),
               ("Sujit Reddy", "Product, UX & demo", "sujitreddy78@gmail.com")]
    for i, (name, role, email) in enumerate(members):
        box = rect(slide, 110 + i * 300, 778, 285, 138)
        write(box.text_frame, name, size=11.5, bold=True, color=INK, font=DISPLAY, first=True)
        write(box.text_frame, role, size=8.5, color=MUTED, space_before=2)
        para = write(box.text_frame, email, size=8, color=SKY, font=MONO, space_before=3)
        para.runs[0].hyperlink.address = "mailto:" + email


def slide_problem(prs):
    slide = slide_base(prs)
    header(slide, "Problem statement",
           ["Digital-arrest scams turn one phone call",
            "into a UPI transfer within minutes."], 2)
    stats = [("2,41,537", "Digital-arrest cases in India, 2022–2025", INK),
             ("₹3,012 cr", "Lost to those cases in the same period", RED),
             ("46%", "Of operations run from Cambodia, Myanmar and Laos", INK)]
    for i, (value, note, colour) in enumerate(stats):
        box = rect(slide, 110 + i * 290, 300, 270, 150)
        write(box.text_frame, value, size=21, bold=True, color=colour, font=HEAVY, first=True)
        write(box.text_frame, note, size=8.5, color=MUTED, spacing=1.25, space_before=6)

    if (ASSETS / "worried_couple.jpg").exists():
        slide.shapes.add_picture(str(ASSETS / "worried_couple.jpg"), px(110), px(480), px(830), px(370))
    frame = textbox(slide, 110, 866, 830, 30)
    write(frame, "Source: MHA and I4C data cited by Chetry (2026), Observer Research Foundation [7]",
          size=8, color=HINT, font=MONO, first=True)

    rect(slide, 990, 300, 820, 420)
    label(slide, 1020, 322, 400, "Where the friction is")
    frictions = [("01", "Protection looks at the wrong thing",
                  "Caller-ID apps judge who is calling. Scammers rotate clean numbers and pass every check."),
                 ("02", "Protection stops at the wrong moment",
                  "Call warnings end when the call ends. The money moves minutes later, inside the payment app."),
                 ("03", "Protection speaks the wrong language",
                  "Scam calls in Hyderabad mix Telugu, Hindi and English. Most tools understand English only.")]
    for i, (num, title, body) in enumerate(frictions):
        y = 360 + i * 118
        frame = textbox(slide, 1020, y, 60, 50)
        write(frame, num, size=16, bold=True, color=RED, font=HEAVY, first=True)
        frame = textbox(slide, 1080, y, 700, 110)
        write(frame, title, size=11.5, bold=True, color=INK, font=DISPLAY, first=True)
        write(frame, body, size=10, color=MUTED, spacing=1.25, space_before=3)

    box = rect(slide, 990, 750, 820, 150, fill=RED_SOFT, line=RGBColor(0xF3, 0xC9, 0xC5))
    write(box.text_frame, "WHO GETS HURT", size=8.5, color=MUTED, font=MONO, first=True)
    write(box.text_frame,
          "Parents at home and first-time UPI users — people who trust authority, are isolated in "
          "the moment, and are pushed to act before they can check with anyone [4][6].",
          size=11, color=TEXT, spacing=1.3, space_before=8)
    footer(slide)


def slide_case(prs):
    """Real, reported victim case plus the national scale of the problem."""
    slide = slide_base(prs)
    header(slide, "Case study · this already happened",
           ["₹24 crore, 26 transfers, 73 days of fear."], 3)

    box = rect(slide, 110, 250, 900, 496)
    frame = box.text_frame
    write(frame, "BENGALURU · FEBRUARY–APRIL 2026", size=11, color=MUTED, font=MONO, first=True)
    write(frame, "Lakshmi Ramamurthy, 74", size=17, bold=True, color=INK, font=DISPLAY, space_before=8)
    write(frame, "Targeted after a property sale. Callers posing as CBI and Enforcement Directorate "
                 "officers kept her under “digital arrest” from 10 February to 24 April 2026.",
          size=11, color=MUTED, spacing=1.35, space_before=6)
    timeline = [("The call", "Impersonated federal investigators; threatened arrest and asset seizure."),
                ("The pressure", "Weeks of daily check-ins. She told nobody — isolation is the tactic."),
                ("The money", "₹24 crore moved in 26 transactions to 23 mule accounts across 10 banks."),
                ("The end", "Police intervened on 24 April, saving ₹3 crore. Six arrested; ₹5.5 crore recovered.")]
    for title, body in timeline:
        write(frame, title, size=11.5, bold=True, color=RED, font=DISPLAY, space_before=9)
        write(frame, body, size=11, color=TEXT, spacing=1.3, space_before=2)
    write(frame, "Source: The Federal, 25 May 2026 [9]", size=8, color=HINT, font=MONO, space_before=10)

    box = rect(slide, 110, 768, 900, 178, fill=SKY_SOFT, line=RGBColor(0xBE, 0xDC, 0xF0))
    frame = box.text_frame
    write(frame, "WHERE CHETAKA WOULD HAVE STEPPED IN", size=11, color=SKY, font=MONO, first=True)
    write(frame, "Transaction 1. An unknown number, a long call, then a banking app — the payment guard "
                 "fires before the first rupee moves, and her son is alerted the same minute.",
          size=12, color=TEXT, spacing=1.35, space_before=8)

    label(slide, 1060, 258, 760, "How many people face this")
    stats = [("2,41,537", "Digital-arrest cases reported in India, 2022–2025", INK),
             ("₹3,012 cr", "Lost in those cases (Ministry of Home Affairs data)", RED),
             ("₹1.25 lakh", "Average loss per reported case (derived from the two MHA figures)", RED),
             ("6,998", "Indians rescued from scam compounds abroad, 2022–2025", SAFE)]
    for i, (value, note, colour) in enumerate(stats):
        x = 1060 + (i % 2) * 390
        y = 300 + (i // 2) * 200
        box = rect(slide, x, y, 370, 175)
        write(box.text_frame, value, size=23, bold=True, color=colour, font=HEAVY, first=True)
        write(box.text_frame, note, size=10.5, color=MUTED, spacing=1.3, space_before=8)

    box = rect(slide, 1060, 710, 760, 236)
    frame = box.text_frame
    write(frame, "WHO IS TARGETED", size=11, color=MUTED, font=MONO, first=True)
    bullets(frame, ["Retirees holding one large, recently liquid sum.",
                    "First-time digital payment users who trust authority.",
                    "People alone at home, told to keep the call secret.",
                    "46% of the operations run from Cambodia, Myanmar and Laos."],
            size=11.5, space=8, first_para=False)
    write(frame, "Figures as cited by Chetry (2026), Observer Research Foundation [7]",
          size=8, color=HINT, font=MONO, space_before=10)
    footer(slide)


def slide_solution(prs):
    slide = slide_base(prs)
    header(slide, "Proposed solution", ["Warn during the call. Pause the payment after it."], 4)
    frame = textbox(slide, 110, 255, 470, 150)
    write(frame, "One shield across the whole scam path — call, payment, family.",
          size=16, bold=True, color=INK, font=DISPLAY, spacing=1.2, first=True)
    value = [("Understands", "What the caller says, in Telugu, Hindi and English — on the phone.", SKY),
             ("Intervenes", "Before the money moves — the payment guard needs no call audio.", RED),
             ("Involves family", "A trusted person is alerted at critical risk, in real time.", SAFE)]
    for i, (tag, body, colour) in enumerate(value):
        card(slide, 620 + i * 405, 250, 385, 140, None, body, tag=tag, tag_color=colour, body_size=10)

    flows = [("1 · During call", "Warn mid-call", SKY,
              ["Unknown number calls.", "Tap speaker: live listening needs speakerphone.",
               "On-device transcript scored live.", "High risk: full-screen alert + haptics."]),
             ("2 · After call", "Pause the payment", RED,
              ["Call ends; length and caller kept.", "UPI or bank app opens within 15 min.",
               "10-second pause screen.", "One tap to skip if the payee is known.",
               "Skip reason logged: known person, delivery, cab."]),
             ("3 · Family", "Bring family in", SAFE,
              ["Risk reaches critical.", "Paired family phone notified.",
               "One tap to call back.", "Opt-in per contact; no audio shared."])]
    for i, (tag, title, colour, steps) in enumerate(flows):
        x = 110 + i * 570
        box = rect(slide, x, 430, 550, 460)
        frame = box.text_frame
        write(frame, tag, size=8.5, color=colour, font=MONO, caps=True, first=True)
        write(frame, title, size=16, bold=True, color=INK, font=DISPLAY, space_before=6, space_after=8)
        for n, step in enumerate(steps, 1):
            write(frame, f"{n}. {step}", size=11, color=TEXT, spacing=1.3, space_after=8)
    footer(slide)


def slide_architecture(prs):
    slide = slide_base(prs)
    header(slide, "On-device & AI architecture", ["Three AI tiers on the phone. Zero cloud AI calls."], 5)

    columns = [
        (110, 250, "Phone signals", None, [
            ("Voice · speaker only", "MediaRecorder VOICE_RECOGNITION", None, None),
            ("Telephony", "Call state, caller, duration", None, None),
            ("App usage", "UPI / bank app in foreground", None, None)]),
        (450, 300, "Tier 0 · always on", SKY, [
            ("Offline speech-to-text", "Android SpeechRecognizer", "CPU", SKY),
            ("Rules & phrases", "Unknown caller, call length, multilingual scam phrases", "CPU", SKY)]),
        (790, 330, "Tier 1 · risk ≥ 20", BLUE, [
            ("Whisper (open-source)", "Code-mixed Telugu · Hindi · English transcription [1]",
             "Snapdragon NPU", BLUE),
            ("Scam classifier", "Small transformer, LiteRT + Qualcomm NPU delegate",
             "Snapdragon NPU", BLUE)]),
        (1160, 300, "Tier 2 · risk ≥ 60", RED, [
            ("Risk engine", "Explainable 0–100 score with reasons", None, None),
            ("Gemma 3 1B", "Explains the scam tactic in the user's language",
             "On-device SLM · stretch", RED)]),
        (1500, 310, "Phone actions", RED, [
            ("Alert + haptics", "Overlay over the call", None, None),
            ("Payment pause", "10-second guard, one-tap skip", None, None),
            ("Family alert", "Paired phone notified", None, None)]),
    ]
    for x, width, head, accent, nodes in columns:
        label(slide, x, 258, width, head, color=HINT)
        count = len(nodes)
        height = (460 - (count - 1) * 12) / count
        for i, (title, body, tag, tag_colour) in enumerate(nodes):
            y = 300 + i * (height + 12)
            fill = SKY_SOFT if title == "Risk engine" else PANEL
            card(slide, x, y, width, height, title, body, accent=accent, fill=fill,
                 title_size=11.5, body_size=9, tag=tag, tag_color=tag_colour or SKY)
    for i in range(4):
        arrow(slide, 400 + i * 350, 515)

    rect(slide, 110, 786, 560, 190)
    label(slide, 140, 800, 400, "On-device vs cloud")
    table(slide, 140, 828, 500, 130,
          [["Need", "On-device", "Cloud API"],
           ["Private call audio", "Never leaves phone", "Uploaded"],
           ["Mid-call latency", "No network hop", "Network-bound"],
           ["Weak signal areas", "Works offline", "Fails"],
           ["Running cost", "Zero per call", "Per request"]],
          col_widths=[180, 180, 140], font_size=8)

    box = rect(slide, 700, 786, 520, 190)
    frame = box.text_frame
    write(frame, "FALLBACK LADDER", size=8.5, color=MUTED, font=MONO, first=True)
    bullets(frame, ["NPU loads: full tiers, latency shown on screen.",
                    "NPU fails: models on GPU or CPU.",
                    "Models fail: rules + phrases; all flows still work."],
            size=10.5, first_para=False)

    box = rect(slide, 1250, 786, 560, 190)
    frame = box.text_frame
    write(frame, "PHONE HARDWARE USED", size=8.5, color=MUTED, font=MONO, first=True)
    write(frame, "Snapdragon NPU · Microphone · Haptics · Telephony · Overlays · Camera (QR check)",
          size=10.5, color=TEXT, spacing=1.3, space_before=6)
    write(frame, "HOW WE GET CALL AUDIO", size=8.5, color=MUTED, font=MONO, space_before=10)
    write(frame, "No app gets the downlink stream. We record the room on speakerphone "
                 "(MediaRecorder, VOICE_RECOGNITION). AccessibilityService rejected — Play policy "
                 "risk. CallScreeningService is metadata only, so it feeds the guard, not the "
                 "transcript.",
          size=8.5, color=TEXT, spacing=1.2, space_before=4)
    footer(slide)


def slide_stack(prs):
    slide = slide_base(prs)
    header(slide, "Technical stack", ["Native Android. Local AI runtime. No backend for AI."], 6)
    layers = [
        ("Mobile platform", "Native Android", "Direct access to telephony, overlays and the NPU.",
         [("Kotlin 2.0", "Language"), ("Jetpack Compose", "UI and overlays"),
          ("Coroutines + Flow", "Real-time pipeline"), ("Foreground Service", "Listening during calls"),
          ("minSdk 29 · targetSdk 35", "Android 15 on the loaner"),
          ("Android Studio + Gradle KTS", "Build and profiling"),
          ("JUnit + Compose UI test", "Metrics harness")]),
        ("Local AI runtime", "On-device models", "Open-source models, quantised for the phone.",
         [("LiteRT + QNN delegate", "Classifier on NPU"), ("whisper.cpp · Whisper small", "Speech-to-text"),
          ("MediaPipe LLM Inference", "Gemma 3 1B (stretch)"), ("SpeechRecognizer", "Offline fallback"),
          ("int8 quantisation", "Classifier ~25 MB · Whisper ~180 MB"),
          ("Gemma 3 1B int4", "~550 MB, loaded only at tier 2"),
          ("All weights shipped in APK", "No model download at runtime")]),
        ("Data & services", "Local first", "Only the family alert touches the network. Office Kit mirrors the debug HUD — per-segment "
         "inference latency in ms and the live risk score — without interrupting the call.",
         [("Room + SQLCipher", "Encrypted local store"), ("TelephonyManager", "Call state"),
          ("UsageStatsManager", "Payment app watch"), ("Firebase Cloud Messaging", "Family alert relay"),
          ("iQOO Office Kit", "Debug HUD mirrored to laptop")]),
    ]
    for i, (tag, title, blurb, items) in enumerate(layers):
        x = 110 + i * 570
        box = rect(slide, x, 250, 550, 420)
        frame = box.text_frame
        write(frame, tag, size=8.5, color=SKY, font=MONO, caps=True, first=True)
        write(frame, title, size=15, bold=True, color=INK, font=DISPLAY, space_before=4)
        write(frame, blurb, size=10.5, color=MUTED, spacing=1.25, space_before=4, space_after=10)
        for name, role in items:
            para = frame.add_paragraph()
            para.space_after = Pt(10)
            run = para.add_run()
            run.text = name
            run.font.size = Pt(13.5)
            run.font.bold = True
            run.font.color.rgb = INK
            run.font.name = BODY
            run2 = para.add_run()
            run2.text = "  ·  " + role
            run2.font.size = Pt(12)
            run2.font.color.rgb = MUTED
            run2.font.name = BODY

    box = rect(slide, 110, 686, 1700, 90, fill=SKY_SOFT, line=RGBColor(0xBE, 0xDC, 0xF0))
    frame = box.text_frame

    rect(slide, 110, 792, 1700, 158)
    label(slide, 140, 806, 900, "Android permissions — each tied to one feature")
    perms = [("READ_PHONE_STATE", "Call start and end"), ("READ_CONTACTS", "Unknown-number check"),
             ("RECORD_AUDIO", "Listening on speaker"), ("PACKAGE_USAGE_STATS", "Payment app detection"),
             ("SYSTEM_ALERT_WINDOW", "Alert and pause overlays"),
             ("FOREGROUND_SERVICE_MICROPHONE", "Background listening"),
             ("POST_NOTIFICATIONS", "Alerts on Android 13+"), ("VIBRATE", "Haptic warning")]
    for i, (code, use) in enumerate(perms):
        x = 140 + (i % 4) * 420
        y = 850 + (i // 4) * 62
        frame = textbox(slide, x, y, 400, 76)
        write(frame, code, size=9, color=INK, font=MONO, first=True)
        write(frame, use, size=10, color=MUTED, space_before=3)
    footer(slide)


def slide_features(prs):
    slide = slide_base(prs)
    header(slide, "Key features & innovation",
           ["Others protect the call. Chetaka protects the money."], 7)
    box = rect(slide, 110, 250, 760, 190, fill=RED_SOFT, line=RGBColor(0xF0, 0xBF, 0xBB))
    frame = box.text_frame
    write(frame, "Payment-app guard — our core innovation", size=14.5, bold=True, color=INK,
          font=DISPLAY, first=True)
    write(frame, "Links a risky call to the payment app opened after it, and pauses before money "
                 "moves. Content-independent, so it still works when the scam script fools a "
                 "classifier [5]. Every skip is logged with a reason, so the guard learns.",
          size=11, color=MUTED, spacing=1.3, space_before=6)

    feats = [("Live vernacular detection",
              "Telugu, Hindi and English code-mix, understood on-device mid-call."),
             ("Explainable risk score",
              "Every alert names its reason: authority, OTP request, urgency, isolation."),
             ("Family Shield", "Real-time alert to a trusted person. Opt-in per contact, no audio shared."),
             ("Private by design", "No audio stored, no server AI, one-tap delete.")]
    for i, (title, body) in enumerate(feats):
        x = 110 + (i % 2) * 390
        y = 465 + (i // 2) * 215
        card(slide, x, y, 370, 195, title, body, title_size=11.5, body_size=10)

    table(slide, 900, 250, 910, 430,
          [["Capability", "Truecaller", "Google scam detect", "Bank SMS alert", "Chetaka"],
           ["Judges who is calling", "Yes", "Yes", "No", "Yes"],
           ["Understands what is said", "No", "Varies", "No", "Yes"],
           ["Telugu · Hindi · English mix", "No", "Limited", "No", "Yes"],
           ["Guards payment app after call", "No", "No", "No", "Yes"],
           ["Acts before money moves", "Partly", "Partly", "After", "Yes"],
           ["Real-time family alert", "No", "No", "No", "Yes"],
           ["Fully on-device AI", "Varies", "Varies", "—", "Yes"]],
          col_widths=[300, 155, 205, 120, 130], font_size=9, highlight_col=4)

    box = rect(slide, 900, 720, 910, 160)
    frame = box.text_frame
    write(frame, "RESEARCH GAP", size=8.5, color=MUTED, font=MONO, first=True)
    write(frame, "Voice-phishing classifiers judge the transcript alone, and LLM-written scam scripts "
                 "cut their accuracy by more than 30% [5]. Chetaka pairs AI detection with a second "
                 "check at the payment step.", size=11, color=TEXT, spacing=1.3, space_before=6)
    footer(slide)


def slide_plan(prs):
    slide = slide_base(prs)
    header(slide, "Hackathon implementation plan",
           ["A working prototype on the iQOO phone in 30 hours."], 8)

    box = rect(slide, 110, 250, 520, 700)
    frame = box.text_frame
    write(frame, "MINIMUM VIABLE PROTOTYPE", size=8.5, color=MUTED, font=MONO, first=True)
    write(frame, "Must work in the demo", size=13, bold=True, color=SAFE, font=DISPLAY, space_before=10)
    bullets(frame, ["Unknown-call detection and call log", "Payment-app guard with pause + skip log",
                    "Live transcription + scam scoring", "In-call alert with haptics",
                    "Family alert on a second phone"], size=11, space=8, first_para=False)
    write(frame, "Stretch goals", size=13, bold=True, color=AMBER, font=DISPLAY, space_before=14)
    bullets(frame, ["Scam classifier on the NPU, latency on screen",
                    "Gemma 3 1B explanation in Telugu / Hindi",
                    "Camera UPI-QR check"], size=11, space=8, first_para=False)

    box = rect(slide, 660, 250, 620, 700)
    frame = box.text_frame
    write(frame, "30-HOUR BUILD ORDER", size=8.5, color=MUTED, font=MONO, first=True)
    rows = [("0–5 h", "Call monitor, contact check, local store"),
            ("5–9 h", "App watcher + payment pause — core innovation first"),
            ("9–14 h", "Listening service, speech-to-text, risk engine"),
            ("14–17 h", "In-call alert and haptics"),
            ("17–20 h", "Family alert and pairing"),
            ("20–24 h", "NPU classifier, Whisper, SLM — stretch"),
            ("24–30 h", "Test set, polish, demo rehearsal")]
    for hours, work in rows:
        para = frame.add_paragraph()
        para.space_after = Pt(15)
        run = para.add_run()
        run.text = hours + "   "
        run.font.size = Pt(12)
        run.font.color.rgb = SKY
        run.font.name = MONO
        run2 = para.add_run()
        run2.text = work
        run2.font.size = Pt(13.5)
        run2.font.color.rgb = TEXT
        run2.font.name = BODY

    box = rect(slide, 1310, 250, 500, 380)
    frame = box.text_frame
    write(frame, "LIVE DEMO · 3 PHONES", size=8.5, color=MUTED, font=MONO, first=True)
    for n, step in enumerate(["Phone B calls Phone A as “police”.",
                              "Chetaka alerts mid-call on Phone A.",
                              "Repeat without speaker; Phone A opens a UPI app.",
                              "Pause screen holds the payment; skip shown.",
                              "Phone C gets the family alert; debug HUD mirrored to the companion screen via Office Kit.",
                              ], 1):
        write(frame, f"{n}. {step}", size=11, color=TEXT, spacing=1.3, space_after=10)

    box = rect(slide, 1310, 655, 500, 300)
    frame = box.text_frame
    write(frame, "HONEST EVALUATION", size=8.5, color=MUTED, font=MONO, first=True)
    write(frame, "Measured live on scripted calls, both languages. Recall on scam calls, "
                 "false-positive rate on normal calls, and median alert latency. Targets: recall "
                 "≥ 0.80, false positives ≤ 10%, alert under 3 s. A wrong block costs more than a "
                 "missed one, so the false-positive target is the hard one.",
          size=10, color=TEXT, spacing=1.25, space_before=6)
    for i, (value, note, colour) in enumerate([("20", "scam calls", RED), ("20", "normal calls", SAFE),
                                               ("3", "metrics", SKY)]):
        inner = rect(slide, 1340 + i * 152, 845, 136, 100, fill=PANEL2)
        write(inner.text_frame, value, size=19, bold=True, color=colour, font=HEAVY,
              align=PP_ALIGN.CENTER, first=True)
        write(inner.text_frame, note, size=8, color=MUTED, align=PP_ALIGN.CENTER, space_before=2)
    footer(slide)


def slide_impact(prs):
    slide = slide_base(prs)
    header(slide, "Utility & impact", ["Buildable today. Useful to millions of families."], 9)

    box = rect(slide, 110, 250, 540, 330)
    frame = box.text_frame
    write(frame, "01  Feasibility", size=14.5, bold=True, color=INK, font=DISPLAY, first=True)
    bullets(frame, ["Every signal uses public Android APIs.", "All AI models are open-source.",
                    "The core guard needs no AI model.", "Fallback ladder keeps flows working."],
            size=11, space=8, first_para=False)

    box = rect(slide, 680, 250, 540, 330)
    frame = box.text_frame
    write(frame, "02  Benefits", size=14.5, bold=True, color=INK, font=DISPLAY, first=True)
    bullets(frame, ["Stops payment before the loss.", "Payment guard works with speakerphone off.",
                    "Private: nothing leaves the phone.", "Zero cloud cost at any scale."],
            size=11, space=8, first_para=False)

    rect(slide, 1250, 250, 560, 700)
    frame = textbox(slide, 1280, 280, 500, 40)
    write(frame, "03  Target users", size=14.5, bold=True, color=INK, font=DISPLAY, first=True)
    if (ASSETS / "upi_market.jpg").exists():
        slide.shapes.add_picture(str(ASSETS / "upi_market.jpg"), px(1280), px(330), px(500), px(260))
    frame = textbox(slide, 1280, 615, 500, 320)
    bullets(frame, ["Parents at home receiving impersonation calls.",
                    "First-time UPI users in tier-2, tier-3 and rural India.",
                    "Adult children protecting family remotely.",
                    "Partners: phone makers, banks, telcos, cyber cells."], size=11, space=12)

    box = rect(slide, 110, 610, 1110, 340, fill=BLUE_SOFT, line=RGBColor(0xC6, 0xD3, 0xF1))
    frame = box.text_frame
    write(frame, "04  Why Chetaka should be selected", size=14.5, bold=True, color=INK,
          font=DISPLAY, first=True)
    bullets(frame, ["Practical utility: acts at the exact moment money is lost.",
                    "Novel: the only approach guarding call-to-payment end to end.",
                    "Phone-first: voice, telephony, haptics and NPU AI on-device.",
                    "Feasible: model-free core first, AI tiers layered on top."],
            size=11, space=12, first_para=False)
    footer(slide)


def slide_references(prs):
    slide = slide_base(prs)
    header(slide, "References", ["Research and data behind Chetaka."], 10)
    refs = [
        ("[1]  Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C., & Sutskever, I. (2023). "
         "Robust speech recognition via large-scale weak supervision. ICML, PMLR 202.",
         "https://proceedings.mlr.press/v202/radford23a.html"),
        ("[2]  He, Y., Sainath, T. N., Prabhavalkar, R., McGraw, I., Alvarez, R., et al. (2018). "
         "Streaming end-to-end speech recognition for mobile devices. arXiv:1811.06621.",
         "https://arxiv.org/abs/1811.06621"),
        ("[3]  Kim, K., Lee, K., Gowda, D., Park, J., Kim, S., et al. (2019). Attention based "
         "on-device streaming speech recognition with large speech corpus. IEEE ASRU 2019.",
         "https://arxiv.org/abs/2001.00577"),
        ("[4]  Shang, Y., Wu, Z., Du, X., Jiang, Y., Ma, B., & Chi, M. (2022). The psychology of the "
         "internet fraud victimization of older adults: A systematic review. Frontiers in Psychology, 13.",
         "https://doi.org/10.3389/fpsyg.2022.912242"),
        ("[5]  Li, W., Manickam, S., Chong, Y.-W., & Karuppayah, S. (2025). Talking like a phisher: "
         "LLM-based attacks on voice phishing classifiers. EAI ICDF2C 2025. arXiv:2507.16291.",
         "https://arxiv.org/abs/2507.16291"),
        ("[6]  Han, S. D., Barnes, L. L., Leurgans, S., Yu, L., Stewart, C. C., Lamar, M., et al. (2021). "
         "Susceptibility to scams in older Black and White adults. Frontiers in Psychology, 12, 685258.",
         "https://doi.org/10.3389/fpsyg.2021.685258"),
        ("[7]  Chetry, S. (2026, July 18). Digital arrest scams and the limits of domestic enforcement. "
         "Observer Research Foundation, Expert Speak.",
         "https://www.orfonline.org/expert-speak/digital-arrest-scams-and-the-limits-of-domestic-enforcement"),
        ("[8]  NITI Aayog. (2025). Digital arrest: The modern day cyber scam. Government of India.",
         "https://www.niti.gov.in/sites/default/files/2025-04/Digital_Arrest_The_Modern_Day_Cyber_Scam.pdf"),
        ("[9]  The Federal. (2026, May 25). Bengaluru digital arrest scam: Elderly woman loses Rs 24 crore, "
         "six held.",
         "https://thefederal.com/category/states/south/karnataka/bengaluru-digital-arrest-scam-elderly-woman-duped-of-rs-24-cr-cyber-police-arrest-six-244311"),
    ]
    for i, (ref, url) in enumerate(refs):
        x = 110 + (i % 2) * 870
        y = 262 + (i // 2) * 142
        frame = textbox(slide, x, y, 820, 124)
        write(frame, ref, size=10.5, color=TEXT, spacing=1.35, first=True)
        link = write(frame, "Open source", size=9, color=SKY, font=MONO, space_before=2)
        link.runs[0].hyperlink.address = url

    stripe(slide, 1630, 835, w=180, h=5)
    frame = textbox(slide, 1110, 860, 700, 80)
    write(frame, "Thank you", size=26, bold=True, color=INK, font=HEAVY,
          align=PP_ALIGN.RIGHT, first=True)
    frame = textbox(slide, 1110, 930, 700, 40)
    write(frame, "Chetaka · The scam shield that follows the call", size=8.5, color=MUTED,
          font=MONO, align=PP_ALIGN.RIGHT, caps=True, first=True)
    footer(slide)


def main() -> None:
    prs = Presentation()
    prs.slide_width = Emu(12192000)
    prs.slide_height = Emu(6858000)
    builders = (slide_title, slide_problem, slide_case, slide_solution, slide_architecture, slide_stack,
                slide_features, slide_plan, slide_impact, slide_references)
    for builder in builders:
        builder(prs)
    for slide in prs.slides:
        fade_transition(slide)
        animate(slide)
    prs.save(OUTPUT)
    print(f"saved {OUTPUT.name} with {len(builders)} editable slides")


if __name__ == "__main__":
    main()
