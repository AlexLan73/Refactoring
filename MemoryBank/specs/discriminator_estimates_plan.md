# Plan: discriminator_estimates — Рефакторинг + Документация + Тесты

**Дата**: 2026-03-28
**Автор**: Кодо (sequential-thinking + context7)
**Модуль**: discriminator_estimates/Old/
**Язык**: C (C17/C11)

---

## 1. Обзор исходного кода

### Файлы (6 заголовков + 5 исходников, ~400 строк)

| Файл | Строк | Автор | Описание |
|------|-------|-------|----------|
| discr_types.h | 52 | Керский Е.В. | enum DISCRTYPE (DT_NO, DT_CG, DT_SD, DT_QA, DT_EA) |
| discr_common.h | 62 | Керский Е.В. | Обёртки: discr2, discr3, discr3_, checkuse3d, conv3to2 |
| discrcg.h | 50 | Федоров С.А. | Центр тяжести: discr2cg, discr3cg, discrncg |
| discrsd.h | 44 | Федоров С.А. | Суммарно-разностный: discr2sd |
| discrqa.h | 43 | Федоров С.А. | Квадратичная аппроксимация: discr3qa |
| discrea.h | 45 | Добродумов А.Б. | Экспоненциальная аппроксимация: discr3ea, discr3eaY |
| discrcg.c | 91 | Федоров С.А. | Реализация CG |
| discrsd.c | 52 | Федоров С.А. | Реализация SD |
| discrqa.c | 66 | Федоров С.А. | Реализация QA |
| discrea.c | 180 | Добродумов А.Б. | Реализация EA (самая сложная) |
| discr_common.c | 160 | Керский Е.В. | Обёртки discr3, discr3_, checkuse3d |

### Функции (11 объявлено, 9 реализовано)

| Функция | Тип | Формула | Статус |
|---------|-----|---------|--------|
| discr2cg(A1,A2,x1,x2) | CG 2-точ | xe = sum(Ai*xi)/sum(Ai) | ✅ |
| discr3cg(A1..A3,x1..x3) | CG 3-точ | то же, 3 точки | ✅ |
| discrncg(A*,x*,N) | CG N-точ | то же, N точек | ✅ |
| discr2sd(c,A1,A2,x1,x2) | SD 2-точ | xe = mid + c*(A2-A1)/(A2+A1) | ✅ |
| discr3qa(A1..A3,x1..x3) | QA 3-точ | Вершина параболы через 3 точки | ✅ |
| discr3ea(A1..A3,x1..x3,*xe) | EA 3-точ | Вершина exp(-a*x²) через 3 точки | ✅ |
| discr3eaY(A1,A2,x1,x2,xe) | EA ампл | Уточнение амплитуды | ✅ |
| discr3(**maz,**mel,**mval,...) | Обёртка | QA/EA по матрицам ДН | ✅ |
| discr3_(maz[3][3],...) | Обёртка | Адаптер для массивов 3x3 | ✅ |
| checkuse3d(**maz,...) | Проверка | Можно ли использовать 3-точ | ✅ |
| **discr2(...)** | **Обёртка** | **2-точечный** | ❌ **НЕТ РЕАЛИЗАЦИИ!** |
| **conv3to2(...)** | **Конверт** | **3x3 → 2x2** | ❌ **НЕТ РЕАЛИЗАЦИИ!** |

---

## 2. Критические проблемы (баги)

### 🔴 BUG-1: discr2() и conv3to2() — объявлены, НЕ реализованы
- **Где**: discr_common.h:37-38, 54-55
- **Риск**: undefined reference при линковке если кто-то вызовет
- **Решение**: реализовать или убрать из интерфейса
- ⚠️ **ВОПРОС К ALEX**: реализовать или удалить?

### 🔴 BUG-2: Глобальная static переменная ax[3] — NOT thread-safe
- **Где**: discrea.c:30-34 — `static struct axstr ax[3]`
- **Риск**: race condition при многопоточном вызове discr3ea()
- **Решение**: сделать локальной переменной в discr3ea()

