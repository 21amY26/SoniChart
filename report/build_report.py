"""Build the SoniChart project report (Word) on top of the university template.

Usage:  python report/build_report.py [pages.json]
A pages.json (heading -> page label, produced by report/paginate.py from a Word-rendered PDF)
fills the page numbers in the Contents, List of Tables and List of Figures.
"""
import copy
import json
import sys
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FIG, SCR = ROOT / "report" / "figures", ROOT / "report" / "screens"
TEMPLATE = ROOT / "report" / "_render" / "format.docx"
OUT = ROOT / "report" / "SoniChart_HCI_Report.docx"
PAGES = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}
FONT = "Times New Roman"
REPO = "https://github.com/21amY26/SoniChart"
TITLE = "SoniChart: Screen-Reader-Friendly Data Visualisation through Sonification and Tactile Output"
STUDENT, REG_NO, SECTION, TEACHER = "Simran Nischal", "23FE10CAI00326", "C", "Dr. Sanjay Teheriya"

# ---------------------------------------------------------------- inputs (generated from the app; see Annexure A)
TEST_OUTPUT = (SCR / "tests.txt").read_text()
N_TESTS = TEST_OUTPUT.count("\nok ") + TEST_OUTPUT.startswith("ok ")
BRF_SAMPLE = (SCR / "sample.brf").read_text().replace("\r", "")
# the study tasks are read from js/study.js so the report always matches the app
import re
_study = (ROOT / "js" / "study.js").read_text()
TASKS = [dict(zip(("dataset", "kind", "q"), m)) for m in
         re.findall(r"dataset: '(\w+)', type: '\w+', kind: '(\w+)', q: '([^']+)'", _study)]

# ---------------------------------------------------------------- document helpers
doc = docx.Document(str(TEMPLATE))
body = doc.element.body


def ensure_heading_styles():
    for name, lvl, size, align in (("Heading 1", 0, 16, WD_ALIGN_PARAGRAPH.CENTER), ("Heading 2", 1, 13, None),
                                   ("Heading 3", 2, 12, None)):
        try:
            st = doc.styles[name]
        except KeyError:
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles["Normal"]
        st.font.name, st.font.size, st.font.bold = FONT, Pt(size), True
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.font.italic = name == "Heading 3"
        pf = st.paragraph_format
        pf.space_before, pf.space_after, pf.keep_with_next = Pt(12 if lvl else 0), Pt(6 if lvl else 12), True
        if align is not None:
            pf.alignment = align
        ppr = st.element.get_or_add_pPr()
        for old in ppr.findall(qn("w:outlineLvl")):
            ppr.remove(old)
        ol = OxmlElement("w:outlineLvl"); ol.set(qn("w:val"), str(lvl)); ppr.append(ol)


def set_cell_borders(table, show: bool):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(old)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single" if show else "nil")
        if show:
            e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)
    tblPr.append(b)


def set_widths(table, widths_cm):
    """Word lays tables out from tblGrid/tblW, not only cell widths: set all three, fixed layout."""
    tbl = table._tbl; tblPr = tbl.tblPr
    total = sum(widths_cm)
    for tag in ("w:tblW", "w:tblLayout"):
        for e in tblPr.findall(qn(tag)):
            tblPr.remove(e)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(total * 567))); tw.set(qn("w:type"), "dxa"); tblPr.append(tw)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_cm):
        gc.set(qn("w:w"), str(int(w * 567)))
    for row in table.rows:
        for c, w in zip(row.cells, widths_cm):
            c.width = Cm(w)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def run(p, text, size=12, bold=False, italic=False, font=FONT, color=None):
    r = p.add_run(text)
    r.font.name, r.font.size, r.bold, r.italic = font, Pt(size), bold, italic
    r._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


def para(text="", size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6, line=1.5, before=0):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = align
    p.paragraph_format.space_after, p.paragraph_format.space_before = Pt(after), Pt(before)
    p.paragraph_format.line_spacing = line
    if text:
        add_rich(p, text, size, bold, italic)
    return p


def add_rich(p, text, size=12, bold=False, italic=False):
    """Supports **bold** spans inside text."""
    parts = text.split("**")
    for i, part in enumerate(parts):
        if part:
            run(p, part, size, bold or i % 2 == 1, italic)


def bullets(items, size=12, numbered=False):
    for i, t in enumerate(items, 1):
        p = para(after=3, line=1.4, align=WD_ALIGN_PARAGRAPH.LEFT)
        p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(0.9), Cm(-0.5)
        run(p, f"{i}.  " if numbered else "•  ", size)
        add_rich(p, t, size)


def h1(chapter_label, title):
    p = doc.add_paragraph(style="Heading 1")
    run(p, f"{chapter_label}\n" if chapter_label else "", 16, True)
    run(p, title, 16, True)
    return p


def h2(text):
    p = doc.add_paragraph(style="Heading 2"); run(p, text, 13, True); return p


def h3(text):
    p = doc.add_paragraph(style="Heading 3"); run(p, text, 12, True, True); return p


FIGS, TABS = [], []


def caption(kind, num, text):
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=10, line=1.0)
    run(p, f"{kind} {num}: ", 11, True); run(p, text, 11, italic=True)
    (FIGS if kind == "Fig." else TABS).append((num, text))


def figure(path, num, text, width_cm=15.5):
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=2, line=1.0)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    caption("Fig.", num, text)


