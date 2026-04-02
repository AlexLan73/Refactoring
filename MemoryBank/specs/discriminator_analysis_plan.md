# Plan: Аналитическое исследование точности дискриминаторов

**Дата**: 2026-04-02
**Автор**: Кодо (AI) + Alex
**Расположение кода**: `discriminator_estimates/test_python/analysis/`
**Базовые наработки**: `test_python/test_discriminators.py`, `test_python/test_discriminators_plot.py`, `test_python/test_fft_frequency.py`

---

## Конвенция sinc

> **sinc(x) = sin(x)/x** (ненормализованный), sinc(0) = 1.
> ⚠️ **НЕ** `numpy.sinc` (который нормализованный: sin(πx)/(πx)).
> Использовать кастомную реализацию из `common.py`.

---

## Цель

Систематическое исследование точности 4 дискриминаторов (CG, SD, QA, EA)
при перемещении точки перегиба (максимума) sinc(x) от крайнего левого
до крайнего правого положения на сетке из 3 отсчётов.

**Визуально**: на картинке `sinc_discriminator_estimates.png` видны
3 жёлтые точки (отсчёты ДН) + вертикальные линии (оценки CG/QA/EA).
Нужно "прогнать" пик sinc(x) через все положения и собрать статистику.

---

## Гипотезы для проверки

| # | Гипотеза | Проверяется в |
|---|----------|---------------|
| H1 | EA даёт наименьшую ошибку в нормальной зоне | Этапы 1-2 |
| H2 | QA более устойчив к шуму, чем EA | Этап 6 |
| H3 | CG имеет линейный bias, пропорциональный смещению | Этапы 1-3 |
| H4 | Точность SD определяется выбором коэффициента `c` | Этапы 1, 4 |
| H5 | Экстраполяция даёт разумные оценки в монотонной зоне | Этап 1 (экстраполяция) |

---

## Этапы работы

### Этап 0. Валидация C ↔ Python + рефакторинг common.py (prerequisite)

#### Задача A — сборка C-библиотеки

> ⚠️ **БЕЗ ЭТОГО ничего не работает!**

```bash
cd discriminator_estimates
mkdir -p build && cd build
cmake .. && cmake --build .
# Результат: build/libdiscr_shared.so (Linux) или build/discr.dll (Windows)
```

#### Задача B — создать analysis/__init__.py + common.py

**Создать** `analysis/__init__.py` (пустой файл) — чтобы Python видел `analysis` как пакет.

**Создать** `analysis/common.py` — вынести общий код:

| Функция | Откуда брать (точный source) | Сигнатура |
|---------|------------------------------|-----------|
| `sinc(x)` | `test_discriminators.py:49-55` | `sinc(x) → ndarray` |
| `ref_cg_2pt(A1, A2, x1, x2)` | **НОВАЯ** (порт `discr2cg`) | `→ float` (2-точечный, как C-код) |
| `ref_cg_3pt(A, x)` | `test_discriminators.py:60-67` | `→ float` (все точки) |
| `ref_sd(c, A1, A2, x1, x2)` | `test_discriminators_plot.py:52-56` | `→ float` |
| `ref_qa(A, x)` | `test_discriminators.py:70-77` | `→ float` |
| `ref_ea(A, x)` | `test_discriminators_plot.py:66-75` | `→ float` (curve_fit) |
| `load_discr_lib()` | `test_discriminators.py:29-44` | `→ ctypes.CDLL` |
| `select_top2(A, x)` | **НОВАЯ** | `→ (A1, A2, x1, x2)` — 2 макс. по амплитуде |

**ref_cg_2pt** — реализация:
```python
def ref_cg_2pt(A1, A2, x1, x2):
    """CG: 2-точечный (как C-функция discr2cg)."""
    s = A1 + A2
    if abs(s) < 1e-15:
        return (x1 + x2) * 0.5
    return (A1 * x1 + A2 * x2) / s
```

**select_top2** — реализация:
```python
def select_top2(A, x):
    """Выбрать 2 отсчёта с максимальными амплитудами (как conv3to2 в C)."""
    idx = np.argsort(A)[-2:]  # два наибольших
    idx = np.sort(idx)        # порядок по x
    return A[idx[0]], A[idx[1]], x[idx[0]], x[idx[1]]
```