### 🔴 BUG-3: discr3() модифицирует входные данные!
- **Где**: discr_common.c:74-79 — `maz[i][j] *= c; mel[i][j] *= c;`
- **Риск**: после вызова входные массивы ИЗМЕНЕНЫ. Повторный вызов даст неверный результат
- **Решение**: работать с локальными копиями или делить обратно (строки 108-109 делят только результат)
- ⚠️ **ВОПРОС К ALEX**: это баг или намеренное поведение?

### 🟡 BUG-4: FLT_EPSILON вместо DBL_EPSILON для double
- **Где**: discrqa.c:45,47 + discr_common.c:130
- **Риск**: FLT_EPSILON (~1e-7) слишком грубо для double, может пропустить различия
- **Решение**: заменить на DBL_EPSILON или подходящий порог

### 🟡 BUG-5: Нет защиты от деления на 0
- **Где**: discr2cg (A1+A2=0), discr3cg (A1+A2+A3=0), discrncg (As=0), discr2sd (A2+A1=0)
- **Риск**: NaN/Inf при нулевых амплитудах
- **Решение**: проверка суммы != 0, возврат значения по умолчанию или кода ошибки

### 🟢 BUG-6: discr3() не поддерживает DT_CG, DT_SD
- **Где**: discr_common.c:81 — switch обрабатывает только DT_QA и DT_EA
- **Риск**: вызов с DT_CG возвращает -2 (ошибка)
- **Решение**: добавить case DT_CG и DT_SD, или документировать ограничение
- ⚠️ **ВОПРОС К ALEX**: добавить поддержку или оставить?

### 🟢 STYLE-1: Смешанные табуляции/пробелы
- **Где**: discrqa.c:47-59
- **Решение**: заменить на 2 пробела

---

## 3. Альтернативные решения (рассмотрены)

| Вариант | Время | Надёжность | Зависимости | Вердикт |
|---------|-------|-----------|-------------|---------|
| **A: Рефакторинг своего кода + тесты** | **3-5 ч** | **Высокая** | **0** | ✅ **ВЫБРАН** |
| B: Переписать на GSL (полиномиальная интерполяция) | 4-6 ч | Средняя | GSL | ❌ Overkill для 3 точек |
| C: Переписать на C++ с Eigen | 3-5 ч | Средняя | Eigen | ❌ Меняет язык |
| D: Только тесты без рефакторинга | 1-2 ч | Низкая | 0 | ❌ Баги остаются |
| E: Использовать scipy.optimize в Python | +1 ч | Высокая | scipy | ✅ Для эталона в тестах |

**Обоснование выбора A**: формулы простые (closed-form), код ~400 строк. Внешние библиотеки увеличат зависимости без пользы. Numpy/Scipy используем только для валидации в Python тестах.

**Из Context7 (Modern CMake)**: используем target_compile_features для C standard, set(CMAKE_C_STANDARD 17) с fallback. Static library + кросс-платформенная сборка MSVC/GCC.

**Из Context7 (pybind11)**: для Python тестов C-кода ctypes проще (не нужна компиляция биндинга). pybind11 оставим для будущей C++ обёртки.

---

## 4. План работ по фазам

### Фаза 0: Подготовка (30 мин)

| # | Задача | Файл |
|---|--------|------|
| 0.1 | Создать структуру папок | include/, src/, test_cpp/, test_python/, Doc/, Doc/Review/, Doc/Doxygen/ |
| 0.2 | Скопировать заголовки Old/include/ → include/ | **БЕЗ изменений интерфейса** |
| 0.3 | Создать CMakeLists.txt | Кросс-платформенный (MSVC C17 + GCC) |
| 0.4 | Проверить сборку Old/ кода на Windows | cmake + build |

**CMakeLists.txt (шаблон)**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(discriminator_estimates LANGUAGES C)

# C17 если компилятор поддерживает, иначе C11
set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED OFF)

set(SOURCES
  src/discrcg.c
  src/discrea.c
  src/discrqa.c
  src/discrsd.c
  src/discr_common.c
)