def table(num, title, header, rows, widths, size=10, align_num=True):
    caption_p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=4, line=1.0)
    caption_p.paragraph_format.keep_with_next = True
    run(caption_p, f"Table {num}: ", 11, True); run(caption_p, title, 11, italic=True)
    TABS.append((num, title))
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_cell_borders(t, True)
    for r_i, row in enumerate([header] + rows):
        for c_i, val in enumerate(row):
            c = t.cell(r_i, c_i); c.width = Cm(widths[c_i])
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(1)
            s = str(val)
            numeric = align_num and c_i > 0 and s.replace(".", "").replace("%", "").replace("-", "").replace("x", "").strip().isdigit()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (r_i == 0 or numeric) else WD_ALIGN_PARAGRAPH.LEFT
            run(p, s, size, bold=r_i == 0)
            if r_i == 0:
                shade(c, "D9E2F3")
    set_widths(t, widths)
    para(after=4, line=1.0)
    return t


def code(text, size=8.5):
    t = doc.add_table(rows=1, cols=1); set_cell_borders(t, True)
    c = t.cell(0, 0); c.width = Cm(15.9); shade(c, "F2F2F2")
    c.paragraphs[0].paragraph_format.space_after = Pt(0)
    lines = text.strip("\n").splitlines()
    for i, l in enumerate(lines):
        p = c.paragraphs[0] if i == 0 else c.add_paragraph()
        p.paragraph_format.space_after, p.paragraph_format.line_spacing = Pt(0), 1.0
        run(p, l if l else " ", size, font="Courier New")
    set_widths(t, [15.9])
    para(after=4, line=1.0)


def page_break():
    p = doc.add_paragraph(); p.add_run().add_break(WD_BREAK.PAGE)


SECT_ORDER = ["headerReference", "footerReference", "footnotePr", "endnotePr", "type", "pgSz", "pgMar", "paperSrc",
              "pgBorders", "lnNumType", "pgNumType", "cols", "formProt", "vAlign", "noEndnote", "titlePg",
              "textDirection", "bidi", "rtlGutter", "docGrid", "printerSettings"]


def sect_insert(sp, el):
    """Insert el into sectPr respecting the schema's element order."""
    name = el.tag.split("}")[1]
    later = SECT_ORDER[SECT_ORDER.index(name) + 1:]
    for child in sp:
        if child.tag.split("}")[1] in later:
            child.addprevious(el); return
    sp.append(el)


def footer_page_number(section, fmt, start=None):
    section.footer.is_linked_to_previous = False
    f = section.footer
    for p in f.paragraphs[1:]:
        p._element.getparent().remove(p._element)
    p = f.paragraphs[0]; p.text = ""; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(); r.font.name, r.font.size = FONT, Pt(11)
    for tag, txt in (("begin", None), (None, " PAGE "), ("separate", None), (None, "1"), ("end", None)):
        if tag:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag)
        else:
            e = OxmlElement("w:instrText" if txt == " PAGE " else "w:t"); e.text = txt
            if txt == " PAGE ":
                e.set(qn("xml:space"), "preserve")
        r._element.append(e)
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")):
        sp.remove(old)
    pg = OxmlElement("w:pgNumType"); pg.set(qn("w:fmt"), fmt)
    if start is not None:
        pg.set(qn("w:start"), str(start))
    sect_insert(sp, pg)


def normalise_section(section):
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, Cm(2.54))
    sp = section._sectPr
    for c in sp.findall(qn("w:cols")):
        sp.remove(c)
    cols = OxmlElement("w:cols"); cols.set(qn("w:space"), "720"); sect_insert(sp, cols)
    for t in sp.findall(qn("w:type")):
        sp.remove(t)


def new_section():
    s = doc.add_section(WD_SECTION.NEW_PAGE); normalise_section(s); return s


def pg(key):
    return PAGES.get(key, "")


def list_table(title, rows, kind):
    p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=8, line=1.0, before=6)
    run(p, title, 16, True)
    t = doc.add_table(rows=1 + len(rows), cols=3); set_cell_borders(t, False)
    for i, (a, b, c) in enumerate([(f"{kind} No", f"{kind} Title", "Page No")] + rows):
        for j, (val, w) in enumerate(zip((a, b, c), (2.6, 11.0, 2.2))):
            cell = t.cell(i, j); cell.width = Cm(w)
            pp = cell.paragraphs[0]; pp.paragraph_format.space_after = Pt(3)
            pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 2 else WD_ALIGN_PARAGRAPH.LEFT
            run(pp, val, 11 if i else 10, bold=i == 0)
    set_widths(t, [2.6, 11.0, 2.2])
    para(after=6, line=1.0)

# ---------------------------------------------------------------- 1. keep the cover, drop the rest
children = list(body.iterchildren())
cover_end = next(i for i, el in enumerate(children) if el.tag == qn("w:p") and el.find(".//" + qn("w:sectPr")) is not None)
final_sectpr = children[-1]
for el in children[cover_end + 1:-1]:
    body.remove(el)
for tag in ("w:type", "w:cols"):
    for e in final_sectpr.findall(qn(tag)):
        final_sectpr.remove(e)
ensure_heading_styles()


def set_text(p, text):
    """Replace a cover paragraph's text while keeping its first run's formatting."""
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    p.runs[0].text = text


