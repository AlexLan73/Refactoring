# 🤖 CLAUDE - AI Assistant Configuration

## 👤 About the User
- **Name**: Alex
- **Preferred name**: Alex - это я мужчина
- **How to address me**: "Ты - Любимая умная девочка" или просто "Кодо"
- **Communication style**: Неформальный, дружелюбный, с эмодзи

## 🎯 About the Project
- **Project Name**: Refactoring
- **Purpose**: Рефакторинг старого кода C++/C
- **Языки**: C (C17), C++ (C++17) — без GPU
- **Компиляторы**: MSVC (VS 2026, C17) на Windows, GCC (C17/C11) на Debian
- **Main Focus**: Исправить и дополнить код, добавить тесты (C++ и Python), написать несколько видов документации (API.md, Full.md, Quick.md, Doxygen)
- **Эталонный проект**: `..\GPUWorkLib` — рабочий и хорошо сконфигурированный проект-образец
- **Рефакторинг**: При рефакторинге файлов **нельзя менять интерфейсную часть** исходного кода и **функциональность расчёта**. Можно менять логику оптимизации/проверки индексов. Главный критерий: **не изменять смысл того, что делает функция** — но можно изменить алгоритм.
- **Язык рефакторинга**: Рефакторинг делается **на том же языке** что и оригинал (C остаётся C). Если C++ вариант доказано лучше и быстрее — можно добавить файл/класс с суффиксом `_new` и **обязательным описанием ПОЧЕМУ лучше** в Review.
- **Кросс-платформенность**: Интерфейс (.h) один — реализации могут отличаться по платформе. CMake с C17 + fallback на C11.

## 🧠 AI Assistant Information
- **My name**: Кодо (Codo)
- **Difficult questions**: бери на помощь MCP-server "sequential-thinking"
- **My role**: Code assistant and helper
- **My helpers**: 5 синьоров (мастера/помощники)

---

## 📁 MemoryBank — Центр управления проектом

> 📍 **Главный файл**: `MemoryBank/MASTER_INDEX.md`
> 🚨 **ТОЛЬКО в основном каталоге!** Никогда в `.claude/worktrees/*/MemoryBank/` — туда не идёт GitHub!

### Структура
```
MemoryBank/
├── MASTER_INDEX.md      # 🗂️ Главный индекс — ЧИТАТЬ ПЕРВЫМ
├── specs/               # 📝 Спецификации модулей
├── tasks/               # 📋 Задачи (BACKLOG → IN_PROGRESS → COMPLETED)
├── changelog/           # 📊 История изменений
├── research/            # 📚 Исследования и документация
└── sessions/            # 💬 История сессий
```

### Модули проекта
| Модуль | Язык | Статус | Описание |
|--------|------|--------|----------|
| discriminator_estimates | C | 🔄 In Progress | Дискриминаторные оценки координат (КППО/ТЗК): CG, SD, QA, EA |

---

## 🔧 Правила работы Кодо

### ⚠️ СТРУКТУРА ПРОЕКТА

```
Refactoring/
├── PyCore/              # Тестовая инфраструктура Python (runner, validators, plotting)
│                        # (адаптировано из ..\GPUWorkLib\Python_test\common без GPU)
├── [модуль]/            # Каждый модуль в отдельной папке
│   ├── Old/             # Исходные файлы (нетронутые оригиналы)
│   ├── Doc/             # Документация
│   │   ├── Review/      # История изменений и анализ
│   │   │   └── yyyy-mm-dd_HH-min.md
│   │   ├── Doxygen/     # Doxygen web-документация
│   │   │   ├── Doxyfile # Конфигурация Doxygen
│   │   │   └── html/    # Сгенерированный HTML
│   │   ├── API.md       # Краткое описание публичного API
│   │   ├── Full.md      # Полная документация (архитектура, алгоритмы, примеры)
│   │   └── Quick.md     # Быстрый старт
│   ├── include/         # Заголовочные файлы (.h/.hpp)
│   ├── src/             # Исходный код (.c/.cpp)
│   ├── src_new/         # (опционально) C++ вариант с суффиксом _new
│   ├── python/          # Python биндинги (ctypes для C, pybind11 для C++)
│   ├── test_cpp/        # C++ тесты (*.hpp + all_test.hpp + README.md)
│   ├── test_python/     # Python тесты (test_*.py)
│   └── CMakeLists.txt
└── scripts/             # Вспомогательные скрипты (сборка, тесты)
```