# Статическая библиотека
add_library(discr STATIC ${SOURCES})
target_include_directories(discr PUBLIC include/)

# Shared для Python ctypes (.dll/.so)
add_library(discr_shared SHARED ${SOURCES})
target_include_directories(discr_shared PUBLIC include/)
if(WIN32)
  set_target_properties(discr_shared PROPERTIES
    WINDOWS_EXPORT_ALL_SYMBOLS ON
    OUTPUT_NAME "discr"
  )
endif()

# Compiler warnings
if(MSVC)
  target_compile_options(discr PRIVATE /W4)
  target_compile_options(discr_shared PRIVATE /W4)
else()
  target_compile_options(discr PRIVATE -Wall -Wextra -pedantic)
  target_compile_options(discr_shared PRIVATE -Wall -Wextra -pedantic)
endif()
```

---

### Фаза 1: Рефакторинг C-кода (1.5-2 часа)

**Правило**: интерфейс (.h) НЕ менять! Менять только реализацию (.c).

| # | Задача | Приоритет | Файл |
|---|--------|-----------|------|
| 1.1 | BUG-2: static ax[3] → локальная переменная | 🔴 Critical | discrea.c |
| 1.2 | BUG-3: discr3() — не модифицировать входные maz/mel | 🔴 Critical | discr_common.c |
| 1.3 | BUG-4: FLT_EPSILON → DBL_EPSILON для double | 🟡 Important | discrqa.c, discr_common.c |
| 1.4 | BUG-5: Защита от деления на 0 (CG, SD) | 🟡 Important | discrcg.c, discrsd.c |
| 1.5 | BUG-1: Реализовать discr2() и conv3to2() | ⚠️ После ответа Alex | discr_common.c |
| 1.6 | BUG-6: Добавить DT_CG/DT_SD в discr3() | ⚠️ После ответа Alex | discr_common.c |
| 1.7 | STYLE-1: Единые 2-пробельные отступы | 🟢 Style | все .c файлы |
| 1.8 | Doxygen комментарии (расширить существующие) | 🟢 Style | все .c файлы |
| 1.9 | Записать Review (что изменено и почему) | 📝 Doc | Doc/Review/ |

---

### Фаза 2: C++ тесты (1-1.5 часа)

```
test_cpp/
├── all_test.hpp
├── test_discr_cg.hpp      # CG: 2-точ, 3-точ, N-точ, деление на 0
├── test_discr_sd.hpp      # SD: базовый, деление на 0
├── test_discr_qa.hpp      # QA: базовый, A1=A2=A3, A2=A3, A1=A2
├── test_discr_ea.hpp      # EA: базовый, вогнутость, нулевые ампл, ограничения
├── test_discr_common.hpp  # discr3, discr3_, checkuse3d (+ discr2, conv3to2)
└── README.md
```

**Тестовые сценарии**:

| Функция | Тест | Входные данные | Ожидаемый результат |
|---------|------|---------------|---------------------|
| discr2cg | Равные амплитуды | A1=A2=1, x1=0, x2=1 | 0.5 (середина) |
| discr2cg | Одна доминирует | A1=1, A2=99, x1=0, x2=1 | ~0.99 (ближе к x2) |
| discr2cg | Нулевые амплитуды | A1=0, A2=0 | обработка ошибки |
| discr3cg | Симметричный | A=[1,3,1], x=[-1,0,1] | 0.0 |
| discrncg | Один пик | A=[0,0,10,0,0], x=[-2,-1,0,1,2] | 0.0 |
| discr2sd | Равные амплитуды | c=1, A1=A2=1, x1=0, x2=1 | 0.5 |
| discr3qa | Парабола в центре | A=[1,3,1], x=[-1,0,1] | 0.0 |
| discr3qa | A2=A3 | A=[1,5,5], x=[0,1,2] | 1.5 |
| discr3ea | Гауссов пик | A=exp(-x²), x=[-1,0,1] | ~0.0 |
| discr3ea | Вогнутость | A=[2,4,8], x=[-1,0,1] | EXIT_FAILURE |

---

### Фаза 3: Python тесты (1-1.5 часа)

```
test_python/
├── test_discriminators.py      # Основные тесты через ctypes
├── test_discriminators_ref.py  # Эталонные реализации на numpy
└── test_discriminators_plot.py # Визуализация (matplotlib)
```

**Эталонные реализации на numpy/scipy**:
```python
# CG — тривиально:
def ref_cg(A, x):
    return np.average(x, weights=A)