**Шаблон импорта** для analysis-скриптов (`01_sweep_accuracy.py` и др.):
```python
import sys
from pathlib import Path

# Пути: analysis/ → test_python/ → discriminator_estimates/ → Refactoring/
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent          # discriminator_estimates/
REPO_ROOT    = MODULE_DIR.parent                    # Refactoring/
sys.path.insert(0, str(REPO_ROOT))                 # для PyCore
sys.path.insert(0, str(ANALYSIS_DIR))              # для common

from common import sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, select_top2
from PyCore.runner import TestRunner, SkipTest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")  # единый стиль с test_discriminators_plot.py
```

#### Задача C — валидация C ↔ Python

Проверить совпадение Python-реализаций с C-кодом (через ctypes):

| Метод | Tolerance | Примечание |
|-------|-----------|------------|
| CG (ref_cg_2pt) | < 1e-12 | Точная формула |
| SD (ref_sd) | < 1e-12 | При одинаковом `c` |
| QA (ref_qa) | < 1e-12 | Точная формула |
| EA (ref_ea) | < 1e-6, **только нормальная зона** | C и Python используют разные алгоритмы! |

> ⚠️ **EA: C-код** (`discr3ea`) возвращает `EXIT_FAILURE` для монотонных данных
> и ставит `*xe` = крайнюю точку. **Python** `ref_ea` (curve_fit) может сойтись
> и вернуть пик за сеткой. **Это НЕ баг** — это разница алгоритмов.
> Для монотонных данных сравнение C↔Python не проводится.

**Выход**: `common.py` + `analysis/__init__.py` + валидация пройдена

**Файл**: `analysis/common.py`

---

### Этап 1. Sweep пика по сетке (основной эксперимент)

**Задача**: сместить максимум sinc(x - x0) от x0 = -1.5 до x0 = +1.5
с мелким шагом (N = 301 точка). Для каждого x0:
- вычислить 3 отсчёта: A1 = sinc(-1 - x0), A2 = sinc(0 - x0), A3 = sinc(1 - x0)
- **3-точечные методы** (QA, EA): подать все 3 отсчёта (A1, A2, A3) → `ref_qa(A, x)`, `ref_ea(A, x)`
- **2-точечные методы** (CG, SD): вызвать `select_top2(A, x)` для отбора 2 макс. амплитуд,
  затем `ref_cg_2pt(A1, A2, x1, x2)` и `ref_sd(c, A1, A2, x1, x2)`
  (это эквивалент C-цепочки `discr3()` → `conv3to2()` → `discr2()`)
- **Монотонный случай**: если A1 ≥ A2 ≥ A3 или A1 ≤ A2 ≤ A3 (нет перегиба) →
  дополнительно запустить экстраполяцию (см. Этап 1.1)
- записать: x0_true, xe_cg, xe_sd, xe_qa, xe_ea, xe_extrap, err_*, is_monotonic
- **xe_extrap = NaN** для немонотонных случаев (`np.nan` в pandas/CSV)

**Параметр калибровки SD**:
> `discrsd(c, A1, A2, x1, x2)` требует коэффициент `c`.
> - **c = 1.0** — default для основной таблицы sweep
> - `c = 2π·dx/λ` — как в `discr3()` для физических координат
> Исследовать влияние `c` на точность SD отдельно (подэтап: серия c = 0.5, 1.0, 1.5, 2.0).
>
> ⚠️ **SD в sinc-домене работает с амплитудами**, а НЕ с мощностями.
> В FFT-домене (`fft_discr_sd`) используется `|S|²` — это другой режим!

**Диапазоны x0**:

| Зона | x0 | Характер данных |
|------|----|-----------------|
| Нормальная | [-0.5, +0.5] | Пик между отсчётами, все методы работают |
| Граничная | [-1.0, -0.5] и [+0.5, +1.0] | Пик у края/за краем сетки |
| Экстремальная | < -1.0 и > +1.0 | Пик за пределами сетки — нет перегиба! |

**Экстремальные случаи** (без перегиба):

```
Все убывают:  A1 > A2 > A3   (x0 < -1.5, пик далеко слева)
Все возрастают: A1 < A2 < A3  (x0 > +1.5, пик далеко справа)
Монотонные:  A1 = A2 > A3     (вырожденные)
Все равны:   A1 = A2 = A3     (плоская "ДН")
```

**Выход**: таблица [N строк x 11 столбцов] + CSV-файл (включая xe_extrap, is_monotonic)

**Файл**: `analysis/01_sweep_accuracy.py`

---

