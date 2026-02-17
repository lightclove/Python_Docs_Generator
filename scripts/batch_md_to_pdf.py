#!/usr/bin/env python3
"""
Пакетная конвертация всех MD файлов в PDF.
Запуск из корня проекта: python scripts/batch_md_to_pdf.py
"""
import sys
from pathlib import Path

# Добавить папку scripts в path для импорта md_to_pdf
_scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_scripts_dir))

from md_to_pdf import md_to_pdf

PROJECT_ROOT = _scripts_dir.parent
PYTHON_DOCS_DIR = PROJECT_ROOT


def main() -> None:
    """Конвертировать все MD в PDF."""
    md_files = list(PYTHON_DOCS_DIR.rglob("*.md"))
    # Исключаем README и файлы в scripts
    md_files = [
        f
        for f in md_files
        if f.name != "README.md" and "scripts" not in str(f)
    ]

    for md_path in sorted(md_files):
        pdf_path = md_path.with_suffix(".pdf")
        try:
            md_to_pdf(md_path, pdf_path)
            print(f"OK: {pdf_path.relative_to(PYTHON_DOCS_DIR)}")
        except Exception as e:
            print(f"Ошибка {md_path.name}: {e}")


if __name__ == "__main__":
    main()
