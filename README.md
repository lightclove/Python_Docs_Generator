# Python_Docs_Generator
Автоматизированный перевод официальной документации Python с https://docs.python.org/3/, организованная по разделам сайта в md и pdf формате
# Документация Python на русском

Полная документация Python с [docs.python.org](https://docs.python.org/3/), организованная по разделам сайта.

**Самодостаточный проект** — можно скопировать папку в `C:\Users\idv\Work\Python_Docs_Generator` и использовать отдельно.

## Структура

```
Python_Docs_Generator/
├── README.md
├── requirements.txt
├── run_fetch.ps1         # Загрузка с docs.python.org
├── run_translation.ps1   # Перевод EN -> RU (в отдельном окне)
├── run_batch_pdf.ps1     # Конвертация MD -> PDF
├── scripts/
│   ├── fetch_python_docs.py   # Загрузка документации
│   ├── translate_python_docs.py  # Перевод на русский
│   ├── md_to_pdf.py            # Один MD -> PDF
│   └── batch_md_to_pdf.py     # Все MD -> PDF
├── 01_TUTORIAL/          # Учебник Python (The Python Tutorial)
│   ├── 00_index.md
│   ├── ...
│   └── 14_appendix.md
├── 02_LIBRARY/           # Стандартная библиотека
│   ├── 00_intro.md
│   ├── ...
│   └── 14_python.md
└── 03_LANGUAGE_REFERENCE/ # Справочник по языку
    ├── 00_intro.md
    ├── ...
    └── 08_toplevel.md
```
# Установка

```powershell
cd path_to_project
pip install -r requirements.txt
```
## Команды

| Действие | PowerShell | Python |
|----------|------------|--------|
| Загрузить MD с docs.python.org | `.\run_fetch.ps1` | `python scripts/fetch_python_docs.py` |
| Перевести EN -> RU (в отдельном окне) | `.\run_translation.ps1` | `python scripts/translate_python_docs.py` |
| Конвертировать все MD в PDF | `.\run_batch_pdf.ps1` | `python scripts/batch_md_to_pdf.py` |
| Один файл MD -> PDF | — | `python scripts/md_to_pdf.py input.md output.pdf` |

## Разделы

### 01_TUTORIAL — Учебник
- Использование интерпретатора
- Неформальное введение
- Управление потоком, структуры данных
- Модули, ввод-вывод, исключения
- Классы, стандартная библиотека
- Виртуальные окружения

### 02_LIBRARY — Стандартная библиотека
- Встроенные функции и типы
- Обработка текста, типы данных
- Файлы, сохранение данных
- Параллельное выполнение, сеть
- Инструменты разработки

### 03_LANGUAGE_REFERENCE — Справочник по языку
- Лексический анализ
- Модель данных и выполнения
- Система импорта
- Выражения и операторы

## Источник

Все материалы с [https://docs.python.org/3/](https://docs.python.org/3/)

© Python Software Foundation. Лицензия: PSF License Version 2, Zero Clause BSD для примеров.
