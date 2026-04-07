===============
C API Reference
===============

.. rubric:: Справочник публичного C API модуля discriminator_estimates

Все заголовки из :file:`include/` используют ``extern "C"`` и совместимы
с C11/C17 и C++11/17. После рефакторинга 2026 года интерфейсы не
менялись — расширения идут через новые файлы (``discr5ea.h``,
``discr_auto.h``).

.. contents:: На этой странице
   :local:
   :depth: 2

----

Обзор заголовков
================

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Заголовок
     - Статус
     - Назначение
   * - :file:`discrcg.h`
     - Оригинал
     - Центр тяжести (2/3/N-точечный)
   * - :file:`discrsd.h`
     - Оригинал
     - Суммарно-разностный (2pt)
   * - :file:`discrqa.h`
     - Оригинал
     - Парабола по 3 точкам
   * - :file:`discrea.h`
     - Оригинал
     - Гауссиан по 3 точкам (EA)
   * - :file:`discr5ea.h`
     - **Новый 2026**
     - МНК по 5 точкам (5QA + 5EA) ★
   * - :file:`discr_auto.h`
     - **Новый 2026**
     - Авто-выбор метода + экстраполяция
   * - :file:`discr_common.h`
     - Оригинал
     - Обёртки ``discr2``, ``discr3_``
   * - :file:`discr_types.h`
     - Оригинал
     - ``DISCRTYPE`` enum

----

1. discrcg.h — Центр тяжести
=============================

.. c:function:: double discr2cg(double A1, double A2, double x1, double x2)

   Двухточечный дискриминатор, центр тяжести.

   Формула: :math:`x_e = \dfrac{A_1 x_1 + A_2 x_2}{A_1 + A_2}`.

   :param A1: амплитуда первой точки
   :param A2: амплитуда второй точки
   :param x1: координата первой точки
   :param x2: координата второй точки
   :return: оценка координаты. При :math:`A_1 + A_2 = 0` возвращает
            :math:`(x_1 + x_2)/2`.

.. c:function:: double discr3cg(double A1, double A2, double A3, double x1, double x2, double x3)

   Трёхточечный дискриминатор, центр тяжести.

   Формула:
   :math:`x_e = \dfrac{A_1 x_1 + A_2 x_2 + A_3 x_3}{A_1 + A_2 + A_3}`.

   :return: оценка координаты. При сумме = 0 возвращает :math:`x_2`.

.. c:function:: double discrncg(const double *A, const double *x, unsigned int N)

   N-точечный дискриминатор, центр тяжести.

   :param A: массив амплитуд (N элементов)
   :param x: массив координат (N элементов)
   :param N: число точек
   :return: оценка координаты. При ``sum(A) = 0`` возвращает ``x[N/2]``.

**Пример**:

.. code-block:: c

   #include "discrcg.h"

   double A[3] = {0.5, 2.0, 1.5};
   double x[3] = {-1.0, 0.0, 1.0};
   double xe = discrncg(A, x, 3);
   // xe ≈ 0.25

----

2. discrsd.h — Суммарно-разностный
===================================

.. c:function:: double discr2sd(double c, double A1, double A2, double x1, double x2)

   Двухточечный суммарно-разностный дискриминатор.

   Формула:
   :math:`x_e = \dfrac{x_1 + x_2}{2} + c \cdot \dfrac{A_2 - A_1}{A_2 + A_1}`.

   :param c: коэффициент крутизны дискриминаторной характеристики
   :param A1: амплитуда первой точки
   :param A2: амплитуда второй точки
   :param x1: координата первой точки
   :param x2: координата второй точки
   :return: оценка координаты. При :math:`A_1 + A_2 = 0` возвращает
            :math:`(x_1 + x_2)/2`.

**Пример**:

.. code-block:: c

   #include "discrsd.h"

   double c = 0.132497;  // подобрано для конкретной ДН
   double xe = discr2sd(c, 0.8, 1.2, -0.5, 0.5);

----

3. discrqa.h — Парабола по 3 точкам
====================================

