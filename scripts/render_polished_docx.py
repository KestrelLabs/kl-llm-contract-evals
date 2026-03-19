from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "WRITEUP.md"
OUTPUT = ROOT / "WRITEUP_polished.docx"


@dataclass
class CodeBlock:
    language: str
    content: str


@dataclass
class TableBlock:
    rows: list[list[str]]


@dataclass
class HeadingBlock:
    level: int
    text: str


@dataclass
class ParagraphBlock:
    text: str


@dataclass
class BulletBlock:
    items: list[str]
    ordered: bool = False


@dataclass
class RuleBlock:
    pass


@dataclass
class BlufBlock:
    blocks: list[object]


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_paragraph_border(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6")
        el.set(qn("w:space"), "6")
        el.set(qn("w:color"), "D9E2F3")
        p_bdr.append(el)
    p_pr.append(p_bdr)


def strip_md_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def parse_table(lines: list[str], idx: int):
    rows: list[list[str]] = []
    start = idx
    while idx < len(lines):
        line = lines[idx]
        if "|" not in line or not line.strip():
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        idx += 1
    if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in rows[1]):
        header = rows[0]
        body = rows[2:]
        width = len(header)
        normalized = [header[:width]] + [r[:width] + [""] * max(0, width - len(r)) for r in body]
        return TableBlock(normalized), idx
    return None, start


def parse_blocks(text: str) -> list[object]:
    lines = text.splitlines()
    blocks: list[object] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            blocks.append(RuleBlock())
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 2 and text == "BLUF":
                i += 1
                inner: list[object] = []
                buf: list[str] = []
                while i < len(lines):
                    s = lines[i].strip()
                    if s == "---":
                        if buf:
                            inner.append(ParagraphBlock(" ".join(buf).strip()))
                            buf = []
                        break
                    if s.startswith("- "):
                        if buf:
                            inner.append(ParagraphBlock(" ".join(buf).strip()))
                            buf = []
                        items = []
                        while i < len(lines) and lines[i].strip().startswith("- "):
                            items.append(strip_md_inline(lines[i].strip()[2:]))
                            i += 1
                        inner.append(BulletBlock(items))
                        continue
                    if s:
                        buf.append(strip_md_inline(s))
                    i += 1
                if buf:
                    inner.append(ParagraphBlock(" ".join(buf).strip()))
                blocks.append(BlufBlock(inner))
                continue
            blocks.append(HeadingBlock(level, strip_md_inline(text)))
            i += 1
            continue

        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            content_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                content_lines.append(lines[i].rstrip("\n"))
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(CodeBlock(lang, "\n".join(content_lines).rstrip()))
            continue

        table_block, new_i = parse_table(lines, i)
        if table_block is not None:
            blocks.append(table_block)
            i = new_i
            continue

        if re.match(r"^-\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^-\s+", lines[i].strip()):
                items.append(strip_md_inline(re.sub(r"^-\s+", "", lines[i].strip())))
                i += 1
            blocks.append(BulletBlock(items))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(strip_md_inline(re.sub(r"^\d+\.\s+", "", lines[i].strip())))
                i += 1
            blocks.append(BulletBlock(items, ordered=True))
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(strip_md_inline(lines[i].strip()[1:].strip()))
                i += 1
            blocks.append(ParagraphBlock(" ".join(quote_lines)))
            continue

        para = [strip_md_inline(stripped)]
        i += 1
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                break
            if s == "---" or s.startswith("#") or s.startswith("```") or s.startswith("- ") or re.match(r"^\d+\.\s+", s) or "|" in s:
                break
            para.append(strip_md_inline(s))
            i += 1
        blocks.append(ParagraphBlock(" ".join(para).strip()))
    return blocks