### Этап 1.1. Экстраполяция для монотонных случаев (ОБЯЗАТЕЛЬНО)

**Задача**: когда 3 отсчёта монотонны (нет перегиба на сетке — пик за пределами),
стандартные дискриминаторы ненадёжны. Создать и применить функцию экстраполяции.

**Детектор монотонности**:
```python
def is_monotonic(A1, A2, A3):
    """True если нет локального максимума среди 3 точек."""
    return (A1 >= A2 >= A3) or (A1 <= A2 <= A3)
```

**Методы экстраполяции** (реализовать все 3, сравнить):

| # | Метод | Формула | Когда лучше |
|---|-------|---------|-------------|
| E1 | Параболическая экстраполяция | Fit y = a·x² + b·x + c → vertex x_v = -b/(2a) | Пик недалеко от края сетки |
| E2 | Гауссова экстраполяция | Fit y = A·exp(-a·(x-x0)²) → x0 | Пик далеко, sinc ≈ Gaussian |
| E3 | Градиентная экстраполяция | Направление + линейная оценка расстояния по отношению амплитуд | Робастный fallback |

**Параболическая экстраполяция (E1)** — основной метод:
- Фактически QA (`discr3qa`) уже находит вершину параболы, даже если она за сеткой
- Но при монотонных данных парабола может дать вершину далеко от сетки → ограничить:
  `x_extrap = clip(x_vertex, x_min - 2*step, x_max + 2*step)`

**Гауссова экстраполяция (E2)**:
- EA (`discr3ea`) фитит Гауссиан — при монотонных данных `curve_fit` может не сойтись
- Нужны начальные приближения: x0_init = x_edge (край в сторону роста)
- Обязательно: try/except для RuntimeError (несходимость)

**Градиентная экстраполяция (E3)** — fallback:
```python
def extrap_gradient(A, x):
    """Оценка по градиенту: в какую сторону и насколько далеко пик."""
    step = x[1] - x[0]  # шаг сетки (вычисляем из координат!)
    slope, intercept = np.polyfit(x, A, 1)
    # Направление: пик в сторону роста
    x_edge = x[-1] if slope > 0 else x[0]
    # Консервативная оценка: полшага за край
    return x_edge + 0.5 * step * np.sign(slope)
```

> ⚠️ E3 — это **fallback**: если E1 и E2 не сработали.
> Если ВСЕ три метода дали несогласованные результаты (разброс > 2*step),
> записать `xe_extrap = NaN` и пометить как "extrapolation failed".

**Статистика для монотонных случаев** (отдельная таблица):
- Процент монотонных случаев от общего числа
- Ошибка каждого метода экстраполяции (E1, E2, E3)
- Процент несходимости E2 (Гауссиан)
- Рекомендация: какой fallback использовать

**Файл**: `analysis/01_sweep_accuracy.py` (секция extrapolation) + `analysis/common.py` (функции)

---

### Этап 2. Матстатистика

**Задача**: по таблице из Этапа 1 вычислить для каждого метода:

| Метрика | Формула | Смысл |
|---------|---------|-------|
| Mean error | mean(\|xe - x0\|) | Средняя абсолютная ошибка |
| Max error | max(\|xe - x0\|) | Наихудший случай |
| RMSE | sqrt(mean((xe-x0)^2)) | Среднеквадратичная |
| Bias | mean(xe - x0) | Систематическое смещение |
| Std | std(xe - x0) | Разброс оценок |
| 95-percentile | percentile(\|err\|, 95) | Ошибка в 95% случаев |

**Зоны анализа** (статистика отдельно для каждой):
- Вся область [-1.5, +1.5]
- Нормальная [-0.5, +0.5]
- Граничная [-1.0, -0.5] + [+0.5, +1.0]
- Экстремальная (монотонная) [-1.5, -1.0] + [+1.0, +1.5]
- **Только монотонные случаи** — отдельная таблица с экстраполяцией (E1/E2/E3)

**Выход**: сводная таблица + LaTeX/Markdown

**Файл**: `analysis/02_statistics.py`

---

### Этап 3. 2D графики

**Задача**: визуализация результатов Этапов 1-2.