.. c:function:: double discr3qa(double A1, double A2, double A3, double x1, double x2, double x3)

   Трёхточечный дискриминатор, парабола по 3 точкам.

   Через 3 точки проводится парабола :math:`y = ax^2 + bx + c`,
   находится её вершина.

   Вспомогательная формула: :math:`A_o = \dfrac{A_2 - A_1}{A_2 - A_3}`.

   **Граничные случаи** обрабатываются через ``DBL_EPSILON``
   (см. :doc:`formulas`).

   :return: оценка координаты :math:`x_e`.

**Пример**:

.. code-block:: c

   #include "discrqa.h"

   double A1 = 0.75, A2 = 2.75, A3 = 2.75;
   double x1 = -1.0, x2 = 0.0,  x3 = 1.0;
   double xe = discr3qa(A1, A2, A3, x1, x2, x3);
   // xe ≈ 0.5 — оценка положения пика между точками

----

4. discrea.h — Гауссиан по 3 точкам (EA)
=========================================

.. c:function:: int discr3ea(double A1, double A2, double A3, double x1, double x2, double x3, double *xe)

   Трёхточечный дискриминатор, экспоненциальная (гауссова) аппроксимация.

   Аппроксимирует отсчёты ДН функцией
   :math:`y = A_{\max} \exp(-a(x-x_0)^2)`:

   1. Логарифмирует амплитуды: :math:`z_i = \ln A_i`.
   2. Аппроксимирует параболой :math:`z(x) = \alpha + \beta x + \gamma x^2`.
   3. Находит вершину :math:`x_e = \alpha / (2\beta)`.

   :param A1-A3: амплитуды (**должны быть > 0**)
   :param x1-x3: координаты
   :param xe: [out] оценка координаты
   :return: ``EXIT_SUCCESS`` (0) при успехе, ``EXIT_FAILURE`` (1) при ошибке.

.. c:function:: double discr3eaY(double A1, double A2, double x1, double x2, double xe)

   Уточнение амплитуды по найденной координате :math:`x_e`.

   :return: уточнённое значение амплитуды :math:`y_e` в точке :math:`x_e`.
            При :math:`A_1 < \varepsilon` или :math:`A_2 < \varepsilon`
            возвращает 0.0.

**Пример**:

.. code-block:: c

   #include "discrea.h"
   #include <stdlib.h>

   double A1 = 0.25, A2 = 1.0, A3 = 0.25;
   double xe;
   int ok = discr3ea(A1, A2, A3, -1.0, 0.0, 1.0, &xe);
   if (ok == EXIT_SUCCESS) {
     double ye = discr3eaY(A2, A3, 0.0, 1.0, xe);
   }

----

5. discr5ea.h — МНК по 5 точкам ★
==================================

.. c:function:: int discr5ea(const double A[5], const double x[5], double *xe)

   **Рекомендуемый по умолчанию.** Пятиточечный МНК-гауссиан.

   Аппроксимирует 5 равноотстоящих отсчётов гауссианом методом
   наименьших квадратов. Логарифмирует амплитуды и применяет замкнутую
   МНК-формулу по параболе в log-пространстве.

   :param A: массив из 5 амплитуд (**все > 0**), центр = ``A[2]``
   :param x: массив из 5 координат, **равноотстоящих**
   :param xe: [out] оценка координаты :math:`x_e`
   :return: ``EXIT_SUCCESS`` (0) при успехе, ``EXIT_FAILURE`` (1) при ошибке.

.. c:function:: int discr5qa(const double A[5], const double x[5], double *xe)

   Пятиточечный МНК-параболический дискриминатор.

   Аналогичен ``discr5ea``, но работает **напрямую с амплитудами**
   (без логарифмирования). Используется как fallback, когда
   :math:`A_i \leq 0`.

   :param A: массив из 5 амплитуд (**могут быть любые**)
   :param x: массив из 5 координат, равноотстоящих
   :param xe: [out] оценка координаты
   :return: ``EXIT_SUCCESS`` / ``EXIT_FAILURE``.

**Пример** — правильное использование с fallback:

