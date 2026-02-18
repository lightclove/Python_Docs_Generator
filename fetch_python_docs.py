#!/usr/bin/env python3
"""
Загрузка документации Python с docs.python.org и сохранение в Markdown.

Возможности:
- Загрузка ВСЕХ разделов документации (парсинг contents.html)
- Детальное логгирование в файл и консоль
- Возобновление с прерванного места при повторном запуске
- Сохранение причины разрыва и места остановки

Запуск: python fetch_python_docs.py

Файлы состояния и логов:
- .fetch_state.json — прогресс загрузки (для возобновления)
- fetch_python_docs.log — детальный лог
"""
import json
import logging
import re
import sys
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

BASE_URL = "https://docs.python.org/3"
CONTENTS_URL = f"{BASE_URL}/contents.html"
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT
STATE_FILENAME = ".fetch_state.json"
LOG_FILENAME = "fetch_python_docs.log"

# Маппинг разделов docs.python.org -> локальные папки
SECTION_TO_DIR: dict[str, str] = {
    "whatsnew": "04_WHATSNEW",
    "tutorial": "01_TUTORIAL",
    "library": "02_LIBRARY",
    "reference": "03_LANGUAGE_REFERENCE",
    "using": "05_USING",
    "howto": "06_HOWTO",
    "installing": "07_INSTALLING",
    "distributing": "08_DISTRIBUTING",
    "extending": "09_EXTENDING",
    "c-api": "10_CAPI",
    "faq": "11_FAQ",
    "license": "12_MISC",
    "copyright": "12_MISC",
}


@dataclass
class FetchState:
    """Состояние загрузки для возобновления."""

    completed_urls: list[str] = field(default_factory=list)
    failed_urls: dict[str, str] = field(default_factory=dict)
    last_url: str | None = None
    error_info: dict[str, str] | None = None
    total_planned: int = 0

    def should_skip(self, url_path: str) -> bool:
        """Пропустить URL если уже загружен."""
        return url_path in self.completed_urls

    def mark_completed(self, url_path: str) -> None:
        """Отметить URL как загруженный."""
        if url_path not in self.completed_urls:
            self.completed_urls.append(url_path)
        self.last_url = url_path
        if url_path in self.failed_urls:
            del self.failed_urls[url_path]
        self.error_info = None

    def mark_failed(self, url_path: str, error: str, tb: str = "") -> None:
        """Отметить URL как ошибочный."""
        self.failed_urls[url_path] = error
        self.error_info = {
            "url": url_path,
            "error": error,
            "traceback": tb,
        }


def _setup_logging(log_dir: Path) -> logging.Logger:
    """Настроить детальное логгирование."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILENAME

    logger = logging.getLogger("fetch_python_docs")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


def _safe_int(val: object, default: int) -> int:
    """Безопасное преобразование в int."""
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def load_state(state_path: Path) -> FetchState:
    """Загрузить состояние из файла."""
    if not state_path.exists():
        return FetchState()
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        completed = data.get("completed_urls", [])
        failed = data.get("failed_urls", {})
        if not isinstance(completed, list):
            completed = []
        if not isinstance(failed, dict):
            failed = {}
        return FetchState(
            completed_urls=completed,
            failed_urls=failed,
            last_url=data.get("last_url"),
            error_info=data.get("error_info"),
            total_planned=_safe_int(data.get("total_planned"), 0),
        )
    except (json.JSONDecodeError, OSError, TypeError):
        return FetchState()


def save_state(state: FetchState, state_path: Path) -> None:
    """Сохранить состояние в файл (атомарно)."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(state)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    tmp_path = state_path.with_suffix(state_path.suffix + ".tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(state_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _url_to_output_path(url_path: str, output_dir: Path) -> Path:
    """Преобразовать URL-путь в локальный путь к MD файлу."""
    parts = url_path.replace(".html", "").split("/")
    if len(parts) < 2:
        name = parts[0] if parts else "index"
        section = name
    else:
        section = parts[0]
        name = "_".join(parts[1:]) if len(parts) > 1 else "index"

    dir_name = SECTION_TO_DIR.get(section, "99_OTHER")
    out_dir = output_dir / dir_name
    return out_dir / f"{name}.md"


def _extract_doc_urls_from_contents(html: str, base_url: str) -> list[str]:
    """Извлечь все ссылки на документацию из contents.html."""
    if BeautifulSoup is None:
        raise ImportError("Установите beautifulsoup4: pip install beautifulsoup4")
    soup = BeautifulSoup(html, "html.parser")
    urls: set[str] = set()
    prefix = f"{base_url}/"

    for a in soup.find_all("a", href=True):
        href = a["href"].split("#")[0].strip()
        if not href.endswith(".html") or "genindex" in href or "py-modindex" in href:
            continue
        if href.startswith(prefix):
            path = href[len(prefix) :].lstrip("/")
            urls.add(path)
        elif href.startswith("/3/"):
            path = href[3:].lstrip("/")
            urls.add(path)
        elif "/" in href or href.startswith(
            ("tutorial", "library", "reference", "whatsnew", "using", "howto",
             "installing", "distributing", "extending", "faq", "c-api", "license", "copyright")
        ):
            urls.add(href)
        elif href.endswith(".html"):
            urls.add(href)

    return sorted(urls)


def fetch_page(url: str, timeout: int = 30) -> str:
    """Загрузить страницу и вернуть HTML."""
    full_url = url if url.startswith("http") else f"{BASE_URL}/{url}"
    with urlopen(full_url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def html_to_markdown(html: str, base_url: str = BASE_URL) -> str:
    """Конвертировать HTML в Markdown."""
    if BeautifulSoup is None:
        raise ImportError("Установите beautifulsoup4: pip install beautifulsoup4")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["nav", "footer", "script", "style"]):
        tag.decompose()

    main = soup.find("main") or soup.find("div", class_=re.compile("body|content"))
    if not main:
        main = soup.find("body") or soup

    lines = []
    for elem in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "pre", "ul", "ol", "dl", "table"]):
        if elem.name and elem.name.startswith("h"):
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
        elif elem.name == "table":
            for tr in elem.find_all("tr"):
                cells = [
                    th.get_text(strip=True).replace("|", "\\|")
                    for th in tr.find_all(["th", "td"])
                ]
                if cells:
                    lines.append("| " + " | ".join(cells) + " |\n")
            lines.append("\n")

    return "\n".join(lines).strip()


