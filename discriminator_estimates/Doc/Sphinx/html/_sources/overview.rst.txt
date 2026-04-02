Обзор
=====

Назначение
----------

Сравнение точности пяти частотных дискриминаторов FFT-спектра:

* **EXP** -- парабола на log|S| (discr3ea.c, Добродумов 2012)
* **SQR** -- парабола на |S| (discr3qa.c, Федоров 2010)
* **LAY** -- Jacobsen: комплексное деление (fcalcdelay.m)
* **SD** -- суммарно-разностный 2-точечный (discrsd.c, Федоров 2010)
* **CG** -- центр тяжести 2-точечный (discrcg.c, Федоров 2010)

Параметры тестового сигнала
---------------------------

.. math::

   x(t) = A \cdot \exp(j \cdot 2\pi \cdot f_{sin} \cdot t) + \text{noise}

============ =================== ================================
Параметр     Значение            Описание
============ =================== ================================
N            32                  Число отсчётов
fd           12 МГц              Частота дискретизации
df = fd/N    375 кГц             Ширина бина FFT
fsin         [-df/2, +df/2]      Sweep (±187.5 кГц)
an           1e-9                СКО шума
============ =================== ================================

Формулы дискриминаторов
-----------------------

**EXP** (discr3ea):

.. math::

   z_i = \ln A_i, \quad
   \alpha = z_1(f_2^2-f_3^2) + z_2(f_3^2-f_1^2) + z_3(f_1^2-f_2^2)

.. math::

   \beta = z_1(f_2-f_3) + z_2(f_3-f_1) + z_3(f_1-f_2), \quad
   x_e = \frac{\alpha}{2\beta}

**SQR** (discr3qa):

.. math::

   A_o = \frac{A_2 - A_1}{A_2 - A_3}, \quad
   x_e = \frac{(A_o-1)x_2^2 - A_o x_3^2 + x_1^2}{2\bigl((A_o-1)x_2 - A_o x_3 + x_1\bigr)}

**LAY** (Jacobsen):

.. math::

   \sigma = \frac{S_{k+1} - S_{k-1}}{2 S_k - S_{k-1} - S_{k+1}}, \quad
   f_{est} = f_k - \operatorname{Re}\{\sigma\} \cdot \frac{f_d}{N}

**SD** (discrsd):

.. math::

   x_e = \frac{x_1+x_2}{2} + c \cdot \frac{A_2 - A_1}{A_2 + A_1}, \quad c = 0.132497

**CG** (discrcg):

.. math::

   x_e = \frac{A_1 x_1 + A_2 x_2}{A_1 + A_2}

Графики
-------

**Дискриминационная характеристика (Primer.m):**

.. image:: ../plots/fft_primer_m.png
   :width: 100%
   :alt: FFT-дискриминаторы: sweep 65 точек

**Ошибка метода EXP + сравнение окон:**

.. image:: ../plots/fft_exp_error_windows.png
   :width: 100%
   :alt: Ошибка EXP и влияние окна

**Оценки на sinc(x):**

.. image:: ../plots/sinc_discriminator_estimates.png
   :width: 100%
   :alt: sinc(x) с оценками CG/QA/EA

**Ошибка vs. смещение пика:**

.. image:: ../plots/error_vs_shift.png
   :width: 100%
   :alt: Ошибка дискриминаторов при разных смещениях

**Ошибка vs. шаг сетки:**

.. image:: ../plots/error_vs_grid_step.png
   :width: 100%
   :alt: Ошибка vs. шаг сетки
