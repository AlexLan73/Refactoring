# FFT-дискриминаторы частоты {#fft_page}

## Оценка частоты по FFT-спектру (из Primer.m)

Дискриминаторы модуля применяются не только для оценки угловых координат
по ДН антенны, но и для **точной оценки частоты** по FFT-спектру
комплексного сигнала.

### Сигнал

\f[
x(t) = A \cdot \exp(j \cdot 2\pi \cdot f_{sin} \cdot t) + \text{noise}
\f]

| Параметр | Значение | Описание |
|----------|----------|----------|
| N | 32 | Число отсчётов |
| fd | 12 МГц | Частота дискретизации |
| df = fd/N | 375 кГц | Ширина бина FFT |
| fsin | [-df/2, +df/2] | Sweep (±187.5 кГц) |
| Окно | Hamming | -43 дБ боковые лепестки |

---

## 5 методов оценки частоты

### 3-точечные (бины k-1, k, k+1)

**EXP** (discr3ea.c — парабола на log|S|):
\f[
z_i = \ln|S_i|, \quad
\alpha = z_1(f_2^2-f_3^2) + z_2(f_3^2-f_1^2) + z_3(f_1^2-f_2^2)
\f]
\f[
\beta = z_1(f_2-f_3) + z_2(f_3-f_1) + z_3(f_1-f_2), \quad
f_{est} = \frac{\alpha}{2\beta}
\f]

**SQR** (discr3qa.c — парабола на |S|):
\f[
A_o = \frac{A_2 - A_1}{A_2 - A_3}, \quad
f_{est} = \frac{(A_o-1)f_2^2 - A_o f_3^2 + f_1^2}{2\bigl((A_o-1)f_2 - A_o f_3 + f_1\bigr)}
\f]

**LAY** (Jacobsen, fcalcdelay.m):
\f[
\sigma = \frac{S_{k+1} - S_{k-1}}{2 S_k - S_{k-1} - S_{k+1}}, \quad
f_{est} = f_k - \operatorname{Re}\{\sigma\} \cdot \frac{f_d}{N}
\f]

### 2-точечные (top-2 bins по амплитуде)

**SD** (discrsd.c):
\f[
f_{est} = \frac{f_1+f_2}{2} + c \cdot \frac{P_2 - P_1}{P_2 + P_1}, \quad c = 0.132497
\f]

**CG** (discrcg.c):
\f[
f_{est} = \frac{A_1 f_1 + A_2 f_2}{A_1 + A_2}
\f]

---

## Дискриминационная характеристика

@image html fft_primer_m.png "Рис. 5: Дискриминационная характеристика 5 FFT-методов (sweep ±df/2)"

Верхний ряд: спектры FFT при fsin = -df/2, 0, +df/2.
Средний ряд: оценки частоты vs. истинная частота (65 точек sweep).
Нижний ряд: ошибка оценки.

---

## Сравнение точности

Sweep ±df/4, N=32, окно Hamming, без шума:

| Метод | Средняя ошибка | Макс. ошибка | Рекомендация |
|-------|---------------|-------------|-------------|
| **EXP** | 2 902 Гц | 4 825 Гц | **Лучший для Hamming** |
| SQR | 13 553 Гц | 23 348 Гц | Хороший |
| LAY | 22 933 Гц | 43 811 Гц | Biased (Jacobsen для Hamming) |
| CG | 84 664 Гц | 115 270 Гц | Грубая оценка |
| SD | 138 393 Гц | 187 500 Гц | Очень грубая (c=0.132497) |

---

## Влияние оконной функции

@image html fft_exp_error_windows.png "Рис. 6: Ошибка метода EXP для разных оконных функций"

Левый график: сравнение всех 5 методов (Hamming).
Правый график: метод EXP с окнами Hamming / Hann / Blackman.

**Blackman** даёт наименьшую ошибку для метода EXP — его форма
спектрального пика ближе всего к гауссиане.

---

## Запуск тестов

```bash
# Тесты (10 проверок):
python test_python/test_fft_frequency.py

# Графики -> Doc/plots/fft_*.png:
python test_python/test_fft_frequency_plot.py
```

## Происхождение

```
C-исходники (2010-2012)        MatLab               Python
discr3ea.c (Добродумов) ──▶ discr='exp' ──▶ fft_discr_exp()
discr3qa.c (Федоров)    ──▶ discr='sqr' ──▶ fft_discr_sqr()
discrsd.c  (Федоров)    ──▶ discr='sd'  ──▶ fft_discr_sd()
discrcg.c  (Федоров)    ──▶ discr='cg'  ──▶ fft_discr_cg()
fcalcdelay.m            ──▶ discr='lay' ──▶ fft_discr_lay()
```