cover_map = {
    "MLOPs ASSIGNMENT REPORT": "HUMAN COMPUTER INTERACTION ASSIGNMENT REPORT",
    "AMISHA SINGH": STUDENT.upper(),
    "23FE10CAI00345": REG_NO,
    "DR. AKASH VERMA": TEACHER.upper(),
    "OCTOBER 2026": "NOVEMBER 2026",
}
for p in doc.paragraphs[:40]:
    key = p.text.strip()
    if key in cover_map:
        set_text(p, cover_map[key])
        if key == "23FE10CAI00345":
            sec_p = copy.deepcopy(p._element); p._element.addnext(sec_p)
            set_text(docx.text.paragraph.Paragraph(sec_p, p._parent), f"SECTION {SECTION}")

title_p = next(p for p in doc.paragraphs if p.text.strip().startswith("HUMAN COMPUTER INTERACTION ASSIGNMENT"))
new_p = copy.deepcopy(title_p._element); title_p._element.addnext(new_p)
tp = docx.text.paragraph.Paragraph(new_p, title_p._parent)
set_text(tp, TITLE)
tp.runs[0].font.size = Pt(15)
tp.paragraph_format.space_before = Pt(10)

cover_ps = [el for el in list(body.iterchildren())[:cover_end] if el.tag == qn("w:p")]
empties = [el for el in cover_ps if not el.xpath("string(.)").strip() and not el.findall(".//" + qn("w:drawing"))
           and el.find(".//" + qn("w:sectPr")) is None]
for el in empties[:4]:
    body.remove(el)

cover = doc.sections[0]
normalise_section(cover)
footer_page_number(cover, "lowerRoman", 1)

# ---------------------------------------------------------------- 2. front matter
s = doc.sections[-1]; normalise_section(s)
p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=14); run(p, "ACKNOWLEDGEMENT", 16, True)
for t in [
    f"I would like to express my sincere gratitude to **{TEACHER}**, Department of Artificial Intelligence and "
    "Machine Learning, School of Computer Science and Engineering, Manipal University Jaipur, for the guidance and "
    "the opportunity to work on this Human Computer Interaction project.",
    "I am thankful to the Department of Artificial Intelligence and Machine Learning for the curriculum and resources "
    "that made this work possible, and to the accessibility research community whose guidelines on sonification, "
    "tactile graphics and accessible visualisation shaped the design of this project.",
    "Finally, I thank my family and friends for their constant support and encouragement.",
]:
    para(t)
p = para(align=WD_ALIGN_PARAGRAPH.RIGHT, before=30, line=1.2); run(p, f"{STUDENT}\n{REG_NO}\nSection {SECTION}", 12, True)

page_break()
p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=14); run(p, "ABSTRACT", 16, True)
para(
    "Charts are one of the most common ways to communicate data, yet they are largely inaccessible to people who are "
    "blind or have low vision (BLV). Screen readers typically announce a chart as a single image with, at best, a short "
    "alternative text, which hides trends, extremes and comparisons that sighted readers see at a glance. This project "
    "presents **SoniChart**, a web application that turns line and bar charts into several non-visual representations: "
    "an interactive **sonification** in which each value is mapped to pitch and its position to stereo pan; "
    "**keyboard exploration** with spoken, screen-reader-compatible descriptions of each point and automatically generated "
    "summaries of extremes and trend; and **tactile output** in the form of a swell-paper graphic with Grade-1 Braille "
    "labels, a Braille Ready File (.brf) for embossers, and vibration patterns for mobile phones.")
para(
    f"The system was built with plain HTML, CSS and JavaScript using the Web Audio, Web Speech and Vibration APIs and "
    f"WAI-ARIA live regions, so it runs in any modern browser without installation. {N_TESTS} automated unit tests "
    "verify the Braille translation, the pitch and pan mappings, the trend classifier, the tactile layout constraints and "
    "the study scoring. To evaluate the approach with its intended users, a within-subjects user study was designed that "
    "compares three conditions (data table baseline, sonification with speech, and tactile graphic) on six chart-reading "
    "tasks covering value retrieval, comparison, extremes and trend, measuring accuracy, completion time, NASA-TLX "
    "workload and System Usability Scale scores. A built-in study mode presents the tasks, records timing and accuracy, "
    "and exports a log for analysis.")
p = para(); add_rich(p, "**Keywords:** accessibility, data visualisation, sonification, tactile graphics, Braille, "
                        "screen readers, blind and low-vision users, human–computer interaction, user study")

page_break()
lt_slot = doc.add_paragraph()
page_break()
toc_slot = doc.add_paragraph()

# ---------------------------------------------------------------- 3. main matter
body_sec = new_section()
footer_page_number(doc.sections[-2], "lowerRoman")
footer_page_number(body_sec, "decimal", 1)

# ---- Chapter 1
h1("CHAPTER 1", "INTRODUCTION")
h2("1.1 Introduction and Motivation")
para("Data visualisation is a primarily visual medium. News articles, school textbooks, dashboards and scientific papers "
     "rely on charts to show how a quantity changes over time or how categories compare. The World Health Organization "
     "estimates that at least 2.2 billion people live with a vision impairment, and many of them use screen readers such "
     "as NVDA, JAWS, VoiceOver or TalkBack to access digital content. For these users, a chart is usually announced as "
     "“image” or with a one-line alternative text, so they cannot explore the data independently, check a specific value, "
     "or notice a trend for themselves [1], [4].")