| # | График | X-ось | Y-ось | Описание |
|---|--------|-------|-------|----------|
| 1 | Абсолютная ошибка | x0 | \|xe - x0\| | 4 кривые (CG/SD/QA/EA), логарифм. Y |
| 2 | Знаковая ошибка | x0 | xe - x0 | Bias: знак показывает направление смещения |
| 3 | Отношение xe/x0 | x0 | xe / x0 | Идеал = 1.0 (пропустить \|x0\| < 0.01 — деление на 0!) |
| 4 | Анимация sinc | x | sinc(x-x0) | Серия кадров: пик двигается, оценки следуют |
| 5 | Box-plot по зонам | зона | \|error\| | Сравнение методов по зонам (box + whiskers) |
| 6 | Гистограмма ошибок | error | count | Распределение ошибок каждого метода |

**Файл**: `analysis/03_plots_2d.py`

---

### Этап 4. Влияние шага сетки

**Задача**: повторить Этап 1 для разных шагов сетки (step = 0.3, 0.5, 1.0, 1.5, 2.0).
Сетка: {-step, 0, +step}. Для каждого step — полный sweep x0.

**Выход**: таблица [step x method x metric] — как зависит точность от шага

**Файл**: `analysis/04_grid_step.py`

---

### Этап 5. 3D графики

**Задача**: визуализация зависимости ошибки от ДВУХ параметров одновременно.

| # | График | X | Y | Z (цвет/высота) |
|---|--------|---|---|-----------------|
| 1 | Surface | x0 (смещение) | step (шаг сетки) | \|error\| |
| 2 | Surface | x0 | SNR (шум) | \|error\| |
| 3 | Heatmap | x0 | step | log10(\|error\|) — цветовая карта |
| 4 | Contour | x0 | step | линии равной ошибки (0.01, 0.05, 0.1) |

Каждый 3D-график — для каждого метода отдельно (4 подграфика) + overlay.

**Файл**: `analysis/05_plots_3d.py`

---

### Этап 6. Влияние шума (Monte Carlo)

**Задача**: для фиксированного x0 и step добавить шум к амплитудам:
A_noisy = A + noise, noise ~ N(0, sigma).
Повторить M раз, собрать статистику.

**Параметры**:
- sigma / A_max = [0.001, 0.01, 0.05, 0.1, 0.2] (SNR от 60 до 14 дБ)
- x0 = [0.0, 0.1, 0.2, 0.3, 0.4] — 5 фиксированных смещений
- M = 10000 реализаций (M_fast = 1000 для отладки, M_full = 10000 для финала)
- **Воспроизводимость**: `rng = np.random.default_rng(seed=42)`

**Выход**: таблица [SNR x x0 x method] -> mean_error, std_error, p95_error

**Файл**: `analysis/06_noise_montecarlo.py`

---

### Этап 7. FFT-применение (частотная оценка)

**Задача**: повторить Этапы 1-3 для FFT-дискриминаторов (5 методов: +LAY).
Вместо sinc(x) — комплексный сигнал + Hamming window + FFT.

> ⚠️ **LAY (Jacobsen)** — только Python-реализация (нет C-исходника).
> Остальные 4 метода (exp=EA, sqr=QA, sd, cg) имеют C-аналоги.

> ⚠️ **FFT-методы НЕ используют `common.py` ref_*!**
> Использовать реализации из `test_fft_frequency.py` — словарь `METHODS`.
> Импорт: `from test_fft_frequency import METHODS, create_signal, compute_fft, make_freq_axis`

**Дополнительные параметры**:
- N_fft = [16, 32, 64, 128, 256]
- Окна: Hamming, Blackman, Kaiser(β=8), Kaiser(β=14) — β это параметр `np.kaiser(N, beta)`

**Файл**: `analysis/07_fft_analysis.py`

---

### Этап 8. Итоговый отчёт

**Задача**: собрать все результаты в один отчёт.

**Содержание**:
1. Постановка задачи
2. Методы и формулы (ссылки на C-исходники)
3. Таблицы точности (по зонам, по шагам, по шуму)
4. Графики (2D + 3D)
5. Рекомендации: какой метод использовать при каких условиях
6. Выводы

**Файл**: `analysis/08_report.py` (генерирует Markdown отчёт + сборник графиков)

---

## Структура каталога