# QA — квадратичная аппроксимация через polyfit:
def ref_qa(A, x):
    coeffs = np.polyfit(x, A, 2)  # ax²+bx+c
    return -coeffs[1] / (2 * coeffs[0])  # вершина параболы

# EA — экспоненциальная аппроксимация:
def ref_ea(A, x):
    from scipy.optimize import curve_fit
    def gauss(x, x0, a, sigma):
        return a * np.exp(-((x - x0) / sigma) ** 2)
    popt, _ = curve_fit(gauss, x, A, p0=[x[1], max(A), 1.0])
    return popt[0]  # x0
```

**ctypes загрузка** (кросс-платформенная):
```python
import ctypes, os, platform

if platform.system() == 'Windows':
    lib = ctypes.CDLL('./build/Release/discr.dll')
else:
    lib = ctypes.CDLL('./build/libdiscr.so')
```

---

### Фаза 4: Документация (1 час)

| Файл | Содержание |
|------|-----------|
| Doc/API.md | Все 11 функций: сигнатура, параметры, возврат, пример |
| Doc/Full.md | Математика (формулы), алгоритмы, диаграммы Mermaid, таблица тестов |
| Doc/Quick.md | Как собрать + 1 пример вызова |
| Doc/Doxygen/Doxyfile | Конфигурация для автогенерации |
| Doc/Review/2026-03-28_*.md | Анализ Old/ кода, список багов, решения |

---

## 5. Вопросы к Alex ⚠️

> Перед началом Фазы 1 нужны ответы:

**Q1**: `discr2()` и `conv3to2()` — объявлены в discr_common.h но нет реализации.
- (a) Реализовать по аналогии с другими функциями?
- (b) Убрать из заголовка?
- (c) Оставить как есть (реализация в другом месте)?

**Q2**: `discr3()` умножает входные maz, mel на коэффициент `c` — это баг?
- (a) Баг → работать с копиями
- (b) Намеренно → документировать

**Q3**: `discr3()` не поддерживает DT_CG и DT_SD — добавить?
- (a) Добавить (полная поддержка всех типов)
- (b) Оставить только QA + EA

**Q4**: Сборка на Windows сегодня — какой генератор CMake?
- (a) Visual Studio 17 2022
- (b) Ninja + MSVC
- (c) MinGW/MSYS2

---

## 6. Порядок работы (Timeline)

### Сегодня (Windows 11, MSVC):
```
Фаза 0 → Фаза 1 (баги) → Сборка → Фаза 2 (C++ тесты) → Фаза 3 (Python ctypes .dll)
```

### Понедельник (Debian, GCC):
```
Проверить сборку GCC → Доработать Python (.so) → Фаза 4 (документация) → Doxygen
```

---

## 7. Критерии завершения (Definition of Done)

- [ ] Все 6 багов исправлены (или решение принято по каждому)
- [ ] Код компилируется на MSVC без warnings (/W4)
- [ ] Код компилируется на GCC без warnings (-Wall -Wextra -pedantic)
- [ ] C++ тесты: все PASS (≥15 тестов)
- [ ] Python тесты: сравнение с numpy/scipy эталоном, tolerance < 1e-10
- [ ] Документация: API.md, Full.md, Quick.md
- [ ] Doxygen: html генерируется
- [ ] Review записан в Doc/Review/

---

*Составлен: Кодо (sequential-thinking + context7)*
*Источники: Modern CMake docs, pybind11 docs, scipy.optimize*