para("Sighted readers get an overview first and then zoom into details. A good accessible chart should support the same "
     "process through other senses. Sound is well suited to showing shape over time: rising pitch is quickly heard as "
     "rising values [2], [5]. Touch is well suited to spatial relationships and is the established medium for Braille "
     "readers [9]. Speech and text give exact values. SoniChart combines these channels so that a BLV user can choose the "
     "representation that suits the task.")
h3("Applications and Advantages")
bullets(["**Education:** students with visual impairments can explore the same charts as their classmates in mathematics, "
         "geography and science.",
         "**News and public data:** weather, prices and statistics can be understood independently rather than through a "
         "single summary written by someone else.",
         "**Workplace:** BLV professionals can inspect business data without asking a sighted colleague.",
         "**No installation:** the tool runs in a browser and works with the user's existing screen reader."])
h2("1.2 Problem Statement and Objectives")
para("**Problem statement.** Common web charts give BLV users no way to explore data on their own: there is no overview "
     "of the shape, no way to step through values, and no tactile version for Braille readers. The aim of this project is "
     "to design, build and plan the evaluation of a system that makes line and bar charts perceivable through sound, speech "
     "and touch.")
para("The objectives are:")
bullets(["Design a sonification that maps data values to pitch and data position to stereo pan, with audible markers for "
         "the extremes.",
         "Provide keyboard-only exploration that works with screen readers, with point-by-point descriptions and "
         "automatically generated summaries.",
         "Generate tactile graphics that follow tactile design guidelines, together with Braille text output.",
         "Build a study mode and protocol to compare these modalities with a data-table baseline using BLV participants."],
        numbered=True)
h2("1.3 Organization of the Report")
para("Chapter 2 introduces the background concepts, technologies and related work. Chapter 3 describes the design "
     "methodology, the system architecture, the mappings used for each modality and the user study design. Chapter 4 "
     "covers the implementation and testing. Chapter 5 presents the evaluation: technical verification, the study "
     "procedure and the results template. Chapter 6 concludes and outlines future work.")

# ---- Chapter 2
page_break()
h1("CHAPTER 2", "BACKGROUND MATERIAL")
h2("2.1 Conceptual Overview")
h3("Screen readers and ARIA")
para("A screen reader converts the content of a page into speech or refreshable Braille. It relies on the accessibility "
     "tree that the browser builds from semantic HTML and WAI-ARIA attributes [16]. An SVG chart is a set of shapes "
     "with no semantics, so it must be complemented with text alternatives, a data table, and live regions "
     "(aria-live) that announce changes as the user navigates.")
h3("Sonification")
para("Sonification is “the use of non-speech audio to convey information” [2]. In parameter-mapping sonification, "
     "each data value controls an audio parameter such as pitch, loudness, timing or spatial position. Pitch is the most "
     "commonly used and best understood mapping for magnitude, and stereo panning can convey position along the x-axis [5].")
h3("Tactile graphics and Braille")
para("Tactile graphics are raised-line images read by touch. They are produced on swell (microcapsule) paper, where "
     "black areas rise when heated, or with Braille embossers. Guidelines recommend thick lines, few labels, distinct "
     "textures instead of colour, and Braille rather than print labels [9]. A Braille Ready File (.brf) stores text in "
     "North American ASCII Braille, 40 cells per line and 25 lines per page, which embossers print directly.")
h2("2.2 Technologies Involved")
table("2.1", "Technology stack used in the project",
      ["Technology", "Purpose"],
      [["HTML5, CSS3", "Semantic page structure, high-contrast and dark-mode styling, visible focus indicators"],
       ["JavaScript (ES2020)", "Application logic with no framework or build step"],
       ["SVG", "On-screen chart rendering and the tactile graphic export"],
       ["Web Audio API", "Oscillators, gain envelopes and stereo panners for sonification [17]"],
       ["Web Speech API", "Spoken summaries for users without a screen reader"],
       ["WAI-ARIA 1.2", "Live regions, role descriptions and labelling for screen readers [16]"],
       ["Vibration API", "Haptic preview of the series on mobile phones"],
       ["Node.js", "Running the automated unit tests"],
       ["Git and GitHub", "Version control and hosting of the source code"]],
      [4.5, 11.4])
h2("2.3 Related Work")
para("Sharif et al. [1] interviewed and observed screen-reader users interacting with online visualisations and found "
     "that they spent much longer than sighted users to extract information and were often less accurate, mainly because "
     "charts lacked usable alternatives. Lundgard and Satyanarayan [3] proposed a four-level model of semantic content for "
     "chart descriptions, from encodings to trends to contextual insight, and found that BLV readers value trend-level "
     "descriptions most. SoniChart's generated summaries follow this guidance by naming the extremes and the overall shape.")
para("Zong et al. [4] designed rich screen-reader experiences that let users navigate a chart hierarchically by keyboard. "
     "Zhao, Plaisant and Shneiderman [5] showed that interactive sonification lets BLV users find patterns in "
     "geographic data. Engel and Weber [10] analysed tactile chart designs and highlighted the importance of reducing "
     "clutter and placing Braille labels carefully. SoniChart combines these strands in one lightweight tool that offers "
     "sound, speech and touch for the same data, and includes the instrumentation needed to compare them.")

# ---- Chapter 3
page_break()
h1("CHAPTER 3", "METHODOLOGY")
h2("3.1 Design Approach")
para("The project follows a user-centred design process: understand the needs of BLV users from the literature [1], [3], "
     "design multiple representations, build a working prototype, and evaluate it with representative users. Three "
     "design principles guided the work:")