```
discriminator_estimates/test_python/analysis/
├── __init__.py                # Пустой (чтобы Python видел analysis как пакет)
├── common.py                  # Общие функции (sinc, ref_*, load_lib, select_top2)
├── 01_sweep_accuracy.py       # Sweep x0 + экстраполяция монотонных
├── 02_statistics.py           # Матстатистика по зонам
├── 03_plots_2d.py             # 6 типов 2D-графиков
├── 04_grid_step.py            # Влияние шага сетки
├── 05_plots_3d.py             # 3D surface + heatmap + contour
├── 06_noise_montecarlo.py     # Monte Carlo с шумом (M=10000)
├── 07_fft_analysis.py         # FFT-дискриминаторы (5 методов, LAY только Python)
├── 08_report.py               # Генератор итогового отчёта
├── results/                   # CSV-таблицы результатов
│   ├── sweep_accuracy.csv
│   ├── extrapolation.csv      # Результаты экстраполяции (монотонные случаи)
│   ├── statistics_by_zone.csv
│   ├── grid_step_sweep.csv
│   ├── noise_montecarlo.csv
│   └── fft_analysis.csv
└── plots/                     # Все графики
    ├── 2d/                    # 2D-графики (6 типов)
    ├── 3d/                    # 3D-графики (4 типа x 4 метода)
    └── report/                # Графики для отчёта
```

---

## Зависимости

- numpy — вычисления
- matplotlib — 2D графики
- scipy — curve_fit для EA, статистика
- mpl_toolkits.mplot3d — 3D surface
- pandas (опц.) — таблицы CSV, сводки

---

## Приоритеты

| Приоритет | Этапы | Описание |
|-----------|-------|----------|
| **P0** (обязательно) | 0, 1, 1.1, 2, 3 | Валидация + Sweep + экстраполяция + статистика + 2D графики |
| **P1** (важно) | 4, 5 | Шаг сетки + 3D |
| **P2** (желательно) | 6, 7 | Шум + FFT |
| **P3** (бонус) | 8 | Итоговый отчёт |

---

## Ожидаемые результаты

1. **Таблица точности** по зонам — для выбора метода в продакшене
2. **Карта применимости** — 3D surface "x0 vs step vs error" для каждого метода
3. **Проверка гипотез** H1-H5 — подтверждение/опровержение с числами
4. **Граничные условия** — при каких параметрах каждый метод "ломается"
5. **Влияние шума** — при каком SNR методы эквивалентны
6. **Стратегия экстраполяции** — какой метод (E1/E2/E3) использовать для монотонных данных, когда переключаться с дискриминатора на экстраполяцию

---

## Граф зависимостей этапов

```
       Этап 0 (common.py + сборка C)
           │
           ▼
    ┌──── Этап 1 + 1.1 (sweep + экстраполяция) ────┐
    │                                                │
    ▼                                                ▼
 Этап 2 (статистика)                          Этап 4 (шаг сетки)
    │                                                │
    ▼                                                ▼
 Этап 3 (2D графики)                          Этап 5 (3D графики)
    │                                                │
    ├────────────────────┬───────────────────────────┘
    ▼                    ▼
 Этап 6 (Monte Carlo)  Этап 7 (FFT)
    │                    │
    └────────┬───────────┘
             ▼
          Этап 8 (итоговый отчёт)
```

> ⚠️ **Каждый этап запускается ТОЛЬКО после завершения его зависимостей!**

---

## Шаблон analysis-скрипта

Все скрипты `01-08` должны следовать этому шаблону:

```python
"""
0X_название.py — Описание
==========================
Запуск: python analysis/0X_название.py
"""
import sys
import numpy as np
from pathlib import Path

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent          # discriminator_estimates/
REPO_ROOT    = MODULE_DIR.parent                    # Refactoring/
sys.path.insert(0, str(REPO_ROOT))                 # для PyCore
sys.path.insert(0, str(ANALYSIS_DIR))              # для common

from common import sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, select_top2
from PyCore.runner import TestRunner, SkipTest

# --- Matplotlib (единый стиль) ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

# --- Воспроизводимость ---
rng = np.random.default_rng(seed=42)

# --- Константы ---
OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_PLOTS   = ANALYSIS_DIR / "plots"


class SweepAnalysis:
    """Основной анализ."""

    def test_sweep_basic(self):
        """Sweep x0 от -1.5 до +1.5."""
        # ... код ...
        assert True


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(SweepAnalysis())
    runner.print_summary(results)
```

**Обязательно**:
- `TestRunner` + `if __name__ == "__main__"` (правило проекта!)
- `plt.style.use("dark_background")` (единый стиль с существующими графиками)
- `rng = np.random.default_rng(seed=42)` (воспроизводимость)
- Запуск: `python analysis/0X_название.py` (НЕ через pytest!)

---

## Источники

