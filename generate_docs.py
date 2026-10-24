import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DIR = r"C:\Users\user\.gemini\antigravity\scratch\adaptive-tool-scoping"
DOC1_PATH = os.path.join(OUTPUT_DIR, "Document_1_Project_Overview_and_Research_Architecture.docx")
DOC2_PATH = os.path.join(OUTPUT_DIR, "Document_2_Page_by_Page_UI_and_Code_Implementation_Guide.docx")

# Styling Palette Constants
COLOR_NAVY = RGBColor(12, 63, 110)      # Primary Header
COLOR_SKY = RGBColor(2, 132, 199)       # Sub-Header Accent
COLOR_SLATE = RGBColor(51, 65, 85)      # Body Dark Text
COLOR_MUTED = RGBColor(100, 116, 139)   # Metadata / Footnote
COLOR_DANGER = RGBColor(220, 38, 38)    # Threat / Warning
COLOR_SUCCESS = RGBColor(22, 163, 74)   # Success / Secure

HEX_LIGHT_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_NAVY = "0C3F6E"
HEX_SKY_BG = "F0F9FF"
HEX_CODE_BG = "F1F5F9"
HEX_CALLOUT_BORDER = "0284C7"
HEX_DANGER_BG = "FEF2F2"
HEX_DANGER_BORDER = "EF4444"


def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_custom_heading(doc, text, level):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    p.paragraph_format.keep_with_next = True

    if level == 1:
        run.font.size = Pt(18)
        run.font.color.rgb = COLOR_NAVY
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        # Add a subtle bottom border or separator line
    elif level == 2:
        run.font.size = Pt(14)
        run.font.color.rgb = COLOR_SKY
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.size = Pt(11.5)
        run.font.color.rgb = COLOR_SLATE
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
    return p


def add_callout(doc, title, text, callout_type="info"):
    bg_color = HEX_SKY_BG if callout_type == "info" else HEX_DANGER_BG
    border_color = HEX_CALLOUT_BORDER if callout_type == "info" else HEX_DANGER_BORDER
    title_color = COLOR_SKY if callout_type == "info" else COLOR_DANGER

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)

    # Left colored accent border
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:top w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    run_title = p.add_run(f"📌 {title}\n" if callout_type == "info" else f"⚠️ {title}\n")
    run_title.bold = True
    run_title.font.size = Pt(10)
    run_title.font.color.rgb = title_color

    run_text = p.add_run(text)
    run_text.font.size = Pt(9.5)
    run_text.font.color.rgb = COLOR_SLATE

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc, code_str, language=""):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    cell = table.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, HEX_CODE_BG)
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)

    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="12" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:right w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{HEX_BORDER}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05

    if language:
        lang_run = p.add_run(f"// {language}\n")
        lang_run.font.name = "Consolas"
        lang_run.font.size = Pt(8.5)
        lang_run.font.color.rgb = COLOR_MUTED
        lang_run.bold = True

    code_run = p.add_run(code_str)
    code_run.font.name = "Consolas"
    code_run.font.size = Pt(8.5)
    code_run.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_styled_table(doc, headers, rows_data, col_widths=None):
    table = doc.add_table(rows=len(rows_data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], HEX_NAVY)
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=120, right=120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for r_idx, row in enumerate(rows_data):
        row_cells = table.rows[r_idx + 1].cells
        bg_col = "FFFFFF" if r_idx % 2 == 0 else HEX_LIGHT_BG
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=120, right=120)
            p = row_cells[c_idx].paragraphs[0]
            for run in p.runs:
                run.font.size = Pt(9.0)
                run.font.color.rgb = COLOR_SLATE

    # Apply Col Widths if specified
    if col_widths:
        for row in table.rows:
            for c_idx, w in enumerate(col_widths):
                row.cells[c_idx].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


print("Ready to generate Word documents...")