def style_document(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(11)

    for style_name, size, color in [
        ("Title", 24, RGBColor(27, 45, 94)),
        ("Heading 1", 16, RGBColor(27, 45, 94)),
        ("Heading 2", 13, RGBColor(46, 84, 150)),
        ("Heading 3", 11, RGBColor(46, 84, 150)),
    ]:
        style = doc.styles[style_name]
        style.font.name = "Aptos"
        style.font.size = Pt(size)
        style.font.color.rgb = color


def add_title_page(doc: Document, title: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    r.bold = True
    r.font.name = "Aptos Display"
    r.font.size = Pt(24)
    r.font.color.rgb = RGBColor(27, 45, 94)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Paper draft generated from the Markdown source")
    r2.italic = True
    r2.font.name = "Aptos"
    r2.font.size = Pt(11)
    r2.font.color.rgb = RGBColor(96, 96, 96)

    p3 = doc.add_paragraph()
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("Kestrel Labs / kestrel-evals")
    r3.font.name = "Aptos"
    r3.font.size = Pt(10)
    r3.font.color.rgb = RGBColor(96, 96, 96)

    doc.add_paragraph()
    doc.add_page_break()


def render_bluf(doc: Document, block: BlufBlock) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    set_cell_shading(cell, "EEF3FB")

    p = cell.paragraphs[0]
    r = p.add_run("BLUF")
    r.bold = True
    r.font.name = "Aptos"
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(27, 45, 94)

    for inner in block.blocks:
        if isinstance(inner, ParagraphBlock):
            p = cell.add_paragraph()
            r = p.add_run(inner.text)
            r.font.name = "Aptos"
            r.font.size = Pt(11)
        elif isinstance(inner, BulletBlock):
            for item in inner.items:
                p = cell.add_paragraph(style="List Bullet")
                r = p.add_run(item)
                r.font.name = "Aptos"
                r.font.size = Pt(10.5)
    doc.add_paragraph()


def render_heading(doc: Document, block: HeadingBlock) -> None:
    if block.level == 1:
        return
    style = {2: "Heading 1", 3: "Heading 2", 4: "Heading 3"}.get(block.level, "Heading 3")
    doc.add_paragraph(block.text, style=style)


def render_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    for part in re.split(r"(`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            r = p.add_run(part[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(10)
        else:
            r = p.add_run(part)
            r.font.name = "Aptos"
            r.font.size = Pt(11)


def render_bullets(doc: Document, block: BulletBlock) -> None:
    style = "List Number" if block.ordered else "List Bullet"
    for item in block.items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(item)
        r.font.name = "Aptos"
        r.font.size = Pt(10.5)


def render_code(doc: Document, block: CodeBlock) -> None:
    if block.language == "mermaid":
        p = doc.add_paragraph()
        r = p.add_run("Architecture diagram (Mermaid source)")
        r.bold = True
        r.font.name = "Aptos"
        r.font.size = Pt(10.5)
        r.font.color.rgb = RGBColor(96, 96, 96)

    for line in block.content.splitlines() or [""]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Inches(0.2)
        set_paragraph_border(p)
        r = p.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(44, 44, 44)


def render_table(doc: Document, block: TableBlock) -> None:
    if not block.rows:
        return
    rows = len(block.rows)
    cols = max(len(r) for r in block.rows)
    table = doc.add_table(rows=rows, cols=cols)
    table.style = "Light List Accent 1"
    table.autofit = True
    for i, row in enumerate(block.rows):
        for j in range(cols):
            text = row[j] if j < len(row) else ""
            cell = table.cell(i, j)
            cell.text = text
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Aptos"
                    r.font.size = Pt(10)
                if i == 0:
                    for r in p.runs:
                        r.bold = True
    doc.add_paragraph()


def render_rule(doc: Document) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("")
    set_paragraph_border(p)


def main() -> None:
    text = INPUT.read_text(encoding="utf-8")
    blocks = parse_blocks(text)
    if not blocks or not isinstance(blocks[0], HeadingBlock):
        raise RuntimeError("Expected first block to be H1 title")
    title = blocks[0].text

    doc = Document()
    style_document(doc)
    add_title_page(doc, title)

    for block in blocks[1:]:
        if isinstance(block, BlufBlock):
            render_bluf(doc, block)
        elif isinstance(block, HeadingBlock):
            render_heading(doc, block)
        elif isinstance(block, ParagraphBlock):
            render_paragraph(doc, block.text)
        elif isinstance(block, BulletBlock):
            render_bullets(doc, block)
        elif isinstance(block, CodeBlock):
            render_code(doc, block)
        elif isinstance(block, TableBlock):
            render_table(doc, block)
        elif isinstance(block, RuleBlock):
            # Use whitespace rather than visible divider inside the Word version.
            doc.add_paragraph()

    doc.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
