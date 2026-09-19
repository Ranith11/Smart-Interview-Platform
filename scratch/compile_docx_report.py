import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Sets background color for a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding (in twentieths of a point, dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tc_pr.append(tc_mar)

def set_table_borders(table, color="CCCCCC", sz="4", val="single"):
    """Sets clean subtle borders for a table."""
    tbl_pr = table._tbl.tblPr
    tbl_borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tbl_pr.append(tbl_borders)

def add_styled_paragraph(doc, text, style='Normal', space_before=0, space_after=4, line_spacing=1.15, bold=False, italic=False, font_size=10.5, color_rgb=(45, 55, 72)):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)
    return p

def format_inlines(paragraph, text, base_font_size=10.5, default_color=(45, 55, 72)):
    """Parses simple inline markdown: **bold**, *italic*, `code`, [link](url)."""
    # Regex to tokenize markdown inlines
    tokens = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(20, 20, 20)
        elif token.startswith('*') and token.endswith('*') and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(*default_color)
        elif token.startswith('`') and token.endswith('`') and len(token) > 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(base_font_size * 0.92)
            run.font.color.rgb = RGBColor(180, 40, 40)
        else:
            run = paragraph.add_run(token)
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(*default_color)

def compile_markdown_to_docx(md_path, docx_path):
    print(f"Reading markdown from: {md_path}")
    with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    doc = docx.Document()
    
    # Page Margins (1 inch all around)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("SmartInterview: Adaptive Technical Mock Interview Platform | Academic Report")
        hrun.font.name = 'Calibri'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(140, 150, 160)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Bachelor of Technology Final Project Documentation — Confidential & Academic Use")
        frun.font.name = 'Calibri'
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(160, 160, 160)

    # Styles
    navy = (27, 54, 93)       # #1B365D
    slate_blue = (44, 82, 130) # #2C5282
    dark_slate = (45, 55, 72)  # #2D3748
    body_color = (30, 41, 59)  # #1E293B

    i = 0
    total_lines = len(lines)
    in_code_block = False
    code_lines = []
    
    while i < total_lines:
        line = lines[i].rstrip('\r\n')
        
        # Check code block toggle
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block, emit table or styled paragraph block
                code_text = '\n'.join(code_lines)
                table = doc.add_table(rows=1, cols=1)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_borders(table, color="CBD5E0", sz="4", val="single")
                cell = table.cell(0, 0)
                set_cell_background(cell, "F7FAFC")
                set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(2)
                cp.paragraph_format.space_after = Pt(2)
                cp.paragraph_format.line_spacing = 1.05
                run = cp.add_run(code_text)
                run.font.name = 'Consolas'
                run.font.size = Pt(9.0)
                run.font.color.rgb = RGBColor(40, 50, 60)
                # Spacer
                p_spacer = doc.add_paragraph()
                p_spacer.paragraph_format.space_before = Pt(0)
                p_spacer.paragraph_format.space_after = Pt(4)
                
                in_code_block = False
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()
        
        # Empty line
        if not stripped:
            i += 1
            continue
            
        # Horizontal Rule
        if stripped in ('---', '***', '___'):
            # subtle divider paragraph
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run("―" * 45)
            run.font.name = 'Calibri'
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(200, 210, 220)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            i += 1
            continue

        # Check Markdown Table
        if '|' in stripped and i + 1 < total_lines and '|' in lines[i+1] and re.search(r':?-+:?', lines[i+1]):
            # Start of table!
            table_raw_rows = []
            table_raw_rows.append([c.strip() for c in stripped.strip('|').split('|')])
            # Skip separator line
            i += 2
            while i < total_lines and '|' in lines[i].strip() and lines[i].strip():
                table_raw_rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                i += 1
            
            # Create docx table
            num_rows = len(table_raw_rows)
            num_cols = max(len(r) for r in table_raw_rows) if num_rows > 0 else 1
            table = doc.add_table(rows=num_rows, cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_table_borders(table, color="CBD5E0", sz="4", val="single")
            
            for row_idx, r_data in enumerate(table_raw_rows):
                is_header = (row_idx == 0)
                row = table.rows[row_idx]
                for col_idx in range(num_cols):
                    cell = row.cells[col_idx]
                    cell_text = r_data[col_idx] if col_idx < len(r_data) else ""
                    set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
                    cp = cell.paragraphs[0]
                    cp.paragraph_format.space_before = Pt(2)
                    cp.paragraph_format.space_after = Pt(2)
                    cp.paragraph_format.line_spacing = 1.05
                    
                    if is_header:
                        set_cell_background(cell, "1B365D") # Navy Header
                        run = cp.add_run(cell_text)
                        run.font.name = 'Calibri'
                        run.font.size = Pt(9.5)
                        run.font.bold = True
                        run.font.color.rgb = RGBColor(255, 255, 255)
                    else:
                        bg_col = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
                        set_cell_background(cell, bg_col)
                        format_inlines(cp, cell_text, base_font_size=9.5, default_color=(30, 41, 59))
            
            p_post = doc.add_paragraph()
            p_post.paragraph_format.space_before = Pt(0)
            p_post.paragraph_format.space_after = Pt(6)
            continue

        # Heading 1 (# ...)
        if stripped.startswith('# '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[2:])
            run.font.name = 'Calibri'
            run.font.size = Pt(22)
            run.font.bold = True
            run.font.color.rgb = RGBColor(*navy)
            i += 1
            continue

        # Heading 2 (## ...)
        if stripped.startswith('## '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[3:])
            run.font.name = 'Calibri'
            run.font.size = Pt(15)
            run.font.bold = True
            run.font.color.rgb = RGBColor(*slate_blue)
            i += 1
            continue

        # Heading 3 (### ...)
        if stripped.startswith('### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(11)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[4:])
            run.font.name = 'Calibri'
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.color.rgb = RGBColor(*dark_slate)
            i += 1
            continue

        # Heading 4 (#### ...)
        if stripped.startswith('#### '):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(stripped[5:])
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = RGBColor(*dark_slate)
            i += 1
            continue

        # Blockquotes (> ...)
        if stripped.startswith('>'):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.left_indent = Inches(0.3)
            clean_quote = stripped.lstrip('> ').strip()
            format_inlines(p, clean_quote, base_font_size=10.0, default_color=(75, 85, 99))
            i += 1
            continue

        # Bullet lists (- ... or * ...)
        if stripped.startswith('- ') or stripped.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            format_inlines(p, stripped[2:], base_font_size=10.5, default_color=body_color)
            i += 1
            continue

        # Numbered list (1. ...)
        num_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if num_match:
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            format_inlines(p, num_match.group(2), base_font_size=10.5, default_color=body_color)
            i += 1
            continue

        # Regular Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        format_inlines(p, stripped, base_font_size=10.5, default_color=body_color)
        i += 1

    print(f"Saving compiled DOCX to: {docx_path}")
    doc.save(docx_path)
    print("Compilation finished successfully!")

if __name__ == '__main__':
    md_file = os.path.abspath(r"c:\Users\kondu\Downloads\Smart-Interview-main (1)\Smart-Interview-main\docs\SmartInterview_Academic_Project_Report.md")
    docx_file = os.path.abspath(r"c:\Users\kondu\Downloads\Smart-Interview-main (1)\Smart-Interview-main\SmartInterview_Master_Technical_Documentation.docx")
    compile_markdown_to_docx(md_file, docx_file)