bullets(["**Overview first, details on demand:** a spoken summary and a full-series sonification give the overview; "
         "arrow-key navigation gives exact values.",
         "**Redundancy across senses:** every piece of information is available as text, so it also works with a "
         "Braille display; sound and touch add the shape.",
         "**Keyboard first:** every function is reachable without a mouse, and focus is always visible."])
h2("3.2 System Architecture")
para("Fig. 3.1 shows the architecture. A dataset is loaded from the samples or from a CSV file and converted to a "
     "label/value series. The description module computes statistics and the trend. Three output channels then "
     "present the same series, and the study module records participants' answers.")
figure(FIG / "architecture.png", "3.1", "SoniChart system architecture", 15.5)
h2("3.3 Sonification Mapping")
para("Each value is mapped to a frequency between 220 Hz (A3) and 880 Hz (A5) on a logarithmic scale, so equal steps in "
     "value sound like equal musical intervals: f = 220 × 4^t, where t is the value normalised to [0, 1]. The position "
     "of the point is mapped to stereo pan from −1 (left) to +1 (right), so the series moves across the listener's head "
     "like a reader's eye across the chart. A triangle wave with a short attack and exponential decay is used because it "
     "is clear without being harsh. During playback a short high click marks the highest and lowest points. "
     "Fig. 3.2 shows the mapping and how the Jaipur temperature data is played.")
figure(FIG / "sonification_mapping.png", "3.2", "Value-to-pitch mapping and the temperature series as sonified", 15.5)
h2("3.4 Text Descriptions")
para("The description module produces three kinds of text: (1) a **summary** that names the chart type, title, range "
     "of labels, the highest and lowest values with their labels, and the trend; (2) a **point description** such as "
     "“May: 33.6 °C, up 3.9. Point 5 of 12”; and (3) a **trend** phrase. The trend is classified from the position of "
     "the extremes and the overall change: a maximum in the middle with a small net change is reported as “rises to a "
     "peak and then falls”, and a net change larger than a quarter of the range as increasing or decreasing.")
h2("3.5 Tactile Output Design")
table("3.1", "Tactile design decisions and the guideline each follows",
      ["Decision", "Rationale"],
      [["A4 landscape, units in millimetres", "Matches swell paper and embosser page sizes"],
       ["Data lines 1.5 mm, axes 1.2 mm", "Lines must be at least about 1 mm to be felt reliably [9]"],
       ["Dotted texture for bars", "Texture replaces colour, which cannot be felt"],
       ["Only 0 and maximum on the y-axis", "Fewer labels reduce clutter for touch [9], [10]"],
       ["Braille labels, 3-letter x-labels on alternating rows", "Braille cells are wide; this avoids overlap"],
       ["Separate .brf summary and values", "Gives exact numbers that the graphic cannot show"]],
      [6.0, 9.9])
h2("3.6 User Study Design")
para("A within-subjects study compares three conditions: **Table** (an accessible data table, the baseline), "
     "**Sonify** (keyboard exploration with tones and speech) and **Tactile** (the swell-paper graphic and Braille "
     "summary). Condition order is counterbalanced with a Latin square. The target sample is 8–12 adult screen-reader "
     "users who are blind or have low vision, recruited through local organisations for the visually impaired after "
     "ethical approval and informed consent.")
table("3.2", "Study tasks, following the task typology of Brehmer and Munzner [6]",
      ["#", "Dataset", "Task type", "Question"],
      [[str(i), t["dataset"], t["kind"], t["q"]] for i, t in enumerate(TASKS, 1)],
      [0.8, 2.6, 2.2, 10.3], align_num=False)
para("Dependent measures are accuracy, task completion time, workload measured with raw NASA-TLX [8] and usability "
     "measured with the System Usability Scale [7], followed by a short semi-structured interview analysed thematically "
     "[11]. Accuracy is compared with Cochran's Q and pairwise McNemar tests, and time, TLX and SUS with the Friedman "
     "test and Wilcoxon signed-rank post-hoc tests with Bonferroni correction.")

# ---- Chapter 4
page_break()
h1("CHAPTER 4", "IMPLEMENTATION")
h2("4.1 Modules")
table("4.1", f"Source modules (repository: {REPO})",
      ["File", "Responsibility"],
      [["index.html", "Page structure, labelled controls, ARIA live region, keyboard help"],
       ["css/style.css", "High-contrast light and dark themes, 4 px focus outline, 40 px minimum targets"],
       ["js/data.js", "Sample datasets and CSV parsing"],
       ["js/describe.js", "Statistics, trend classification, summaries and point descriptions"],
       ["js/chart.js", "SVG line and bar chart with a moving focus cursor"],
       ["js/sonify.js", "Web Audio sonification: pitch and pan mapping, playback, extreme clicks"],
       ["js/braille.js", "Grade-1 English Braille to Unicode cells and ASCII Braille"],
       ["js/tactile.js", "Tactile SVG, .brf file generation, vibration patterns"],
       ["js/study.js", "Study tasks, timing, scoring and CSV export"],
       ["js/app.js", "Event handling and glue between modules"],
       ["tests/run.js", f"{N_TESTS} automated unit tests"]],
      [3.6, 12.3])
h2("4.2 Interaction Design")
para("The chart region is a focusable element with role “application” and a role description of “interactive chart”, "
     "so screen readers pass arrow keys to the page. Its description points to the generated summary and the keyboard "
     "help. Every key press updates a polite ARIA live region, which the screen reader reads aloud, and plays the "
     "point's tone.")
