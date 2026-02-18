#!/usr/bin/env python3
"""
Пакетная конвертация всех MD файлов в PDF.
Запуск: python batch_md_to_pdf.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_DOCS_DIR = PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT))
from md_to_pdf import md_to_pdf


def main() -> None:
    """Конвертировать все MD в PDF."""
    md_files = list(PYTHON_DOCS_DIR.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]

    failed = 0
    for md_path in sorted(md_files):
        pdf_path = md_path.with_suffix(".pdf")
        try:
            md_to_pdf(md_path, pdf_path)
            print(f"OK: {pdf_path.relative_to(PYTHON_DOCS_DIR)}")
        except Exception as e:
            print(f"Ошибка {md_path.name}: {e}")
            failed += 1

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