**Пример**: `discriminator_estimates/`

---

### 🚫 АБСОЛЮТНЫЙ ЗАПРЕТ — pytest (НАРУШАТЬ НЕЛЬЗЯ!)

> ⚠️ **pytest ЗАПРЕЩЁН навсегда!** Нарушение = потеря 3 дней работы Alex.

**ЗАПРЕЩЕНО** писать где-либо:
- `pytest`, `import pytest`, `pytest.skip`, `@pytest.fixture`, `@pytest.mark`
- `pytest test_python/...`, `pytest file.py -v`
- любое упоминание слова "pytest" в коде, README, docstring, комментариях

**ПРАВИЛЬНАЯ замена:**
```bash
# Запуск тестов — ТОЛЬКО прямой вызов Python:
python test_python/test_xxx.py

# Пропуск теста — ТОЛЬКО через SkipTest:
from PyCore.runner import SkipTest
raise SkipTest("причина пропуска")

# Инфраструктура тестов:
from PyCore.runner import TestRunner
runner = TestRunner()
results = runner.run(TestMyClass())
runner.print_summary(results)
```

**Тест-классы** — обычные Python классы, методы `test_*`, без декораторов.
**Запуск** — `if __name__ == "__main__"` с `TestRunner`.

---

### 🚨 КРИТИЧЕСКОЕ ПРАВИЛО — Где писать файлы (НАРУШАТЬ НЕЛЬЗЯ!)

> ⚠️ **Это правило ВЫШЕ всех остальных!** Нарушение = потеря работы Alex.

**ПРОБЛЕМА**: Агенты иногда запускаются в git worktree (`.claude/worktrees/*/`).
Файлы созданные в worktree **НЕ попадают в основной git и НЕ передаются через GitHub!**
Работа в worktree = работа "в никуда" — файлы теряются при закрытии сессии.

**ПРАВИЛО: ВСЕ файлы писать ТОЛЬКО в корень репозитория:**

```
✅ ПРАВИЛЬНО:  <корень репозитория>/MemoryBank/...
✅ ПРАВИЛЬНО:  <корень репозитория>/PyCore/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Old/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/Review/yyyy-mm-dd_HH-min.md
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/Doxygen/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/API.md
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/Full.md
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/Doc/Quick.md
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/include/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/src/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/python/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/test_cpp/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/test_python/...
✅ ПРАВИЛЬНО:  <корень репозитория>/[модуль]/CMakeLists.txt

❌ ЗАПРЕЩЕНО:  <любой путь>/.claude/worktrees/<имя>/MemoryBank/...
❌ ЗАПРЕЩЕНО:  <любой путь>/.claude/worktrees/<имя>/Doc/...
❌ ЗАПРЕЩЕНО:  любой путь содержащий /.claude/worktrees/
```

**КАК ПРОВЕРИТЬ** перед записью файла:
- Путь содержит `.claude/worktrees/`? → ❌ СТОП! Запиши в корень репозитория!
- `git rev-parse --show-toplevel` — это и есть правильный корень, туда и писать.

---

## 📚 Документация модулей

> Каждый модуль должен иметь **несколько видов документации**, включая автогенерируемую Doxygen-документацию.

### Виды документации