table("4.2", "Keyboard commands", ["Key", "Action"],
      [["← / →", "Previous / next point (tone + spoken description)"], ["Home / End", "First / last point"],
       ["Space", "Play the whole series"], ["S", "Speak the summary"], ["T", "Speak the trend"],
       ["H / L", "Jump to the highest / lowest point"], ["Esc", "Stop sound"]], [3.5, 12.4], align_num=False)
h2("4.3 User Interface")
para("Fig. 4.1 shows the interface. The panels are numbered in the order a user would work through them, every control "
     "has a visible label, and the summary is shown above the chart so that sighted helpers and low-vision users see the "
     "same text the screen reader announces. The colour scheme follows the operating system's light or dark setting, and "
     "the button colours were checked for sufficient contrast in both themes.")
figure(SCR / "app_full.png", "4.1", "SoniChart interface (light theme) with summary, chart, sonification and tactile controls", 12.5)
h2("4.4 Tactile Output")
para("Fig. 4.2 and Fig. 4.3 show the generated tactile graphics, which are ready to print on swell paper. The labels are "
     "Unicode Braille. Below is the .brf file generated for the sales chart, in ASCII Braille as sent to an embosser:")
code(BRF_SAMPLE, 9)
figure(SCR / "tactile_temp.png", "4.2", "Tactile line chart of Jaipur temperature with Braille labels", 14.5)
figure(SCR / "tactile_sales.png", "4.3", "Tactile bar chart of quarterly sales with dotted texture", 14.5)
h2("4.5 Testing")
para("The non-visual logic is tested automatically with Node.js. The tests check the Braille letters, capital and number "
     "signs, the difference between a decimal point and a full stop, the pitch and pan ranges, trend classification, "
     "point descriptions, the tactile page size and Braille labels, the 40-cell line limit of .brf files, CSV parsing and "
     "the study answer key. All tests pass:")
code(TEST_OUTPUT, 8.5)

# ---- Chapter 5
page_break()
h1("CHAPTER 5", "EVALUATION AND RESULTS")
h2("5.1 Technical Verification")
para("Before any study with participants, the prototype was checked against the following criteria:")
table("5.1", "Technical verification checklist",
      ["Check", "Method", "Outcome"],
      [["Keyboard-only operation", "All controls and chart navigation used without a mouse", "Pass"],
       ["Live announcements", "Arrow keys produce text such as “May: 33.6 °C, up 3.9. Point 5 of 12.”", "Pass"],
       ["Summary correctness", "Extremes and trend checked against the sample data (unit tests)", "Pass"],
       ["Braille translation", "Letters, capitals, numbers, punctuation (unit tests)", "Pass"],
       ["BRF format", "Lines ≤ 40 cells, word wrapping, page breaks (unit tests)", "Pass"],
       ["Contrast", "Button text in light and dark themes; fixed a low-contrast dark-mode button", "Pass after fix"],
       ["Tactile layout", "A4 page size, line widths, label overlap inspected visually", "Pass"]],
      [3.8, 9.4, 2.7], align_num=False)
h2("5.2 Study Procedure")
para("Each session lasts about 45 minutes: consent and demographics; a short training for each condition with a "
     "practice chart; the six tasks per condition presented through study mode, where the researcher reads each question "
     "aloud and records the spoken answer; NASA-TLX and SUS after each condition; and a 10-minute interview. Study mode "
     "records the time from question to submitted answer and scores the answer automatically. The full protocol, "
     "including ethics considerations, is in the repository at docs/study-protocol.md.")
h2("5.3 Results")
p = para()
add_rich(p, "**Note:** the tables below are the reporting template for the user study. The values are to be filled in "
            "from the exported study logs and questionnaires after the sessions with blind and low-vision participants "
            "have been conducted; no participant data is reported here.")
table("5.2", "Participant demographics (to be completed)",
      ["ID", "Age range", "Vision status", "Screen reader", "Braille reader", "Chart use"],
      [[f"P{i:02d}", "", "", "", "", ""] for i in range(1, 9)],
      [1.4, 2.2, 3.0, 3.2, 2.6, 3.5], align_num=False)
table("5.3", "Accuracy and completion time per condition (mean ± SD, to be completed)",
      ["Condition", "Accuracy (%)", "Time (s)", "NASA-TLX (0–100)", "SUS (0–100)"],
      [["Table (baseline)", "", "", "", ""], ["Sonify + speech", "", "", "", ""], ["Tactile", "", "", "", ""]],
      [3.8, 3.0, 3.0, 3.2, 2.9], align_num=False)
table("5.4", "Accuracy per task type and condition (%, to be completed)",
      ["Task type", "Table", "Sonify", "Tactile"],
      [["Retrieve value", "", "", ""], ["Compare", "", "", ""], ["Find extreme", "", "", ""], ["Trend", "", "", ""]],
      [4.9, 3.6, 3.6, 3.6], align_num=False)
para("**Hypotheses.** Based on prior work [1], [3], [5], we expect (H1) sonification and tactile graphics to be at least "
     "as accurate as the table for extreme and trend tasks while being faster, because the shape is perceived at once "
     "rather than read value by value; (H2) the table to remain best for exact value retrieval; and (H3) Braille readers "
     "to prefer the tactile graphic, and other participants the sonification.")
