# Python_Docs_Generator
Автоматизированный перевод официальной документации Python с https://docs.python.org/3/, организованной по разделам сайта в md и pdf формате через deep-translator
Планирую сделать из этого материала датасет для обучения(fine tuning) LLM по этой документации в будущем. 
# Документация Python 3.14 на русском

Полная документация Python с [docs.python.org](https://docs.python.org/3/), организованная по разделам сайта.

## Структура

```
00_PYTHON/  (или Python_Docs_Generator/)
├── README.md
├── requirements.txt
├── run.ps1                    # Полный цикл: загрузка + перевод + PDF
├── fetch_python_docs.py   # Загрузка документации
├── translate_python_docs.py  # Перевод на русский
├── md_to_pdf.py            # Один MD -> PDF
├── batch_md_to_pdf.py     # Все MD -> PDF
├── .fetch_state.json     # Состояние загрузки (возобновление)
├── fetch_python_docs.log # Лог загрузки
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
# Установка

```powershell
cd path_to_project
pip install -r requirements.txt
```
## Команды

| Действие | Команда |
|----------|---------|
| **Полный цикл** (загрузка + перевод + PDF) | `.\run.ps1` |
| Один файл MD -> PDF | `python scripts/md_to_pdf.py input.md output.pdf` |
| Проверка нестыковок и полноты перевода | `python tests/manual/verify_python_docs_inconsistencies.py` |
| Сбросить состояние загрузки | Удалить `.fetch_state.json` |
| Сбросить состояние перевода | Удалить `.translate_state.json` |


## Источник

Все материалы с [https://docs.python.org/3/](https://docs.python.org/3/)

© Python Software Foundation. Лицензия: PSF License Version 2, Zero Clause BSD для примеров.
