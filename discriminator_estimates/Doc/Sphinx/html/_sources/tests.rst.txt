==========
Тесты
==========

.. rubric:: 4 вида тестов — 77+ проверок

Все тесты используют экспериментальные данные, моделирующие ДН антенны:

.. math::
   :label: eq:test_sinc

   \text{sinc}(x - x_0) = \frac{\sin(x - x_0)}{x - x_0}

где :math:`x_0` — истинное смещение пика (цели) относительно центра сетки.

----

1. Простые C++ тесты (``test_cpp/``) — 27 тестов
=================================================

:Фреймворк: без фреймворка, ``assert`` + ``std::cout``
:Запуск: ``./build/test_discr``

Быстрые тесты для разработчиков C/C++. Не требуют внешних зависимостей.

Структура
---------

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Файл
     - Тестов
     - Что проверяет
   * - ``test_discr_cg.hpp``
     - 7
     - CG: 2/3/N-точечный, деление на 0
   * - ``test_discr_sd.hpp``
     - 3
     - SD: базовый, смещение, деление на 0
   * - ``test_discr_qa.hpp``
     - 5
     - QA: парабола, граничные :math:`A_1 = A_2`, :math:`A_2 = A_3`
   * - ``test_discr_ea.hpp``
     - 6
     - EA: гауссиан, вогнутость, нулевые амплитуды
   * - ``test_discr_common.hpp``
     - 6
     - Обёртки: ``discr2``, ``discr3_``, ``conv3to2``

Паттерн теста
-------------

.. code-block:: cpp

   extern "C" {
   #include "discrcg.h"
   }
   #include <cassert>

   void test_symmetric() {
     double r = discr3cg(1.0, 3.0, 1.0, -1.0, 0.0, 1.0);
     assert(fabs(r - 0.0) < 1e-12);
     std::cout << "[PASS] discr3cg: symmetric -> center\n";
   }

Результат
---------

.. code-block:: text

   === CG Tests ===
   [PASS] discr2cg: equal amplitudes -> midpoint
   [PASS] discr2cg: dominant A2 -> near x2
   [PASS] discr2cg: zero amplitudes -> midpoint (ERR-005)
   ...
   ========================================
   ALL DISCRIMINATOR TESTS COMPLETE (27/27)
   ========================================

----

2. Google Test (``test_gtest/``) — 40 тестов
=============================================

:Фреймворк: Google Test v1.15.2 (CMake FetchContent)
:Запуск: ``./build/test_discr_gtest`` или ``ctest --test-dir build``

Полные тесты с подробной диагностикой. Используют ``sinc(x)`` данные —
реалистичные отсчёты ДН антенны с разными смещениями пика.

Структура
---------

.. list-table::
   :header-rows: 1
   :widths: 40 15 45

   * - Файл
     - Тестов
     - Данные
   * - ``test_discr_cg_gtest.cpp``
     - 11
     - ``sinc(x)``, ``sinc(x-0.3)``, 5 точек
   * - ``test_discr_sd_gtest.cpp``
     - 5
     - ``sinc(x)``, ``sinc(x-0.2)``
   * - ``test_discr_qa_gtest.cpp``
     - 8
     - ``sinc(x-0.2)``, ``sinc(x-0.4)`` мелкая сетка
   * - ``test_discr_ea_gtest.cpp``
     - 9
     - Гауссиан, ``sinc(x-0.2)``, вогнутость
   * - ``test_discr_common_gtest.cpp``
     - 7
     - ``sinc(x)*sinc(y)`` 3x3, ERR-003 побочные эффекты

Ключевые тесты
--------------

Проверка точности на ``sinc(x-0.2)``:

.. code-block:: cpp

   TEST(Discr3QA, SincData_Peak_at_02) {
     double x0 = 0.2;
     double A1 = sinc(-1.0 - x0);
     double A2 = sinc(0.0 - x0);
     double A3 = sinc(1.0 - x0);
     double r = discr3qa(A1, A2, A3, -1.0, 0.0, 1.0);
     EXPECT_NEAR(r, x0, 0.15);  // QA: ±0.1 шага
   }

Проверка ERR-003 (нет побочных эффектов):