h2("5.4 Discussion and Limitations")
bullets(["The sonification depends on pitch perception and headphones for panning; participants with hearing loss may "
         "need the tactile or text channel instead.",
         "Tactile graphics require swell paper and a heater or an embosser, which not every user has at home.",
         "The Braille translation is Grade 1 (uncontracted); many experienced readers prefer Grade 2 contracted Braille.",
         "The prototype supports single-series line and bar charts; multi-series and scatter plots are not yet supported.",
         "A study with 8–12 participants gives limited statistical power; results should be read as indicative."])

# ---- Chapter 6
page_break()
h1("CHAPTER 6", "CONCLUSIONS & FUTURE SCOPE")
h2("6.1 Conclusions")
para("This project designed and built SoniChart, a browser-based tool that makes line and bar charts accessible to blind "
     "and low-vision users through sonification, screen-reader-friendly speech and text, and tactile output with "
     "Braille. The design follows established accessibility guidance: keyboard-first interaction, overview-first "
     "summaries, logarithmic pitch mapping with spatial panning, and tactile graphics with thick lines, textures and few "
     "Braille labels. The implementation is lightweight, needs no installation, and its core logic is covered by "
     f"{N_TESTS} passing automated tests. A complete within-subjects study protocol and an integrated study mode make it "
     "possible to measure how each modality affects accuracy, speed, workload and usability for its intended users.")
h2("6.2 Future Scope of Work")
bullets(["Conduct the planned study with BLV participants and refine the design from the findings.",
         "Add Grade 2 contracted Braille through the open-source Liblouis library.",
         "Support multi-series charts with different timbres per series, and scatter plots.",
         "Add speech-recognition queries such as “what is the value in July?”.",
         "Integrate with refreshable Braille displays and pin-array tactile displays for dynamic tactile charts.",
         "Package SoniChart as a browser extension that adds these features to charts on existing websites."],
        numbered=True)

# ---- References
page_break()
p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=2, line=1.0); run(p, "REFERENCES", 14, True)
p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=12, line=1.0); run(p, "(IEEE Format)", 14, True)
refs_j = [
    "[1] A. Sharif, S. S. Chintalapati, J. O. Wobbrock and K. Reinecke, “Understanding Screen-Reader Users’ Experiences with Online Data Visualizations”, Proceedings of the 23rd International ACM SIGACCESS Conference on Computers and Accessibility (ASSETS), 2021, pp. 1–16.",
    "[2] G. Kramer et al., “Sonification Report: Status of the Field and Research Agenda”, International Community for Auditory Display, 1999.",
    "[3] A. Lundgard and A. Satyanarayan, “Accessible Visualization via Natural Language Descriptions: A Four-Level Model of Semantic Content”, IEEE Transactions on Visualization and Computer Graphics, vol. 28, no. 1, 2022, pp. 1073–1083.",
    "[4] J. Zong, C. Lee, A. Lundgard, J. Jang, D. Hajas and A. Satyanarayan, “Rich Screen Reader Experiences for Accessible Data Visualization”, Computer Graphics Forum, vol. 41, no. 3, 2022, pp. 15–27.",
    "[5] H. Zhao, C. Plaisant, B. Shneiderman and J. Lazar, “Data Sonification for Users with Visual Impairment: A Case Study with Georeferenced Data”, ACM Transactions on Computer-Human Interaction, vol. 15, no. 1, 2008, pp. 1–28.",
    "[6] M. Brehmer and T. Munzner, “A Multi-Level Typology of Abstract Visualization Tasks”, IEEE Transactions on Visualization and Computer Graphics, vol. 19, no. 12, 2013, pp. 2376–2385.",
    "[7] J. Brooke, “SUS: A ‘Quick and Dirty’ Usability Scale”, in Usability Evaluation in Industry, Taylor & Francis, 1996, pp. 189–194.",
    "[8] S. G. Hart and L. E. Staveland, “Development of NASA-TLX (Task Load Index): Results of Empirical and Theoretical Research”, Advances in Psychology, vol. 52, 1988, pp. 139–183.",
    "[10] C. Engel and G. Weber, “Analysis of Tactile Chart Design”, Proceedings of the 10th International Conference on PErvasive Technologies Related to Assistive Environments (PETRA), 2017, pp. 197–200.",
    "[11] V. Braun and V. Clarke, “Using Thematic Analysis in Psychology”, Qualitative Research in Psychology, vol. 3, no. 2, 2006, pp. 77–101.",
]
refs_b = [
    "[9] Braille Authority of North America, “Guidelines and Standards for Tactile Graphics”, BANA, 2010.",
    "[12] T. Hermann, A. Hunt and J. G. Neuhoff (Eds.), “The Sonification Handbook”, Logos Publishing House, Berlin, 1st Edition, ISBN 978-3832528195.",
    "[13] A. Dix, J. Finlay, G. D. Abowd and R. Beale, “Human-Computer Interaction”, Pearson, 3rd Edition, ISBN 978-0130461094.",
]
refs_w = [
    "[14] World Health Organization, “World Report on Vision”, who.int, Last accessed 17 November 2026.",
    "[15] W3C, “Web Content Accessibility Guidelines (WCAG) 2.2”, w3.org/TR/WCAG22, Last accessed 17 November 2026.",
    "[16] W3C, “Accessible Rich Internet Applications (WAI-ARIA) 1.2”, w3.org/TR/wai-aria-1.2, Last accessed 17 November 2026.",
    "[17] MDN Web Docs, “Web Audio API”, developer.mozilla.org, Last accessed 17 November 2026.",
]
for head, refs in (("Journal / Conference Papers", refs_j), ("Reference / Handbooks", refs_b), ("Web", refs_w)):
    p = para(after=3, line=1.15, before=8); run(p, head, 11, True, True)
    for r_ in refs:
        p = para(r_, size=11, after=3, line=1.15, align=WD_ALIGN_PARAGRAPH.LEFT)
        p.paragraph_format.left_indent, p.paragraph_format.first_line_indent = Cm(0.8), Cm(-0.8)

