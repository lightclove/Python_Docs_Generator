#!/usr/bin/env python3
"""
Перевод документации Python с английского на русский.

Возможности:
- Атомарная запись (временный файл → rename) — при прерывании оригинал не повреждается
- Возобновление с прерванного места при повторном запуске
- Обработка KeyboardInterrupt (Ctrl+C)
- Очистка orphan .tmp после аварийного завершения
- Эвристика: пропуск уже переведённых (кириллица)
- Retry при сетевых ошибках
- Проверка свободного места на диске
- Таймаут запросов к переводчику (избежание зависания)

Запуск: python translate_python_docs.py

Файл состояния: .translate_state.json — список переведённых файлов
"""
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_DOCS_DIR = PROJECT_ROOT
MAX_CHUNK_LEN = 4500  # Лимит Google Translate
SLEEP_BETWEEN = 0.5  # Задержка между запросами (сек)
STATE_FILENAME = ".translate_state.json"
TRANSLATE_RETRIES = 3  # Повторы при сетевой ошибке
CYRILLIC_THRESHOLD = 0.35  # Доля кириллицы для "уже переведён"
REQUEST_TIMEOUT = 60  # Таймаут одного запроса к переводчику (сек)
MIN_FREE_MB = 100  # Минимум свободного места на диске (МБ)


def _check_disk_space(root: Path) -> None:
    """Проверить свободное место. Выход с ошибкой при нехватке."""
    check_path = root if root.exists() else Path.cwd()
    try:
        usage = shutil.disk_usage(check_path)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < MIN_FREE_MB:
            print(
                f"ОШИБКА: Недостаточно места на диске. Свободно: {free_mb:.0f} МБ, "
                f"требуется минимум: {MIN_FREE_MB} МБ"
            )
            sys.exit(1)
        if free_mb < MIN_FREE_MB * 2:
            print(f"ВНИМАНИЕ: Мало места на диске ({free_mb:.0f} МБ). Рекомендуется ≥ {MIN_FREE_MB * 2} МБ.\n")
    except OSError as e:
        print(f"ВНИМАНИЕ: Не удалось проверить место на диске: {e}\n")


def _path_to_key(path: Path) -> str:
    """Относительный путь для ключа в состоянии."""
    try:
        return str(path.relative_to(PYTHON_DOCS_DIR))
    except ValueError:
        return str(path)


def load_state(state_path: Path) -> set[str]:
    """Загрузить множество переведённых файлов."""
    if not state_path.exists():
        return set()
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        completed = data.get("completed", []) if isinstance(data, dict) else []
        return set(completed) if isinstance(completed, list) else set()
    except (json.JSONDecodeError, OSError, TypeError):
        return set()