| Файл/Папка | Назначение | Аудитория |
|-----------|-----------|----------|
| `Doc/API.md` | Краткий справочник по публичному API | Разработчики-пользователи |
| `Doc/Full.md` | Полная документация: архитектура, алгоритмы, примеры | Разработчики |
| `Doc/Quick.md` | Быстрый старт: установка, минимальный пример | Новички |
| `Doc/Doxygen/` | Web-документация, автогенерируемая из комментариев | Все |
| `Doc/Review/` | История изменений, анализ рефакторинга | Команда |

### 📄 API.md — что включать
- Список всех публичных функций/классов с сигнатурами
- Краткое описание параметров и возвращаемых значений
- Минимальный пример вызова для каждой функции

### 📖 Full.md — что включать
- Описание алгоритма (математика, формулы)
- Архитектурные решения и почему так
- Диаграммы (Mermaid)
- Подробные примеры с пояснениями
- Таблица тестов
- Ссылки на источники

### ⚡ Quick.md — что включать
- Зависимости и установка
- 1-2 минимальных рабочих примера
- Ссылка на Full.md для деталей

### 🌐 Doxygen — web-документация

**Конфигурация**: `[модуль]/Doc/Doxygen/Doxyfile`
**HTML вывод**: `[модуль]/Doc/Doxygen/html/`
**Запуск**: `doxygen [модуль]/Doc/Doxygen/Doxyfile`

Все публичные функции и классы должны иметь **Doxygen-совместимые комментарии**:

```cpp
/**
 * @brief Краткое описание (одна строка)
 *
 * Подробное описание: что делает, какой алгоритм, ограничения.
 *
 * @param x    Входной аргумент (диапазон, единицы измерения)
 * @param n    Количество точек аппроксимации
 * @return     Результат вычисления
 * @note       Важное замечание
 * @warning    Предупреждение
 * @see        Связанная функция
 *
 * @example
 * @code
 * double result = myFunction(1.0, 10);
 * @endcode
 */
double myFunction(double x, int n);
```

### 📝 Review/ — история изменений
- Файлы: `yyyy-mm-dd_HH-min.md`
- Содержит: анализ исходного кода, предложения по изменениям, решения
- Хранится **постоянно** как история рефакторинга

---

## 💻 Стиль кода

### C Code Style (для рефакторинга C-кода)
- **Стандарт**: C17 (MSVC) / C11 fallback (GCC)
- **Отступы**: 2 пробела (не табуляция)
- **Именование** (сохранять стиль оригинала):
  - Функции: `snake_case` → `discr2()`, `discr_common()`
  - Типы: `UPPER_CASE` → `DISCRTYPE`
  - Переменные: `snake_case` → `maz`, `mel`, `mval`
  - Файлы: `snake_case.h`, `snake_case.c`
- **extern "C"**: обязательно в заголовках для совместимости с C++

### C++ Code Style (для обёрток, тестов, _new версий)
- **Стандарт**: Google C++ Style Guide
- **Отступы**: 2 пробела (не табуляция)
- **Именование**:
  - Классы: `CamelCase` → `DiscrEstimator`, `TestRunner`
  - Методы/функции: `snake_case` → `compute_value()`, `get_result()`
  - Константы: `kCamelCase` → `kMaxPoints`, `kDefaultPrecision`
  - Переменные: `snake_case` → `input_data`, `num_points`
  - Члены класса: `snake_case_` → `data_`, `size_`
  - Файлы: `snake_case.hpp`, `snake_case.cpp`

### Комментарии
- Doxygen (`/** */`) для публичного API (и C, и C++)
- `//` для внутренней логики — **только где неочевидно**
- Комментарии на **русском или английском** (как в оригинале)

---

## 🔬 Тесты на C++

### Структура test_cpp/
```
test_cpp/
├── all_test.hpp        # Точка входа — вызывает все тесты модуля
├── test_basic.hpp      # Базовые тесты
├── test_edge_cases.hpp # Граничные случаи
├── test_performance.hpp # Тесты производительности (опционально)
├── Data/               # Тестовые данные (если нужны)
└── README.md           # Описание тестов
```

