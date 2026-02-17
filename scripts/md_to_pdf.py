#!/usr/bin/env python3
"""
Конвертация Markdown в PDF.
Использует reportlab для поддержки Unicode (русский язык).
Запуск: python scripts/md_to_pdf.py input.md output.pdf
"""
import os
import platform
import sys
from pathlib import Path


def _register_cyrillic_font():
    """Регистрирует шрифт с поддержкой кириллицы."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_name = "CyrillicFont"
    system = platform.system()
    if system == "Windows":
        font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        font_file = "arial.ttf"
    elif system == "Darwin":
        font_dir = "/Library/Fonts"
        font_file = "Arial.ttf"
    else:
        font_dir = "/usr/share/fonts/truetype/dejavu"
        font_file = "DejaVuSans.ttf"

    font_path = os.path.join(font_dir, font_file)
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name
    raise FileNotFoundError(f"Шрифт для кириллицы не найден: {font_path}")


def md_to_pdf(md_path: str | Path, pdf_path: str | Path) -> None:
    """Конвертировать MD файл в PDF."""
    md_path = Path(md_path)
    pdf_path = Path(pdf_path)

    if not md_path.exists():
        raise FileNotFoundError(f"Файл не найден: {md_path}")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer
    except ImportError:
        raise ImportError("Установите reportlab: pip install reportlab")

    font_name = _register_cyrillic_font()
    md_content = md_path.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Cyrillic",
            fontName=font_name,
            fontSize=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CyrillicHeading1",
            fontName=font_name,
            fontSize=16,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CyrillicHeading2",
            fontName=font_name,
            fontSize=13,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CyrillicCode",
            fontName=font_name,
            fontSize=8,
            leftIndent=20,
            backColor="#f0f0f0",
        )
    )

    story = []
    in_code_block = False
    code_lines = []

    for line in md_content.split("\n"):
        if line.strip().startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines).replace("&", "&amp;").replace("<", "&lt;")
                story.append(Preformatted(code_text, styles["CyrillicCode"]))
                story.append(Spacer(1, 6))
                code_lines = []
            in_code_block = not in_code_block
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["CyrillicHeading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["CyrillicHeading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["CyrillicHeading2"]))
        elif line.strip():
            story.append(Paragraph(line, styles["Cyrillic"]))
        else:
            story.append(Spacer(1, 6))

    if code_lines:
        code_text = "\n".join(code_lines).replace("&", "&amp;").replace("<", "&lt;")
        story.append(Preformatted(code_text, styles["CyrillicCode"]))

    doc.build(story)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python scripts/md_to_pdf.py input.md output.pdf")
        sys.exit(1)
    md_to_pdf(sys.argv[1], sys.argv[2])