def save_state(completed: set[str], state_path: Path) -> None:
    """Сохранить состояние перевода (атомарно)."""
    content = json.dumps({"completed": sorted(completed)}, ensure_ascii=False, indent=2)
    tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(state_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _cleanup_orphan_tmp_files(root: Path) -> int:
    """Удалить оставшиеся .tmp после аварийного завершения. Возвращает количество удалённых."""
    removed = 0
    for p in root.rglob("*.md.tmp"):
        try:
            p.unlink()
            removed += 1
        except OSError:
            pass
    state_tmp = root / (STATE_FILENAME + ".tmp")
    if state_tmp.exists():
        try:
            state_tmp.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def _cyrillic_ratio(text: str) -> float:
    """Доля символов кириллицы в тексте (игнорируя пробелы и код)."""
    chars = [c for c in text if c.isalpha()]
    if not chars:
        return 0.0
    cyrillic = sum(1 for c in chars if "\u0400" <= c <= "\u04FF")
    return cyrillic / len(chars)


def _is_likely_translated(content: str) -> bool:
    """Файл уже переведён (эвристика по доле кириллицы)."""
    # Берём только текстовые части, исключая код
    no_code = re.sub(r"```[\s\S]*?```", " ", content)
    no_code = re.sub(r"`[^`]+`", " ", no_code)
    return _cyrillic_ratio(no_code) >= CYRILLIC_THRESHOLD


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


def _translate_with_retry(translator, text: str) -> str:
    """Перевести с повторами при сетевых ошибках и таймауте."""
    last_err: Exception | None = None
    for attempt in range(TRANSLATE_RETRIES):
        ex = ThreadPoolExecutor(max_workers=1)
        try:
            future = ex.submit(translator.translate, text)
            out = future.result(timeout=REQUEST_TIMEOUT)
            return out if out is not None and isinstance(out, str) else text
        except FuturesTimeoutError:
            last_err = TimeoutError(f"Таймаут запроса ({REQUEST_TIMEOUT} сек)")
            if attempt < TRANSLATE_RETRIES - 1:
                time.sleep(SLEEP_BETWEEN * (attempt + 1))
        except Exception as e:
            last_err = e
            if attempt < TRANSLATE_RETRIES - 1:
                time.sleep(SLEEP_BETWEEN * (attempt + 1))
        finally:
            ex.shutdown(wait=False)  # Не ждать зависший поток
    print(f"  Ошибка перевода (после {TRANSLATE_RETRIES} попыток): {last_err}")
    return text


def translate_chunk(translator, text: str) -> str:
    """Перевести фрагмент с учётом лимита длины."""
    text = text.strip()
    if not text or len(text) < 10:
        return text

    if len(text) > MAX_CHUNK_LEN:
        parts = re.split(r"(\n\n+)", text)
        result = []
        buf = ""
        for p in parts:
            if len(buf) + len(p) > MAX_CHUNK_LEN and buf:
                result.append(_translate_with_retry(translator, buf))
                time.sleep(SLEEP_BETWEEN)
                buf = p
            else:
                buf += p
        if buf:
            result.append(_translate_with_retry(translator, buf))
            time.sleep(SLEEP_BETWEEN)
        return "".join(result)

    return _translate_with_retry(translator, text)


def translate_md_file(path: Path, translator) -> bool:
    """Перевести один MD файл. Код блоки не трогаем."""
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл удалён: {path}") from None
    except PermissionError:
        raise PermissionError(f"Нет доступа к чтению: {path}") from None
    except UnicodeDecodeError as e:
        raise ValueError(f"Некорректная кодировка {path}: {e}") from e
    except OSError as e:
        raise OSError(f"Ошибка чтения {path}: {e}") from e

    if not content.strip():
        return True  # Пустой файл — считаем обработанным

    if _is_likely_translated(content):
        return True  # Уже переведён (эвристика) — пропустить

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

    # Атомарная запись: сначала во временный файл, затем rename.
    # При прерывании во время записи оригинал не повреждается.
    content = "".join(result)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
    except OSError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise OSError(f"Ошибка записи {path}: {e}") from e
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    return True


def main() -> None:
    """Основная функция с возобновлением и обработкой прерывания."""
    print("Запуск перевода документации Python EN -> RU...")
    print(f"Каталог: {PYTHON_DOCS_DIR}\n")

    _check_disk_space(PYTHON_DOCS_DIR)

    # Очистка orphan .tmp после аварийного завершения
    orphan_count = _cleanup_orphan_tmp_files(PYTHON_DOCS_DIR)
    if orphan_count:
        print(f"Удалено временных файлов (.tmp): {orphan_count}\n")

    state_path = PYTHON_DOCS_DIR / STATE_FILENAME
    completed = load_state(state_path)
    if completed:
        print(f"Возобновление: пропуск {len(completed)} уже переведённых файлов.\n")

    translator = get_translator()
    md_files = sorted(PYTHON_DOCS_DIR.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]

    to_translate = [f for f in md_files if _path_to_key(f) not in completed]
    total = len(to_translate)

    for i, path in enumerate(to_translate, 1):
        rel = path.relative_to(PYTHON_DOCS_DIR)
        print(f"[{i}/{total}] {rel}")
        try:
            translate_md_file(path, translator)
            completed.add(_path_to_key(path))
            try:
                save_state(completed, state_path)
            except OSError as e:
                print(f"  ОШИБКА сохранения состояния: {e}")
            print("  OK")
        except KeyboardInterrupt:
            print("\nПрервано пользователем (Ctrl+C).")
            try:
                save_state(completed, state_path)
                print("Состояние сохранено.")
            except OSError as e:
                print(f"Ошибка сохранения состояния: {e}")
            print(f"Повторный запуск возобновит с {rel}")
            sys.exit(130)
        except (FileNotFoundError, PermissionError, OSError, ValueError) as e:
            print(f"  ОШИБКА: {e}")
        except Exception as e:
            print(f"  ОШИБКА: {type(e).__name__}: {e}")

    print("\nПеревод завершён.")


if __name__ == "__main__":
    main()
