# Документация Python на русском

Полная документация Python с [docs.python.org](https://docs.python.org/3/), организованная по разделам сайта.

## Возможности

### Загрузка (`fetch_python_docs.py`)
- Загрузка **всех** разделов документации (парсинг contents.html)
- Детальное логгирование в файл и консоль
- **Возобновление** с прерванного места при повторном запуске
- Сохранение причины разрыва и места остановки

### Перевод (`translate_python_docs.py`)
- **Атомарная запись** (временный файл → rename) — при прерывании оригинал не повреждается
- Возобновление с прерванного места
- Обработка Ctrl+C (KeyboardInterrupt)
- Эвристика: пропуск уже переведённых (доля кириллицы)
- Retry при сетевых ошибках, таймаут запросов
- Проверка свободного места на диске

### Конвертация MD → PDF
- Поддержка **Unicode** (русский язык) через reportlab
- Один файл: `md_to_pdf.py input.md output.pdf`
- Пакетная: `batch_md_to_pdf.py` — все MD в PDF

### Проверка (`verify_python_docs_inconsistencies.py`)
- Формат и консистентность `.fetch_state.json`
- Маппинг URL → путь (отсутствие коллизий)
- Интеграция fetch/translate/batch (одинаковые наборы MD)
- Полнота перевода (файлы с низкой долей кириллицы)

## Структура

```
00_PYTHON/  (или Python_Docs_Generator/)
├── README.md
├── requirements.txt
├── run.ps1                    # Полный цикл: загрузка + перевод + PDF
├── fetch_python_docs.py       # Загрузка документации
├── translate_python_docs.py   # Перевод на русский
├── md_to_pdf.py               # Один MD -> PDF
├── batch_md_to_pdf.py         # Все MD -> PDF
├── .fetch_state.json     # Состояние загрузки (возобновление)
├── .translate_state.json # Состояние перевода
├── fetch_python_docs.log # Лог загрузки
├── tests/                # Unit и интеграционные тесты
├── 01_TUTORIAL/          # Учебник
├── 02_LIBRARY/           # Стандартная библиотека
├── 03_LANGUAGE_REFERENCE/# Справочник по языку
├── 04_WHATSNEW/          # Что нового
├── 05_USING/             # Установка и использование
├── 06_HOWTO/             # Руководства HOWTO
├── 07_INSTALLING/        # Установка модулей
├── 08_DISTRIBUTING/      # Распространение модулей
├── 09_EXTENDING/         # Расширение и встраивание
├── 10_CAPI/              # C API
├── 11_FAQ/               # Частые вопросы
└── ...
```

## Установка

```powershell
cd C:\Users\idv\Work\Python_Docs_Generator   # или docs\00_PYTHON
pip install -r requirements.txt
```

## Команды

| Действие | Команда |
|----------|---------|
| **Полный цикл** (загрузка + перевод + PDF) | `.\run.ps1` |
| Один файл MD -> PDF | `python md_to_pdf.py input.md output.pdf` |
| Сбросить состояние загрузки | Удалить `.fetch_state.json` |
| Сбросить состояние перевода | Удалить `.translate_state.json` |



## Источник

Все материалы с [https://docs.python.org/3/](https://docs.python.org/3/)

© Python Software Foundation. Лицензия: PSF License Version 2, Zero Clause BSD для примеров.



