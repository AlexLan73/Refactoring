# Тестирование {#tests_page}

## 4 вида тестов — 77+ тестов

Все тесты используют экспериментальные данные, моделирующие ДН антенны:

\f[
\text{sinc}(x - x_0) = \frac{\sin(x - x_0)}{x - x_0}
\f]

где \f$ x_0 \f$ — истинное смещение пика (цели) относительно центра сетки.

---

## 1. Простые C++ тесты (`test_cpp/`) — 27 тестов

**Фреймворк**: без фреймворка, assert + std::cout
**Запуск**: `./build/test_discr`

Быстрые тесты для разработчиков C/C++. Не требуют внешних зависимостей.

### Структура

| Файл | Тестов | Что проверяет |
|------|--------|---------------|
| `test_discr_cg.hpp` | 7 | CG: 2/3/N-точечный, деление на 0 |
| `test_discr_sd.hpp` | 3 | SD: базовый, смещение, деление на 0 |
| `test_discr_qa.hpp` | 5 | QA: парабола, граничные A1=A2, A2=A3 |
| `test_discr_ea.hpp` | 6 | EA: гауссиан, вогнутость, нулевые ампл. |
| `test_discr_common.hpp` | 6 | Обёртки: discr2, discr3_, conv3to2 |

### Паттерн теста

```cpp
extern "C" {
#include "discrcg.h"
}
#include <cassert>

void test_symmetric() {
  double r = discr3cg(1.0, 3.0, 1.0, -1.0, 0.0, 1.0);
  assert(fabs(r - 0.0) < 1e-12);
  std::cout << "[PASS] discr3cg: symmetric -> center\n";
}
```

### Результат

```
=== CG Tests ===
[PASS] discr2cg: equal amplitudes -> midpoint
[PASS] discr2cg: dominant A2 -> near x2
[PASS] discr2cg: zero amplitudes -> midpoint (ERR-005)
...
========================================
ALL DISCRIMINATOR TESTS COMPLETE (27/27)
========================================
```

---

## 2. Google Test (`test_gtest/`) — 40 тестов

**Фреймворк**: Google Test v1.15.2 (CMake FetchContent)
**Запуск**: `./build/test_discr_gtest` или `ctest --test-dir build`

Полные тесты с подробной диагностикой. Используют **sinc(x)** данные — реалистичные
отсчёты ДН антенны с разными смещениями пика.

### Структура

| Файл | Тестов | Данные |
|------|--------|--------|
| `test_discr_cg_gtest.cpp` | 11 | sinc(x), sinc(x-0.3), 5 точек |
| `test_discr_sd_gtest.cpp` | 5 | sinc(x), sinc(x-0.2) |
| `test_discr_qa_gtest.cpp` | 8 | sinc(x-0.2), sinc(x-0.4) мелкая сетка |
| `test_discr_ea_gtest.cpp` | 9 | гауссиан, sinc(x-0.2), вогнутость |
| `test_discr_common_gtest.cpp` | 7 | sinc(x)*sinc(y) 3x3, ERR-003 побочные эффекты |

### Ключевые тесты

**Проверка точности на sinc(x-0.2):**
```cpp
TEST(Discr3QA, SincData_Peak_at_02) {
  double x0 = 0.2;
  double A1 = sinc(-1.0 - x0);
  double A2 = sinc(0.0 - x0);
  double A3 = sinc(1.0 - x0);
  double r = discr3qa(A1, A2, A3, -1.0, 0.0, 1.0);
  EXPECT_NEAR(r, x0, 0.15);  // QA: ±0.1 шага
}
```

**Проверка ERR-003 (нет побочных эффектов):**
```cpp
TEST(Discr3, QA_NoSideEffect_ERR003) {
  double maz_before = maz[0][0];
  discr3_(maz, mel, mval, DT_QA, 0.1, 0.03, &az, &el, &val);
  EXPECT_DOUBLE_EQ(maz[0][0], maz_before);  // входные данные НЕ изменены
}
```

---