.. code-block:: cpp

   TEST(Discr3, QA_NoSideEffect_ERR003) {
     double maz_before = maz[0][0];
     discr3_(maz, mel, mval, DT_QA, 0.1, 0.03, &az, &el, &val);
     EXPECT_DOUBLE_EQ(maz[0][0], maz_before);  // входные данные НЕ изменены
   }

----

3. Python тесты (``test_python/``) — 7 тестов + 3 графика
==========================================================

:Фреймворк: PyCore (``TestRunner`` + ``DataValidator``)
:Запуск: ``python test_python/test_discriminators.py``
:Графики: ``python test_python/test_discriminators_plot.py``

.. warning::

   В этом проекте pytest **запрещён**. Запуск тестов только через
   прямой вызов ``python test_file.py`` + ``PyCore.runner.TestRunner``.

Тесты с визуализацией и сравнением с эталонами NumPy/SciPy.

Эталонные реализации
--------------------

.. code-block:: python

   # CG — numpy weighted average:
   def ref_cg(A, x):
       return np.average(x, weights=A)

   # QA — вершина параболы через polyfit:
   def ref_qa(A, x):
       coeffs = np.polyfit(x, A, 2)
       return -coeffs[1] / (2.0 * coeffs[0])

Результат сравнения точности
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Метод
     - Средняя ошибка
     - Точность
   * - CG
     - 0.172
     - ±0.3 шага
   * - QA
     - 0.007
     - ±0.1 шага

**QA в 25 раз точнее CG!**

Графики
-------

.. figure:: ../plots/2_no_noise/sinc_discriminator_estimates.png
   :alt: sinc(x) + отсчёты + оценки
   :align: center
   :width: 100%

   ``sinc(x)`` + отсчёты + оценки CG / QA / EA.

.. figure:: ../plots/2_no_noise/error_vs_shift.png
   :alt: Ошибка vs смещение пика
   :align: center
   :width: 100%

   Ошибка оценки vs смещение пика.

.. figure:: ../plots/2_no_noise/error_vs_grid_step.png
   :alt: Ошибка vs шаг сетки
   :align: center
   :width: 100%

   Ошибка vs шаг сетки.

----

4. FFT-дискриминаторы (``test_python/``) — 10 тестов + 2 графика
=================================================================

:Фреймворк: PyCore (``TestRunner``)
:Запуск: ``python test_python/test_fft_frequency.py``

Тестирование дискриминаторов в задаче оценки частоты по FFT-спектру
(воспроизведение MatLab ``Primer.m`` + ``fcalcdelay.m``).

Тестовые группы
---------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Класс
     - Тестов
     - Что проверяет
   * - ``TestFFTBasic``
     - 4
     - Симметрия (:math:`f_{\text{sin}} = 0`), смещённый пик, все 5 методов
   * - ``TestFFTSweep``
     - 4
     - Монотонность ДХ, макс. ошибка < 10 кГц, знак оценки
   * - ``TestFFTCompare``
     - 2
     - EXP лучше SQR лучше LAY; таблица точности

Результат
---------

.. code-block:: text

   [PASS]  TestFFTBasic.test_exp_at_center
   [PASS]  TestFFTBasic.test_exp_shifted: f_est=98575, err=4825 Hz
   [PASS]  TestFFTSweep.test_exp_monotonic (17 pts)
   [PASS]  TestFFTCompare.test_exp_best: EXP(2902) < SQR(13553) < LAY(22933)
   Total: 10 passed, 0 failed, 0 skipped

----

Сборка и запуск
===============

Простые C++ тесты
-----------------

.. code-block:: bash

   g++ -std=c++17 -Iinclude test_cpp/test_main.cpp \
       -Lbuild -ldiscr -lm -o test_discr
   ./test_discr

Google Test
-----------

.. code-block:: bash

   cd build
   cmake .. -G Ninja
   cmake --build .
   ./test_discr_gtest
   ctest  # альтернативно

Python
------

.. code-block:: bash

   python test_python/test_discriminators.py       # sinc(x) тесты
   python test_python/test_discriminators_plot.py  # графики → Doc/plots/
   python test_python/test_fft_frequency.py        # FFT тесты
   python test_python/test_fft_frequency_plot.py   # FFT графики

----

Дальше
======

- :doc:`api` — справочник C API
- :doc:`methods` — сравнение методов
- :doc:`recommendations` — итоговые рекомендации