def fetch_and_save_one(
    url_path: str,
    output_path: Path,
    logger: logging.Logger,
) -> None:
    """Загрузить одну страницу и сохранить в MD (атомарно)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = fetch_page(url_path)
    md = html_to_markdown(html)
    source_note = f"*Источник: https://docs.python.org/3/{url_path}*"
    md = f"# {output_path.stem}\n\n{source_note}\n\n---\n\n{md}"
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        tmp_path.write_text(md, encoding="utf-8")
        tmp_path.replace(output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
    logger.info("Сохранено: %s -> %s", url_path, output_path.relative_to(OUTPUT_DIR))


def _cleanup_orphan_tmp_files(root: Path) -> int:
    """Удалить оставшиеся .tmp после аварийного завершения."""
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


def main() -> None:
    """Основная функция с возобновлением и логгированием."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state_path = OUTPUT_DIR / STATE_FILENAME
    logger = _setup_logging(OUTPUT_DIR)

    orphan_count = _cleanup_orphan_tmp_files(OUTPUT_DIR)
    if orphan_count:
        logger.info("Удалено временных файлов (.tmp): %d", orphan_count)

    logger.info("=== Запуск загрузки документации Python ===")
    logger.info("Каталог вывода: %s", OUTPUT_DIR)
    logger.info("Файл состояния: %s", state_path)

    state = load_state(state_path)
    if state.error_info:
        logger.warning(
            "Предыдущий запуск прерван. URL: %s, Ошибка: %s",
            state.error_info.get("url"),
            state.error_info.get("error"),
        )
        logger.debug("Трейсбек: %s", state.error_info.get("traceback", "")[:500])

    try:
        logger.info("Загрузка оглавления: %s", CONTENTS_URL)
        contents_html = fetch_page(CONTENTS_URL)
        all_urls = _extract_doc_urls_from_contents(contents_html, BASE_URL)
        logger.info("Найдено страниц для загрузки: %d", len(all_urls))
    except (HTTPError, URLError, OSError) as e:
        logger.exception("Ошибка загрузки contents.html: %s", e)
        state.mark_failed("contents.html", str(e), traceback.format_exc())
        save_state(state, state_path)
        sys.exit(1)

    to_fetch: list[str] = []
    synced = 0
    for u in state.failed_urls:
        if u in all_urls:
            to_fetch.append(u)
    for u in all_urls:
        if u in to_fetch:
            continue
        if state.should_skip(u):
            continue
        output_path = _url_to_output_path(u, OUTPUT_DIR)
        if output_path.exists():
            state.mark_completed(u)
            synced += 1
            continue
        to_fetch.append(u)
    if synced:
        save_state(state, state_path)
        logger.info("Синхронизировано с диском (файлы уже есть): %d", synced)

    total = len(to_fetch)
    state.total_planned = len(all_urls)
    logger.info("К пропуску (уже загружено): %d", len(state.completed_urls))
    logger.info("К загрузке: %d", total)

    for i, url_path in enumerate(to_fetch, 1):
        try:
            output_path = _url_to_output_path(url_path, OUTPUT_DIR)
            logger.debug("[%d/%d] Загрузка %s", i, total, url_path)
            fetch_and_save_one(url_path, output_path, logger)
            state.mark_completed(url_path)
            save_state(state, state_path)
        except KeyboardInterrupt:
            logger.warning("Прервано пользователем (Ctrl+C). Текущий URL: %s.", url_path)
            save_state(state, state_path)
            logger.info("Состояние сохранено. Повторный запуск возобновит с %s", url_path)
            sys.exit(130)
        except (HTTPError, URLError, OSError) as e:
            err_msg = f"{type(e).__name__}: {e}"
            logger.error("Ошибка [%d/%d] %s: %s", i, total, url_path, err_msg)
            logger.debug("Трейсбек: %s", traceback.format_exc())
            state.mark_failed(url_path, err_msg, traceback.format_exc())
            save_state(state, state_path)
            logger.warning(
                "Скачивание прервано. URL: %s. Причина: %s. Повторный запуск возобновит с этого места.",
                url_path,
                err_msg,
            )
        except Exception as e:
            err_msg = f"{type(e).__name__}: {e}"
            tb = traceback.format_exc()
            logger.exception("Неожиданная ошибка [%d/%d] %s: %s", i, total, url_path, err_msg)
            state.mark_failed(url_path, err_msg, tb)
            save_state(state, state_path)
            logger.warning(
                "Скачивание прервано. URL: %s. Причина: %s. Файл состояния: %s",
                url_path,
                err_msg,
                state_path,
            )
            raise

    logger.info("=== Загрузка завершена ===")
    logger.info("Успешно: %d, Ошибок: %d", len(state.completed_urls), len(state.failed_urls))
    if state.failed_urls:
        logger.warning("Не загружены: %s", list(state.failed_urls.keys())[:10])


if __name__ == "__main__":
    main()
