#!/usr/bin/env python3
"""
Перевод документации Python с английского на русский.
Запуск из корня проекта: python scripts/translate_python_docs.py
Или в отдельном окне: .\run_translation.ps1
"""
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_DOCS_DIR = PROJECT_ROOT
MAX_CHUNK_LEN = 4500  # Лимит Google Translate
SLEEP_BETWEEN = 0.5  # Задержка между запросами (сек)


def get_translator():
    """Получить переводчик."""
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="en", target="ru")
    except ImportError:
        print("Установите: pip install deep-translator")
        sys.exit(1)


def split_preserving_blocks(content: str) -> list[tuple[str, str]]:
    """
    Разбить MD на блоки: ('text', chunk) или ('code', chunk).
    code блоки не переводим.
    """
    blocks = []
    pattern = r"(```[\s\S]*?```|`[^`]+`|\[.*?\]\(.*?\)|https?://[^\s\)]+)"
    parts = re.split(pattern, content)

    for part in parts:
        if not part.strip():
            continue
        if part.startswith("```") or (part.startswith("`") and part.endswith("`")):
            blocks.append(("code", part))
        elif part.startswith("http") or "](http" in part:
            blocks.append(("skip", part))
        else:
            # Разбить длинный текст на части по предложениям/абзацам
            for chunk in re.split(r"(\n\n+)", part):
                if chunk.strip():
                    blocks.append(("text", chunk))
    return blocks


def translate_chunk(translator, text: str) -> str:
    """Перевести фрагмент с учётом лимита длины."""
    text = text.strip()
    if not text or len(text) < 10:
        return text

    if len(text) > MAX_CHUNK_LEN:
        # Разбить по абзацам
        parts = re.split(r"(\n\n+)", text)
        result = []
        buf = ""
        for p in parts:
            if len(buf) + len(p) > MAX_CHUNK_LEN and buf:
                result.append(translator.translate(buf))
                time.sleep(SLEEP_BETWEEN)
                buf = p
            else:
                buf += p
        if buf:
            result.append(translator.translate(buf))
            time.sleep(SLEEP_BETWEEN)
        return "".join(result)

    try:
        return translator.translate(text)
    except Exception as e:
        print(f"  Ошибка перевода: {e}")
        return text


def translate_md_file(path: Path, translator) -> bool:
    """Перевести один MD файл. Код блоки не трогаем."""
    content = path.read_text(encoding="utf-8")

    # Заменить код-блоки на плейсхолдеры
    code_blocks = []

    def save_code(m):
        code_blocks.append(m.group(0))
        return f"\n\n__CODE_BLOCK_{len(code_blocks)-1}__\n\n"

    temp = re.sub(r"```[\s\S]*?```", save_code, content)

    # Перевести по абзацам (двойной перенос)
    paragraphs = re.split(r"(\n\n+)", temp)
    result = []
    for p in paragraphs:
        if p.startswith("__CODE_BLOCK_"):
            idx = int(re.search(r"(\d+)", p).group(1))
            result.append(code_blocks[idx])
        elif p.strip() and not p.isspace():
            # Проверить: не ссылка, не URL
            if re.match(r"^\[.*\]\(http", p) or p.startswith("http"):
                result.append(p)
            else:
                if len(p.strip()) > 15:
                    try:
                        result.append(translate_chunk(translator, p))
                        time.sleep(SLEEP_BETWEEN)
                    except Exception:
                        result.append(p)
                else:
                    result.append(p)
        else:
            result.append(p)

    path.write_text("".join(result), encoding="utf-8")
    return True


def main() -> None:
    """Основная функция."""
    print("Запуск перевода документации Python EN -> RU...")
    print(f"Каталог: {PYTHON_DOCS_DIR}\n")

    translator = get_translator()
    md_files = sorted(PYTHON_DOCS_DIR.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md" and "scripts" not in str(f)]

    total = len(md_files)
    for i, path in enumerate(md_files, 1):
        rel = path.relative_to(PYTHON_DOCS_DIR)
        print(f"[{i}/{total}] {rel}")
        try:
            translate_md_file(path, translator)
            print("  OK")
        except Exception as e:
            print(f"  ОШИБКА: {e}")

    print("\nПеревод завершён.")


if __name__ == "__main__":
    main()