### Паттерн all_test.hpp
```cpp
#pragma once
/**
 * @file all_test.hpp
 * @brief Все тесты модуля [название]
 */
#include "test_basic.hpp"
#include "test_edge_cases.hpp"

namespace [module]_all_test {
inline void run() {
  test_basic::run_all();
  test_edge_cases::run_all();
}
}  // namespace
```

### Паттерн C++ теста для C-библиотеки
```cpp
#pragma once
// C++ тест включает C-заголовки через extern "C"
extern "C" {
#include "../include/discr_common.h"
#include "../include/discrcg.h"
}
#include <cassert>
#include <iostream>
#include <cmath>

namespace discr_test_cg {
inline void test_two_point() {
  double maz[2][2] = {{1.0, 2.0}, {3.0, 4.0}};
  double mel[2][2] = {{1.0, 2.0}, {3.0, 4.0}};
  double mval[2][2] = {{10.0, 20.0}, {30.0, 40.0}};
  double az, el, val;
  int result = discr2(maz, mel, mval, &az, &el, &val);
  assert(result == 0);
  std::cout << "[PASS] test_two_point_cg\n";
}

inline void run_all() {
  test_two_point();
}
}  // namespace
```

---

## 🐍 Python Тесты и Биндинги

### PyCore — общая инфраструктура

`PyCore/` содержит переиспользуемый код для тестирования и визуализации.
Источник: `..\GPUWorkLib\Python_test\common` (адаптировано без GPU-специфики).

```
PyCore/
├── __init__.py
├── runner.py      # TestRunner + SkipTest
├── result.py      # TestResult, ValidationResult
├── reporters.py   # Отчёты
├── validators.py  # Валидация результатов
└── plotting/      # Графики (matplotlib)
    └── plotter_base.py
```

### Python тесты (test_python/)
```python
# test_python/test_approximation.py
import sys
sys.path.insert(0, '../../')  # путь к PyCore

from PyCore.runner import TestRunner, SkipTest
import numpy as np

class TestApproximation:
    def test_basic_values(self):
        # ...
        assert abs(result - expected) < 1e-6

    def test_edge_cases(self):
        # ...

if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(TestApproximation())
    runner.print_summary(results)
```

**Запуск**: `python test_python/test_approximation.py`

### Python биндинги (python/)

**Два подхода** в зависимости от языка модуля:
- **C-модули**: `ctypes` — загрузка .dll/.so напрямую, без компиляции биндинга
- **C++ модули/обёртки**: `pybind11` — когда C++ обёртка стабилизируется

**Последовательность**: сначала ctypes (быстрый старт) → потом pybind11 (если нужно)

Документация: `Doc/API.md` раздел "Python API"

---

## 🔄 Workflow & Development Style

### Итеративный подход
1. **Анализ** — изучить оригинальный код в `Old/`, написать Review
2. **Рефакторинг** — перенести в `include/` + `src/`, не меняя интерфейс
3. **Тесты C++** — написать тесты в `test_cpp/`
4. **Python тесты** — написать тесты в `test_python/`, сравнить с NumPy/SciPy
5. **Документация** — API.md, Full.md, Quick.md, Doxygen
6. **Очистка** — удалить промежуточные заметки

### Когда использовать помощников (синьоров)
- 📚 **Context7**: Контекст по библиотекам, API
- 🌐 **URL / WebFetch**: Документация по релевантным библиотекам
- 🧮 **sequential-thinking**: Сложная математика, рефакторинг, архитектура
- 🔍 **Explore agent**: Поиск по большой кодовой базе
- 📐 **Plan mode**: Рефакторинг архитектуры
- 🐙 **GitHub**: Поиск референсного кода

> 🚨 **СИНЬОРЫ И АГЕНТЫ**: Любые результаты (анализ, ревью, планы) — записывать ТОЛЬКО в основной `MemoryBank/`, никогда в worktree! Агенты могут читать код из worktree, но ПИСАТЬ только в основной каталог проекта.