# ---- Annexures
page_break()
h1("", "ANNEXURES")
h2("Annexure A: Source Code and Running the Project")
para(f"Source code repository: **{REPO}**")
code('''git clone https://github.com/21amY26/SoniChart.git
cd SoniChart
python3 -m http.server 8765     # then open http://localhost:8765
node tests/run.js               # run the unit tests''')
h2("Annexure B: Study Session Checklist")
bullets(["Ethics approval obtained and consent form available in an accessible format.",
         "Laptop with screen reader, headphones, swell-paper prints of the tactile charts and the .brf printouts ready.",
         "Participant ID set in study mode; condition order taken from the Latin square.",
         "After each condition: NASA-TLX and SUS asked verbally; log exported with “Export log (CSV)”.",
         "Interview audio recorded only with consent; files stored under participant ID."], numbered=True)

# ---------------------------------------------------------------- 4. front-matter lists and contents
anchor = lt_slot._element
list_table("LIST OF TABLES", [(f"Table {n}", t, pg(f"Table {n}")) for n, t in TABS], "Table")
list_table("LIST OF FIGURES", [(f"Fig. {n}", t, pg(f"Fig. {n}")) for n, t in FIGS], "Figure")
blocks = list(body.iterchildren())
start = blocks.index(next(el for el in blocks if el.tag == qn("w:p") and "LIST OF TABLES" in el.xpath("string(.)")))
for el in blocks[start:-1]:
    anchor.addprevious(el)
body.remove(anchor)

TOC = [("Acknowledgement", None, None, "Acknowledgement"), ("Abstract", None, None, "Abstract"),
       ("List Of Tables", None, None, "List of Tables"), ("List Of Figures", None, None, "List of Figures")]
chapters = [
    ("Chapter 1", "INTRODUCTION", [("1.1", "Introduction and Motivation (Applications & Advantages)"),
                                   ("1.2", "Problem Statement and Objectives"), ("1.3", "Organization of the Report")]),
    ("Chapter 2", "BACKGROUND MATERIAL", [("2.1", "Conceptual Overview"), ("2.2", "Technologies Involved"), ("2.3", "Related Work")]),
    ("Chapter 3", "METHODOLOGY", [("3.1", "Design Approach"), ("3.2", "System Architecture"), ("3.3", "Sonification Mapping"),
                                  ("3.4", "Text Descriptions"), ("3.5", "Tactile Output Design"), ("3.6", "User Study Design")]),
    ("Chapter 4", "IMPLEMENTATION", [("4.1", "Modules"), ("4.2", "Interaction Design"), ("4.3", "User Interface"),
                                     ("4.4", "Tactile Output"), ("4.5", "Testing")]),
    ("Chapter 5", "EVALUATION AND RESULTS", [("5.1", "Technical Verification"), ("5.2", "Study Procedure"),
                                             ("5.3", "Results"), ("5.4", "Discussion and Limitations")]),
    ("Chapter 6", "CONCLUSIONS & FUTURE SCOPE", [("6.1", "Conclusions"), ("6.2", "Future Scope of Work")]),
]
p = para(align=WD_ALIGN_PARAGRAPH.CENTER, after=8, line=1.0); run(p, "Contents", 16, True)
rows = [("", "", "Page No", True)]
rows += [(a, "", pg(k), True) for a, _, _, k in TOC]
for chap, title, secs in chapters:
    rows.append((chap, title, pg(chap), True))
    rows += [(f"    {n}", t, pg(n), False) for n, t in secs]
rows += [("REFERENCES", "", pg("REFERENCES"), True), ("ANNEXURES", "", pg("ANNEXURES"), True)]
t = doc.add_table(rows=len(rows), cols=3); set_cell_borders(t, False)
for i, (a, b, c, bold) in enumerate(rows):
    for j, (val, w) in enumerate(zip((a, b, c), (2.8, 11.0, 2.0))):
        cell = t.cell(i, j); cell.width = Cm(w)
        pp = cell.paragraphs[0]; pp.paragraph_format.space_after = Pt(2)
        pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j == 2 else WD_ALIGN_PARAGRAPH.LEFT
        run(pp, val, 11, bold=bold and j < 2 or i == 0)
set_widths(t, [2.8, 11.0, 2.0])
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (a, b, c, bold) in enumerate(rows):
    if i and a and not b:
        t.cell(i, 0).merge(t.cell(i, 1))
blocks = list(body.iterchildren())
start = blocks.index(next(el for el in blocks if el.tag == qn("w:p") and el.xpath("string(.)").strip() == "Contents"))
for el in blocks[start:-1]:
    toc_slot._element.addprevious(el)
body.remove(toc_slot._element)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print(OUT, "sections:", len(doc.sections), "figures:", len(FIGS), "tables:", len(TABS))
