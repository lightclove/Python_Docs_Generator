#!/usr/bin/env python3
"""
Загрузка документации Python с docs.python.org и сохранение в Markdown.
Запуск из корня проекта: python scripts/fetch_python_docs.py
"""
import re
from pathlib import Path

from urllib.request import urlopen

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

BASE_URL = "https://docs.python.org/3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT

# Словарь переводов ключевых терминов
TRANSLATIONS = {
    "Introduction": "Введение",
    "Tutorial": "Учебник",
    "Library": "Стандартная библиотека",
    "Reference": "Справочник",
    "Note": "Примечание",
    "Warning": "Внимание",
    "Tip": "Совет",
    "See also": "См. также",
    "For example": "Например",
    "The": "Этот/Эта/Это",
    "This": "Этот/Эта",
    "module": "модуль",
    "function": "функция",
    "class": "класс",
    "method": "метод",
    "argument": "аргумент",
    "parameter": "параметр",
    "return": "возвращать",
    "returns": "возвращает",
    "raise": "вызывать",
    "raises": "вызывает",
    "exception": "исключение",
    "error": "ошибка",
}


def fetch_page(url: str) -> str:
    """Загрузить страницу и вернуть HTML."""
    full_url = url if url.startswith("http") else f"{BASE_URL}/{url}"
    with urlopen(full_url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_markdown(html: str, base_url: str = BASE_URL) -> str:
    """Конвертировать HTML в Markdown."""
    if BeautifulSoup is None:
        raise ImportError("Установите beautifulsoup4: pip install beautifulsoup4")
    soup = BeautifulSoup(html, "html.parser")

    # Удалить навигацию, футер
    for tag in soup.find_all(["nav", "footer", "script", "style"]):
        tag.decompose()

    # Найти основной контент
    main = soup.find("main") or soup.find("div", class_=re.compile("body|content"))
    if not main:
        main = soup.find("body") or soup

    lines = []
    for elem in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "dl", "table"]):
        if elem.name.startswith("h"):
            level = int(elem.name[1])
            text = elem.get_text(strip=True)
            lines.append(f"\n{'#' * level} {text}\n")
        elif elem.name == "p":
            text = elem.get_text(separator=" ", strip=True)
            if text:
                lines.append(f"{text}\n\n")
        elif elem.name == "pre":
            code = elem.get_text()
            lang = "python" if ">>>" in code or "def " in code else ""
            lines.append(f"\n```{lang}\n{code}\n```\n\n")
        elif elem.name in ("ul", "ol"):
            for li in elem.find_all("li", recursive=False):
                text = li.get_text(separator=" ", strip=True)
                prefix = "- " if elem.name == "ul" else "1. "
                lines.append(f"{prefix}{text}\n")
            lines.append("\n")
        elif elem.name == "dl":
            for dt in elem.find_all("dt"):
                term = dt.get_text(strip=True)
                dd = dt.find_next_sibling("dd")
                defn = dd.get_text(separator=" ", strip=True) if dd else ""
                lines.append(f"- **{term}**: {defn}\n")
            lines.append("\n")

    return "\n".join(lines).strip()