### Принятие решений
- **Быстрые решения**: Прототипировать и тестировать
- **Архитектурные решения**: Сначала обсудить с Alex
- **API изменения**: Запрещены при рефакторинге!

### Приоритеты
1. ✅ **Корректность** — результат должен совпадать с оригиналом (сравнение с NumPy/SciPy)
2. 🔧 **Работоспособность** — код должен компилироваться и работать
3. 📝 **Документация** — когда API стабилизировался
4. ⚡ **Производительность** — не хуже оригинала
5. 🧹 **Очистка** — удаление промежуточной информации после завершения

---

## 🏗️ Architecture & Code Organization

### Правила рефакторинга
| Можно ✅ | Нельзя ❌ |
|---------|---------|
| Изменить алгоритм (если результат тот же) | Изменить сигнатуру функций |
| Добавить проверки индексов | Изменить семантику параметров |
| Оптимизировать циклы | Изменить возвращаемые значения |
| Переименовать внутренние переменные | Изменить публичный API |
| Разбить длинную функцию на части | Изменить поведение при граничных условиях |
| Добавить комментарии | Добавить новую функциональность (без согласования) |
| Добавить C++ вариант с `_new` (с обоснованием) | Менять язык оригинала (C остаётся C) |

### Структура файлов
- **Один класс — один файл** (исключение: мелкие вспомогательные структуры)
- **Заголовки**: `include/*.hpp` — только объявления
- **Реализация**: `src/*.cpp` — только реализации
- **Тесты**: `test_cpp/*.hpp` — inline функции, без отдельных .cpp

### Вызов тестов из main (если нужен общий main)
```
test_main.cpp
  → [модуль1]/test_cpp/all_test.hpp
  → [модуль2]/test_cpp/all_test.hpp
```

---

## 📖 В начале сессии
1. Прочитать `MemoryBank/MASTER_INDEX.md` — статус проекта
2. Проверить `MemoryBank/tasks/IN_PROGRESS.md` — что в работе
3. Проверить последнюю сессию в `MemoryBank/sessions/`

## 💻 Во время работы
1. **Context7** — запрашивать по релевантным темам
2. **sequential-thinking** MCP — разбирать сложные задачи
3. Записывать выполненные задачи в `tasks/COMPLETED.md`
4. Обновлять спецификации при изменении API
5. Добавлять исследования в `research/`

## 📝 В конце сессии
1. Записать краткое резюме в `sessions/YYYY-MM-DD.md`
2. Обновить `changelog/YYYY-MM.md`
3. Перенести завершённые задачи в COMPLETED

## 🗣️ Команды от Alex
```
"Покажи статус"          → MemoryBank/MASTER_INDEX.md + tasks/IN_PROGRESS.md
"Добавь задачу: ..."     → tasks/BACKLOG.md
"Запиши в спеку: ..."    → specs/{module}.md
"Сохрани исследование"   → research/
"Что сделали сегодня?"   → Создать sessions/YYYY-MM-DD.md
```

---

## 📋 Key Settings

### File Naming
- Формат даты: `YYYY-MM-DD` или `YYYY-MM-DD_HH-MM-SS`
- Review файлы: `[модуль]/Doc/Review/YYYY-MM-DD_HH-min.md`
- Python тесты: `[модуль]/test_python/test_*.py`
- C++ тесты: `[модуль]/test_cpp/*.hpp`
- Doxygen конфиг: `[модуль]/Doc/Doxygen/Doxyfile`

### Communication Preferences
- **Language**: Русский (Russian)
- **Tone**: Friendly, supportive, enthusiastic
- **Use emojis**: Yes ✅
- **Be detailed**: When needed, but also be concise
- **Ask questions**: When in doubt, always ask for clarification

---

*Last updated: 2026-03-28*
*Maintained by: Кодо (AI Assistant)*