- [Parabolic Peak Interpolation (Stanford CCRMA)](https://ccrma.stanford.edu/software/scmp/SCMTheory/ParabolicPeak.pdf)
- [Sinusoidal Peak Interpolation (DSPrelated)](https://www.dsprelated.com/freebooks/sasp/Sinusoidal_Peak_Interpolation.html)
- [SciPy Extrapolation tips](https://docs.scipy.org/doc/scipy/tutorial/interpolate/extrapolation_examples.html)

---

## 🚀 Команда запуска реализации (для AI-исполнителя)

> Эту секцию копировать как prompt для другой AI.

```
Реализуй план аналитического исследования точности дискриминаторов.

📍 Спецификация: MemoryBank/specs/discriminator_analysis_plan.md — ПРОЧИТАЙ ЦЕЛИКОМ ПЕРЕД НАЧАЛОМ.
📍 Проект: /home/alex/C++/Refactoring/
📍 Модуль: discriminator_estimates/

⚠️ КРИТИЧЕСКИЕ ПРАВИЛА (нарушение = потеря работы):
1. pytest ЗАПРЕЩЁН! Только `python файл.py` + TestRunner из PyCore
2. Файлы писать ТОЛЬКО в основной каталог проекта, НИКОГДА в .claude/worktrees/
3. Не менять существующий C-код и публичный API
4. Все графики: plt.style.use("dark_background")

📋 ПОРЯДОК РАБОТЫ (строго по графу зависимостей):

ФАЗА 1 — Фундамент (Этап 0):
  1. Собрать C-библиотеку: cd discriminator_estimates && mkdir -p build && cd build && cmake .. && cmake --build .
  2. Создать analysis/__init__.py (пустой файл)
  3. Создать analysis/common.py — по таблице из Этапа 0 (sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, select_top2, load_discr_lib)
     ИСТОЧНИКИ ФУНКЦИЙ:
       sinc, ref_cg(→ref_cg_3pt), ref_qa, load_discr_lib → из test_discriminators.py
       ref_sd, ref_ea → из test_discriminators_plot.py
       ref_cg_2pt, select_top2 → НОВЫЕ (код в спеке)
  4. Написать тесты валидации C↔Python в common.py (self-test)
  5. Запустить: python analysis/common.py — убедиться что всё зелёное

ФАЗА 2 — Основной анализ (Этапы 1 + 1.1):
  6. Создать analysis/01_sweep_accuracy.py:
     - Sweep x0 от -1.5 до +1.5 (N=301)
     - 3-точечные: ref_qa, ref_ea по 3 отсчётам
     - 2-точечные: select_top2 → ref_cg_2pt, ref_sd(c=1.0)
     - Детектор монотонности → экстраполяция E1/E2/E3 для монотонных
     - Сохранить results/sweep_accuracy.csv и results/extrapolation.csv
  7. Запустить: python analysis/01_sweep_accuracy.py

ФАЗА 3 — Статистика + графики (Этапы 2-3):
  8. Создать analysis/02_statistics.py — метрики по зонам (из CSV Этапа 1)
  9. Создать analysis/03_plots_2d.py — 6 типов 2D-графиков
  10. Запустить оба, проверить plots/2d/

ФАЗА 4 — Расширенный анализ (Этапы 4-5, если время есть):
  11. analysis/04_grid_step.py — серия step = 0.3, 0.5, 1.0, 1.5, 2.0
  12. analysis/05_plots_3d.py — surface + heatmap

ФАЗА 5 — Monte Carlo + FFT (Этапы 6-7, если время есть):
  13. analysis/06_noise_montecarlo.py — M=10000, rng seed=42
  14. analysis/07_fft_analysis.py — использовать METHODS из test_fft_frequency.py, НЕ common.py!

ФАЗА 6 — Отчёт (Этап 8):
  15. analysis/08_report.py — собрать всё в Markdown

📐 ШАБЛОН СКРИПТА — в спеке секция "Шаблон analysis-скрипта". Копируй оттуда.

🧪 КАЖДЫЙ СКРИПТ после создания — ЗАПУСТИТЬ и убедиться что работает:
   cd discriminator_estimates/test_python
   python analysis/0X_название.py

📊 ПОСЛЕ КАЖДОЙ ФАЗЫ — показать Alex результат (таблицы, графики, ошибки).
```

---

*Последнее обновление: 2026-04-02*
*Ревью: Кодо (старшая AI) — 6 критических + 8 важных фиксов внесены*