.. code-block:: c

   #include "discr5ea.h"
   #include <complex.h>
   #include <stdlib.h>

   double y[5], xs[5];
   for (int i = 0; i < 5; ++i) {
     y[i]  = cabs(X[k_max - 2 + i]);
     xs[i] = (double)(i - 2);
   }

   double delta;
   int ok = discr5ea(y, xs, &delta);
   if (ok != EXIT_SUCCESS) {
     discr5qa(y, xs, &delta);      // fallback
   }

   double f_hz = (k_max + delta) * fs / (double)N_padded;

----

6. discr_auto.h — Автовыбор метода
===================================

.. c:function:: int discr_is_monotonic(double A1, double A2, double A3)

   Проверка монотонности трёх отсчётов.

   :return: 1 — монотонные (пик за сеткой), 0 — есть перегиб (пик внутри).

.. c:function:: int discr3_extrap_gauss(double A1, double A2, double A3, double x1, double x2, double x3, double *xe)

   Гауссова экстраполяция (E2) для монотонных случаев.

   Алгоритм как ``discr3ea``, но без проверки выпуклости и с
   расширенным диапазоном допустимого вылета (2× вместо 0.5×).

   :return: 0 — успех, 1 — ошибка.

.. c:function:: int discr3_auto(double A1, double A2, double A3, double x1, double x2, double x3, double *xe)

   Автоматический дискриминатор с переключением.

   Алгоритм выбора:

   .. code-block:: text

      if is_monotonic(A1, A2, A3):
          xe = extrap_gauss(...)        // E2
      else:
          ret = discr3ea(...)           // EA (лучший)
          if ret == FAILURE:
              xe = discr3qa(...)        // QA fallback

   :return:
      * **0** — EA успех
      * **1** — использован QA fallback
      * **2** — использована экстраполяция E2
      * **3** — экстраполяция E2 не сошлась (``xe = x2``)

**Пример**:

.. code-block:: c

   #include "discr_auto.h"

   double xe;
   int how = discr3_auto(A1, A2, A3, x1, x2, x3, &xe);
   switch (how) {
     case 0: printf("EA normal\n"); break;
     case 1: printf("QA fallback\n"); break;
     case 2: printf("E2 extrapolation\n"); break;
     case 3: printf("E2 failed, xe=x2\n"); break;
   }

----

7. discr_common.h — Обёртки discr2 / discr3
============================================

Высокоуровневые обёртки для удобного вызова 2pt / 3pt дискриминаторов
по 2D-массивам (для РЛС-моноимпульсного канала).

Используют ``DISCRTYPE`` enum из :file:`discr_types.h`:

.. code-block:: c

   typedef enum {
     DT_CG = 0,   // центр тяжести
     DT_SD = 1,   // сумма-разность
     DT_QA = 2,   // парабола
     DT_EA = 3,   // гауссиан
   } DISCRTYPE;

.. admonition:: ERR-003 fix
   :class: important

   После рефакторинга обёртки **не модифицируют** входные массивы —
   координаты умножаются на коэффициент :math:`c = 2\pi dx / \lambda`
   при передаче в дискриминатор.

----

8. Константы и возвращаемые значения
=====================================

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Константа
     - Значение
     - Смысл
   * - ``EXIT_SUCCESS``
     - 0
     - Функция отработала штатно
   * - ``EXIT_FAILURE``
     - 1
     - Ошибка в данных (отрицательные A, вогнутость)

----

Python API (будущее)
====================

.. note::

   Python-биндинги в разработке. Планируется два подхода:

   * **ctypes** — быстрый старт, загрузка ``.so``/``.dll`` напрямую
   * **pybind11** — когда C++ обёртка стабилизируется

   Прототип реализован в :file:`test_python/test_discriminators.py`,
   см. :doc:`tests`.

----

Связанные документы
===================

- :doc:`formulas` — полные математические формулы
- :doc:`methods` — сравнение методов с графиками
- :doc:`recommendations` — рекомендации по выбору
- :doc:`tests` — тестовое покрытие