## 3. Python тесты (`test_python/`) — 7 тестов + 3 графика

**Фреймворк**: PyCore (TestRunner + DataValidator)
**Запуск**: `python test_python/test_discriminators.py`
**Графики**: `python test_python/test_discriminators_plot.py`

Тесты с визуализацией и сравнением с эталонами NumPy/SciPy.

### Эталонные реализации

```python
# CG — numpy weighted average:
def ref_cg(A, x):
    return np.average(x, weights=A)

# QA — вершина параболы через polyfit:
def ref_qa(A, x):
    coeffs = np.polyfit(x, A, 2)
    return -coeffs[1] / (2.0 * coeffs[0])
```

### Результат сравнения точности

| Метод | Средняя ошибка | Точность |
|-------|---------------|----------|
| CG | 0.172 | ±0.3 шага |
| QA | 0.007 | ±0.1 шага |

**QA в 25 раз точнее CG!**

### Графики

@image html sinc_discriminator_estimates.png "sinc(x) + отсчёты + оценки CG/QA/EA"

График показывает:
- Голубая линия — sinc(x - 0.25) (ДН антенны, пик смещён на 0.25)
- Жёлтые точки — 3 отсчёта на сетке {-1, 0, +1}
- Вертикальные линии — оценки дискриминаторов
- Зелёная пунктирная — истинное положение пика

@image html error_vs_shift.png "Ошибка оценки vs смещение пика"

График показывает зависимость абсолютной ошибки от смещения пика:
- CG (красный) и SD (фиолетовый) — линейный рост ошибки
- QA (бирюзовый) — ошибка < 0.02 при любом смещении
- EA (жёлтый) — самая маленькая ошибка

@image html error_vs_grid_step.png "Ошибка vs шаг сетки"

Влияние шага сетки на точность:
- При мелкой сетке (< 0.5) все методы точны
- При крупной сетке (> 1.5) EA значительно лучше остальных

---

## Сборка и запуск

### Простые C++ тесты
```bash
g++ -std=c++17 -Iinclude test_cpp/test_main.cpp -Lbuild -ldiscr -lm -o test_discr
./test_discr
```

### Google Test
```bash
cd build
cmake .. -G Ninja
cmake --build .
./test_discr_gtest
ctest  # или так
```

### Python
```bash
python test_python/test_discriminators.py       # sinc(x) тесты
python test_python/test_discriminators_plot.py   # sinc(x) графики → Doc/plots/
python test_python/test_fft_frequency.py         # FFT тесты (10 проверок)
python test_python/test_fft_frequency_plot.py    # FFT графики → Doc/plots/
```

---

## 4. FFT-дискриминаторы частоты (`test_python/`) — 10 тестов + 2 графика

**Фреймворк**: PyCore (TestRunner)
**Запуск**: `python test_python/test_fft_frequency.py`

Тестирование дискриминаторов в задаче оценки частоты по FFT-спектру
(воспроизведение MatLab Primer.m + fcalcdelay.m).

### Тестовые группы

| Класс | Тестов | Что проверяет |
|-------|--------|---------------|
| `TestFFTBasic` | 4 | Симметрия (fsin=0), смещённый пик, все 5 методов |
| `TestFFTSweep` | 4 | Монотонность ДХ, макс. ошибка < 10 кГц, знак оценки |
| `TestFFTCompare` | 2 | EXP лучше SQR лучше LAY; таблица точности |

### Результат

```
[PASS]  TestFFTBasic.test_exp_at_center
[PASS]  TestFFTBasic.test_exp_shifted: f_est=98575, err=4825 Hz
[PASS]  TestFFTSweep.test_exp_monotonic (17 pts)
[PASS]  TestFFTCompare.test_exp_best: EXP(2902) < SQR(13553) < LAY(22933)
Total: 10 passed, 0 failed, 0 skipped
```

### Графики FFT

@image html fft_primer_m.png "Дискриминационная характеристика FFT (Primer.m)"

@image html fft_exp_error_windows.png "Ошибка метода EXP: все методы + сравнение окон"
