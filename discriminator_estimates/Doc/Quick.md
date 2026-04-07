# discriminator_estimates -- Быстрый старт

Модуль дискриминаторных оценок координат для уточнения положения максимума диаграммы направленности (ДН) по 2-3 отсчётам.

---

## 1. Зависимости

| Компонент | Минимальная версия |
|-----------|--------------------|
| CMake | 3.15+ |
| C-компилятор | C17 (C11 достаточно) |
| C++-компилятор | C++17 (для тестов) |
| Google Test | v1.15.2 (скачивается автоматически через FetchContent) |

Внешних зависимостей у самой библиотеки нет -- только стандартная библиотека C (`math.h`, `float.h`, `stdlib.h`).

---

## 2. Сборка

### Linux / macOS

```bash
cd discriminator_estimates
mkdir build && cd build
cmake ..
cmake --build .
```

### Windows (MSVC)

```bash
cd discriminator_estimates
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
```

### Windows (MinGW / Ninja)

```bash
cd discriminator_estimates
mkdir build && cd build
cmake .. -G Ninja
cmake --build .
```

### Результат сборки

| Артефакт | Описание |
|----------|----------|
| `libdiscr.a` / `discr.lib` | Статическая библиотека (для C/C++ проектов) |
| `libdiscr.so` / `discr.dll` | Shared библиотека (для Python ctypes) |
| `test_discr` | Простые C++ тесты |
| `test_discr_gtest` | Google Test тесты |

### Запуск тестов

```bash
cd build
ctest --output-on-failure
# или напрямую:
./test_discr
./test_discr_gtest
```

---

## 3. Минимальный пример на C

Квадратичная аппроксимация (`discr3qa`) -- наиболее распространённый метод.

```c
/* example_qa.c */
#include <stdio.h>
#include "discrqa.h"

int main(void)
{
    /*
     * Три отсчёта ДН (sinc-подобная функция со смещением 0.3):
     *   x = -1.0, 0.0, 1.0
     *   A = sinc(-1.3), sinc(-0.3), sinc(0.7)
     */
    double A1 = 0.858, A2 = 1.0, A3 = 0.947;
    double x1 = -1.0,  x2 = 0.0, x3 = 1.0;

    double xe = discr3qa(A1, A2, A3, x1, x2, x3);

    printf("Оценка координаты максимума: %.4f\n", xe);
    /* Ожидаемый результат: ~0.30 (истинное смещение) */

    return 0;
}
```

**Компиляция и запуск:**

```bash
gcc -I include/ -o example_qa example_qa.c src/discrqa.c -lm
./example_qa
```

### Пример с обёрткой discr3_ (матрица 3x3)

```c
/* example_3x3.c */
#include <stdio.h>
#include "discr_common.h"

int main(void)
{
    /* Координатная сетка 3x3 (азимут, угол места) */
    double maz[3][3]  = {{ -1, 0, 1 }, { -1, 0, 1 }, { -1, 0, 1 }};
    double mel[3][3]  = {{ -1, -1, -1 }, { 0, 0, 0 }, { 1, 1, 1 }};
    double mval[3][3] = {
        { 0.5, 0.7, 0.5 },
        { 0.7, 1.0, 0.7 },
        { 0.5, 0.7, 0.5 }
    };

    double az, el, val;
    double dx = 0.01;       /* шаг по углу, рад */
    double lambda = 0.03;   /* длина волны, м */

    int rc = discr3_(maz, mel, mval, DT_QA, dx, lambda, &az, &el, &val);

    if (rc == 0) {
        printf("Азимут: %.4f, Угол места: %.4f, Амплитуда: %.4f\n",
               az, el, val);
    } else {
        printf("Ошибка дискриминатора: %d\n", rc);
    }

    return 0;
}
```

---

## 4. Минимальный пример на Python (ctypes)

```python
"""example_discr.py -- вызов библиотеки через ctypes."""
import ctypes
import os

# Путь к shared-библиотеке
if os.name == "nt":
    lib = ctypes.CDLL("./build/Release/discr.dll")
else:
    lib = ctypes.CDLL("./build/libdiscr_shared.so")

# --- discr3qa ---
lib.discr3qa.restype = ctypes.c_double
lib.discr3qa.argtypes = [
    ctypes.c_double, ctypes.c_double, ctypes.c_double,  # A1, A2, A3
    ctypes.c_double, ctypes.c_double, ctypes.c_double,  # x1, x2, x3
]

# Три отсчёта ДН (смещение 0.3)
A1, A2, A3 = 0.858, 1.0, 0.947
x1, x2, x3 = -1.0, 0.0, 1.0

xe = lib.discr3qa(A1, A2, A3, x1, x2, x3)
print(f"discr3qa -> xe = {xe:.4f}")  # ~0.30


# --- discr3ea ---
lib.discr3ea.restype = ctypes.c_int
lib.discr3ea.argtypes = [
    ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.POINTER(ctypes.c_double),  # xe (out)
]

xe_out = ctypes.c_double(0.0)
rc = lib.discr3ea(A1, A2, A3, x1, x2, x3, ctypes.byref(xe_out))
print(f"discr3ea -> rc={rc}, xe = {xe_out.value:.4f}")


# --- discr2cg ---
lib.discr2cg.restype = ctypes.c_double
lib.discr2cg.argtypes = [
    ctypes.c_double, ctypes.c_double,
    ctypes.c_double, ctypes.c_double,
]

xe = lib.discr2cg(0.8, 1.0, -1.0, 1.0)
print(f"discr2cg -> xe = {xe:.4f}")
```

**Запуск:**

```bash
# Сначала собрать shared-библиотеку
cd discriminator_estimates && mkdir -p build && cd build
cmake .. && cmake --build .

# Затем запустить пример
cd ..
python example_discr.py
```

---

## 5. Какой метод выбрать?

| Метод | Функция | Точек | Когда использовать |
|-------|---------|-------|--------------------|
| CG (центр тяжести) | `discr2cg` / `discr3cg` | 2-3 | Быстрая грубая оценка |
| SD (суммарно-разностный) | `discr2sd` | 2 | При известном коэффициенте `c` |
| QA (квадратичная) | `discr3qa` | 3 | Основной метод, хорошая точность |
| EA (экспоненциальная) | `discr3ea` | 3 | Наивысшая точность для гауссовых ДН |
| AUTO | `discr3_auto` | 3 | Автоматически EA/QA/экстраполяция |
| 5EA (МНК-гауссов) | `discr5ea` | 5 | Устойчивость к шуму + широкое окно |
| 5QA (МНК-парабола) | `discr5qa` | 5 | Как 5EA, но без логарифмирования |

**Монотонный режим:** если пик вне окна из 3 точек (67% реальных случаев!) -- используй `discr3_auto` или 5-точечные методы.

```c
#include "discr_auto.h"

double xe;
// Автоматически: EA в норме, E2 экстраполяция при монотонных данных
int mode = discr3_auto(A1, A2, A3, x1, x2, x3, &xe);
```

---

## 6. Дальнейшее чтение

- **[API.md](API.md)** -- полный справочник всех 17 функций с формулами и граничными случаями
- **[Full.md](Full.md)** -- подробная документация (архитектура, математика, МНК 5/7/9, монотонный режим)
- **test_cpp/** -- C++ тесты (примеры вызовов всех функций)
- **test_python/** -- Python тесты с визуализацией
- **[Doc/plots/README.md](plots/README.md)** -- описание всех графиков (42 файла + 5 GIF)

---

*Обновлено: 2026-04-06 | Модуль: discriminator_estimates v1.1*