def fetch_and_save(
    url_path: str,
    output_path: Path,
    title_ru: str | None = None,
) -> None:
    """Загрузить страницу и сохранить в MD."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = fetch_page(url_path)
    md = html_to_markdown(html)

    if title_ru:
        md = f"# {title_ru}\n\n*Источник: https://docs.python.org/3/{url_path}*\n\n---\n\n{md}"

    output_path.write_text(md, encoding="utf-8")
    print(f"Сохранено: {output_path}")


def main() -> None:
    """Основная функция."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Tutorial
    tutorial_pages = [
        ("tutorial/index.html", "01_TUTORIAL/00_index.md", "Учебник Python — Оглавление"),
        ("tutorial/interpreter.html", "01_TUTORIAL/01_interpreter.md", "Использование интерпретатора"),
        ("tutorial/introduction.html", "01_TUTORIAL/02_introduction.md", "Неформальное введение в Python"),
        ("tutorial/controlflow.html", "01_TUTORIAL/03_controlflow.md", "Инструменты управления потоком"),
        ("tutorial/datastructures.html", "01_TUTORIAL/04_datastructures.md", "Структуры данных"),
        ("tutorial/modules.html", "01_TUTORIAL/05_modules.md", "Модули"),
        ("tutorial/inputoutput.html", "01_TUTORIAL/06_inputoutput.md", "Ввод и вывод"),
        ("tutorial/errors.html", "01_TUTORIAL/07_errors.md", "Ошибки и исключения"),
        ("tutorial/classes.html", "01_TUTORIAL/08_classes.md", "Классы"),
        ("tutorial/stdlib.html", "01_TUTORIAL/09_stdlib.md", "Краткий обзор стандартной библиотеки"),
        ("tutorial/stdlib2.html", "01_TUTORIAL/10_stdlib2.md", "Обзор стандартной библиотеки — Часть II"),
        ("tutorial/venv.html", "01_TUTORIAL/11_venv.md", "Виртуальные окружения и пакеты"),
        ("tutorial/interactive.html", "01_TUTORIAL/12_interactive.md", "Интерактивный ввод"),
        ("tutorial/floatingpoint.html", "01_TUTORIAL/13_floatingpoint.md", "Арифметика с плавающей точкой"),
        ("tutorial/appendix.html", "01_TUTORIAL/14_appendix.md", "Приложение"),
    ]

    for url_path, rel_path, title in tutorial_pages:
        try:
            fetch_and_save(url_path, OUTPUT_DIR / rel_path, title)
        except Exception as e:
            print(f"Ошибка {url_path}: {e}")

    # Library - intro and key sections
    library_pages = [
        ("library/intro.html", "02_LIBRARY/00_intro.md", "Стандартная библиотека — Введение"),
        ("library/functions.html", "02_LIBRARY/01_functions.md", "Встроенные функции"),
        ("library/stdtypes.html", "02_LIBRARY/02_stdtypes.md", "Встроенные типы"),
        ("library/exceptions.html", "02_LIBRARY/03_exceptions.md", "Встроенные исключения"),
        ("library/text.html", "02_LIBRARY/04_text.md", "Обработка текста"),
        ("library/datatypes.html", "02_LIBRARY/05_datatypes.md", "Типы данных"),
        ("library/numeric.html", "02_LIBRARY/06_numeric.md", "Числа и математика"),
        ("library/filesys.html", "02_LIBRARY/07_filesys.md", "Файлы и каталоги"),
        ("library/persistence.html", "02_LIBRARY/08_persistence.md", "Сохранение данных"),
        ("library/concurrency.html", "02_LIBRARY/09_concurrency.md", "Параллельное выполнение"),
        ("library/ipc.html", "02_LIBRARY/10_ipc.md", "Сеть и IPC"),
        ("library/netdata.html", "02_LIBRARY/11_netdata.md", "Обработка данных интернета"),
        ("library/development.html", "02_LIBRARY/12_development.md", "Инструменты разработки"),
        ("library/debug.html", "02_LIBRARY/13_debug.md", "Отладка и профилирование"),
        ("library/python.html", "02_LIBRARY/14_python.md", "Службы времени выполнения"),
    ]
    for url_path, rel_path, title in library_pages:
        try:
            fetch_and_save(url_path, OUTPUT_DIR / rel_path, title)
        except Exception as e:
            print(f"Ошибка {url_path}: {e}")

    # Language Reference
    ref_pages = [
        ("reference/introduction.html", "03_LANGUAGE_REFERENCE/00_intro.md", "Справочник по языку — Введение"),
        ("reference/lexical_analysis.html", "03_LANGUAGE_REFERENCE/01_lexical.md", "Лексический анализ"),
        ("reference/datamodel.html", "03_LANGUAGE_REFERENCE/02_datamodel.md", "Модель данных"),
        ("reference/executionmodel.html", "03_LANGUAGE_REFERENCE/03_execution.md", "Модель выполнения"),
        ("reference/import.html", "03_LANGUAGE_REFERENCE/04_import.md", "Система импорта"),
        ("reference/expressions.html", "03_LANGUAGE_REFERENCE/05_expressions.md", "Выражения"),
        ("reference/simple_stmts.html", "03_LANGUAGE_REFERENCE/06_simple_stmts.md", "Простые операторы"),
        ("reference/compound_stmts.html", "03_LANGUAGE_REFERENCE/07_compound_stmts.md", "Составные операторы"),
    ]

    for url_path, rel_path, title in ref_pages:
        try:
            fetch_and_save(url_path, OUTPUT_DIR / rel_path, title)
        except Exception as e:
            print(f"Ошибка {url_path}: {e}")

    try:
        fetch_and_save(
            "reference/toplevel_components.html",
            OUTPUT_DIR / "03_LANGUAGE_REFERENCE/08_toplevel.md",
            "Верхнеуровневые компоненты",
        )
    except Exception as e:
        print(f"Ошибка toplevel: {e}")

    print("\nГотово!")


if __name__ == "__main__":
    main()
