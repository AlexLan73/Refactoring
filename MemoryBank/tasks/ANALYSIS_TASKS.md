# TASKS: Аналитическое исследование точности дискриминаторов

**Спецификация**: `MemoryBank/specs/discriminator_analysis_plan.md`
**Статус**: BACKLOG
**Приоритет**: P0 первыми, потом P1, P2, P3

---

## TASK-0: common.py + валидация C ↔ Python

**Приоритет**: P0 (prerequisite — делать ПЕРВЫМ)
**Файл**: `discriminator_estimates/test_python/analysis/common.py`
**Зависимости**: нет

### Что сделать

1. **Создать `analysis/__init__.py`** (пустой, для импорта)

2. **Создать `analysis/common.py`** со следующим содержимым:

   **Функция `sinc(x)`**:
   ```python
   def sinc(x):
       """sinc(x) = sin(x)/x, sinc(0) = 1. НЕ numpy.sinc!"""
   ```
   - Принимает scalar и np.ndarray
   - НЕ использовать `np.sinc` (он нормализованный: sin(πx)/(πx))
   - Обработка x=0: вернуть 1.0

   **Эталонные реализации** (из C-исходников, порт 1:1):
   ```python
   def ref_cg(A1, A2, x1, x2):        # из discrcg.c — 2-точечный
   def ref_cg3(A1, A2, A3, x1, x2, x3):  # из discrcg.c — 3-точечный
   def ref_sd(c, A1, A2, x1, x2):     # из discrsd.c
   def ref_qa(A1, A2, A3, x1, x2, x3): # из discr3qa.c — формула Ao!
   def ref_ea(A1, A2, A3, x1, x2, x3): # из discr3ea.c — с проверками!
   ```
   - Формулы ТОЧНО из C-кода (см. `src/discrcg.c`, `src/discrsd.c`, `src/discrqa.c`, `src/discrea.c`)
   - `ref_qa`: формула `Ao = (A2-A1)/(A2-A3)`, НЕ `np.polyfit`
   - `ref_ea`: с сортировкой по x, проверкой выпуклости, ограничением вылета — ВСЁ как в C
   - `ref_sd`: принимает коэффициент `c` первым аргументом

   **Детектор монотонности**:
   ```python
   def is_monotonic(A1, A2, A3):
       """True если нет локального максимума (все возрастают или убывают)."""
       return (A1 >= A2 >= A3) or (A1 <= A2 <= A3)
   ```

   **Методы экстраполяции** (для Этапа 1.1):
   ```python
   def extrap_parabolic(A1, A2, A3, x1, x2, x3, max_extrap=2.0):
       """E1: парабола через 3 точки, вершина, clip по max_extrap*step."""
   def extrap_gaussian(A1, A2, A3, x1, x2, x3):
       """E2: Гауссиан fit через scipy.optimize.curve_fit, try/except."""
   def extrap_gradient(A1, A2, A3, x1, x2, x3):
       """E3: линейная регрессия -> направление + 0.5*step."""
   ```

   **Загрузка C-библиотеки** (опционально, для валидации):
   ```python
   def load_discr_lib():
       """Загрузить libdiscr.so / discr.dll через ctypes."""
       # Искать в build/, build/Release/, ...
       # При отсутствии: raise SkipTest(...)
   ```

   **Константы**:
   ```python
   GRID_DEFAULT = np.array([-1.0, 0.0, 1.0])  # стандартная сетка
   SD_COEFF_DEFAULT = 1.0       # базовый коэффициент SD
   SD_COEFF_FFT = 0.132497      # из fcalcdelay.m
   ```

3. **Обновить `test_discriminators.py` и `test_discriminators_plot.py`**:
   - Заменить локальные `sinc`, `ref_cg`, `ref_qa` на `from analysis.common import ...`
   - Убедиться что все существующие тесты проходят

4. **Валидация C ↔ Python** (если C-библиотека собрана):
   - Для каждой функции (cg, sd, qa, ea): вызвать C через ctypes и Python ref_*
   - Сравнить: `assert abs(c_result - py_result) < 1e-12`
   - Тестовые данные: sinc(x) с x0 = 0, 0.1, 0.2, 0.3, 0.4
   - Если библиотека не собрана — SkipTest, НЕ падать

### Критерии приёмки
- [ ] `common.py` импортируется без ошибок
- [ ] `sinc(0) == 1.0`, `sinc(np.array([0, 1, -1]))` работает
- [ ] `ref_qa` даёт тот же результат что `discr3qa` в C (если lib доступна)
- [ ] `ref_ea` обрабатывает граничные случаи (нулевые ампл., все равные, вогнутость)
- [ ] `is_monotonic` корректно: `is_monotonic(3,2,1) == True`, `is_monotonic(1,3,2) == False`
- [ ] `test_discriminators.py` по-прежнему проходит после рефакторинга
- [ ] `python test_python/test_discriminators.py` — все PASS

---

## TASK-1: Sweep пика по сетке

**Приоритет**: P0
**Файл**: `analysis/01_sweep_accuracy.py`
**Зависимости**: TASK-0 (common.py)

### Что сделать

1. **Основной sweep**:
   - `x0 = np.linspace(-1.5, 1.5, 301)` — 301 точка
   - Для каждого x0:
     - `A1, A2, A3 = sinc(-1-x0), sinc(0-x0), sinc(1-x0)` — 3 отсчёта
     - `xe_qa = ref_qa(A1, A2, A3, -1, 0, 1)`
     - `xe_ea = ref_ea(A1, A2, A3, -1, 0, 1)` — обработать return code!
     - Для CG и SD: **выбрать 2 из 3** с максимальными амплитудами (как `conv3to2`)
     - `mono = is_monotonic(A1, A2, A3)` — флаг монотонности
   - Записать в pandas DataFrame или numpy structured array

2. **Экстраполяция монотонных случаев** (Этап 1.1):
   - Если `is_monotonic == True`:
     - `xe_e1 = extrap_parabolic(A1, A2, A3, -1, 0, 1)`
     - `xe_e2 = extrap_gaussian(A1, A2, A3, -1, 0, 1)` — try/except!
     - `xe_e3 = extrap_gradient(A1, A2, A3, -1, 0, 1)`
   - Иначе: `xe_e1 = xe_e2 = xe_e3 = NaN`

3. **Sweep SD с разными c**:
   - Отдельный цикл: `c_values = [0.5, 1.0, 1.5, 2.0]`
   - Для каждого c — полный sweep → отдельная колонка `xe_sd_c05`, `xe_sd_c10`, ...

4. **Сохранить результаты**:
   - CSV: `results/sweep_accuracy.csv`
   - Колонки: `x0, A1, A2, A3, xe_cg, xe_sd, xe_qa, xe_ea, xe_e1, xe_e2, xe_e3, err_cg, err_sd, err_qa, err_ea, is_monotonic, zone`
   - `zone`: "normal" / "boundary" / "extreme" по диапазону x0

5. **Консольный вывод при запуске**:
   ```
   Sweep: 301 points, x0 = [-1.50, +1.50]
   Monotonic cases: 87/301 (28.9%)
   E2 convergence failures: 12/87 (13.8%)
   Saved: results/sweep_accuracy.csv
   ```

### Критерии приёмки
- [ ] CSV файл создаётся, 301 строка, все колонки заполнены
- [ ] При x0=0: все методы дают xe ≈ 0 (err < 0.001)
- [ ] При x0=0.2: EA ошибка < QA < CG (проверка порядка точности)
- [ ] Монотонные случаи корректно детектируются (x0 < -1.0 и x0 > 1.0)
- [ ] Экстраполяция E1 не падает при монотонных данных
- [ ] Экстраполяция E2 корректно обрабатывает несходимость (NaN, не exception)
- [ ] `python analysis/01_sweep_accuracy.py` — без ошибок

---

## TASK-2: Матстатистика

**Приоритет**: P0
**Файл**: `analysis/02_statistics.py`
**Зависимости**: TASK-1 (sweep_accuracy.csv)

### Что сделать

1. **Загрузить** `results/sweep_accuracy.csv`

2. **Вычислить метрики** для каждого метода (CG, SD, QA, EA) в каждой зоне:

   | Метрика | Формула |
   |---------|---------|
   | MAE | `np.mean(np.abs(err))` |
   | MaxErr | `np.max(np.abs(err))` |
   | RMSE | `np.sqrt(np.mean(err**2))` |
   | Bias | `np.mean(err)` — со знаком! |
   | Std | `np.std(err)` |
   | P95 | `np.percentile(np.abs(err), 95)` |

3. **Зоны**:
   - `all`: все 301 точка
   - `normal`: `|x0| <= 0.5`
   - `boundary`: `0.5 < |x0| <= 1.0`
   - `extreme`: `|x0| > 1.0`
   - `monotonic`: только `is_monotonic == True`

4. **Таблица экстраполяции** (отдельная):
   - Только монотонные случаи
   - Сравнить E1, E2, E3: MAE, MaxErr, % несходимости E2

5. **Проверка гипотез**:
   - H1: `MAE_ea < MAE_qa < MAE_cg` в normal зоне → print("H1: CONFIRMED/REJECTED")
   - H3: `Bias_cg` ~ линейный → вычислить корреляцию bias vs x0 → print("H3: corr = ...")
   - H4: `MAE_sd(c=0.5)` vs `MAE_sd(c=1.0)` vs ... → print("H4: best c = ...")

6. **Сохранить**:
   - CSV: `results/statistics_by_zone.csv`
   - Markdown: `results/statistics_summary.md` (красивая таблица)

7. **Консольный вывод**:
   ```
   === Statistics by Zone ===
   Zone: normal (|x0| <= 0.5), N=101
   Method |   MAE    | MaxErr  |  RMSE   |  Bias   |  Std    |  P95
   -------|----------|---------|---------|---------|---------|--------
   CG     | 0.17213  | 0.30142 | 0.19012 | 0.00021 | 0.19012 | 0.28456
   ...

   === Hypothesis Testing ===
   H1: EA best in normal zone? CONFIRMED (EA=0.003 < QA=0.007 < CG=0.172)
   H3: CG bias linear? corr(bias, x0) = 0.998 → CONFIRMED
   ```

### Критерии приёмки
- [ ] Таблица для 5 зон x 4 метода x 6 метрик
- [ ] H1 проверена и выведен результат
- [ ] H3: корреляция bias_cg vs x0 вычислена
- [ ] CSV и Markdown сохранены
- [ ] `python analysis/02_statistics.py` — без ошибок

---

## TASK-3: 2D графики

**Приоритет**: P0
**Файл**: `analysis/03_plots_2d.py`
**Зависимости**: TASK-1 (sweep_accuracy.csv)

### Что сделать

6 графиков, каждый сохраняется в `plots/2d/`:

1. **`abs_error_vs_x0.png`** — Абсолютная ошибка |xe - x0| vs x0
   - 4 кривые: CG (красный), SD (фиолетовый), QA (бирюзовый), EA (жёлтый)
   - Y-ось: логарифмическая (`plt.yscale('log')`)
   - Вертикальные пунктиры: границы зон (x0 = -1, -0.5, +0.5, +1)
   - Подписи зон: "extreme", "boundary", "normal", "boundary", "extreme"
   - Тема: `plt.style.use('dark_background')`

2. **`signed_error_vs_x0.png`** — Знаковая ошибка (xe - x0) vs x0
   - Показывает bias: положительный = оценка завышена
   - Горизонтальная линия y=0 (идеал)
   - Цвета как в п.1

3. **`ratio_xe_x0.png`** — Отношение xe/x0 vs x0
   - Идеал = горизонтальная линия y=1.0
   - Исключить x0=0 (деление на 0)
   - Показывает нелинейность каждого метода

4. **`sinc_animation_frames.png`** — Серия из 9 кадров (3x3 subplot)
   - x0 = [-1.0, -0.75, -0.5, -0.25, 0, 0.25, 0.5, 0.75, 1.0]
   - Каждый кадр: sinc(x-x0) + 3 отсчёта + вертикальные линии оценок
   - Как `sinc_discriminator_estimates.png`, но 9 положений пика

5. **`boxplot_by_zone.png`** — Box-plot ошибок по зонам
   - X: зоны (normal, boundary, extreme)
   - Y: |error|
   - 4 бокса в каждой зоне (по методу), разные цвета
   - Показывает медиану, квартили, выбросы

6. **`error_histogram.png`** — Гистограмма распределения ошибок
   - 4 подграфика (один на метод) или 4 overlay
   - X: error (signed), Y: count
   - bins = 50
   - Показывает форму распределения и bias

### Стиль графиков
- Тема: `dark_background`
- Цвета: CG=#FF6B6B, SD=#C792EA, QA=#4ECDC4, EA=#FFE66D
- DPI: 150
- figsize: (14, 7) для одиночных, (14, 14) для мультиплотов
- Сетка: `ax.grid(True, alpha=0.3)`
- Подписи осей: русский язык, размер 12

### Критерии приёмки
- [ ] 6 PNG файлов в `plots/2d/`
- [ ] Все графики читаемы, легенда не перекрывает данные
- [ ] Логарифмическая шкала на графике 1 корректна (нет log(0))
- [ ] Серия кадров (п.4) показывает движение пика
- [ ] `python analysis/03_plots_2d.py` — без ошибок

---

## TASK-4: Влияние шага сетки

**Приоритет**: P1
**Файл**: `analysis/04_grid_step.py`
**Зависимости**: TASK-0 (common.py)

### Что сделать

1. **Сетки**: `step_values = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]`
2. Для каждого step:
   - Сетка: `x_grid = [-step, 0, step]`
   - Sweep: `x0 = np.linspace(-step, step, 101)` (пик внутри сетки)
   - Вычислить ошибку всех 4 методов
3. **Сохранить**: `results/grid_step_sweep.csv`
4. **График**: `plots/2d/error_vs_grid_step_sweep.png`
   - Линии: mean_error(step) для каждого метода
   - X: step, Y: mean |error|

### Критерии приёмки
- [ ] CSV с результатами для 6 шагов
- [ ] График показывает как ошибка растёт с шагом
- [ ] EA стабильно лучше QA при всех шагах (проверка H1)

---

## TASK-5: 3D графики

**Приоритет**: P1
**Файл**: `analysis/05_plots_3d.py`
**Зависимости**: TASK-4 (grid_step_sweep.csv)

### Что сделать

1. **Surface plot**: `plots/3d/surface_error_{method}.png`
   - X: x0, Y: step, Z: |error|
   - Один график на метод (4 файла) + один overlay
   - `from mpl_toolkits.mplot3d import Axes3D`
   - Colormap: `viridis`

2. **Heatmap**: `plots/3d/heatmap_error_{method}.png`
   - X: x0, Y: step, Color: log10(|error|)
   - `plt.pcolormesh` или `plt.imshow`
   - Colorbar с подписью

3. **Contour**: `plots/3d/contour_error_{method}.png`
   - Линии уровня: error = [0.001, 0.01, 0.05, 0.1, 0.2, 0.5]
   - Подписи на линиях

4. **Сводный 2x2**: `plots/3d/surface_all_methods.png`
   - 4 подграфика: CG, SD, QA, EA — одинаковая шкала цвета

### Критерии приёмки
- [ ] 4+4+4+1 = 13 PNG файлов в `plots/3d/`
- [ ] Surface plot корректно рендерится (нет артефактов)
- [ ] Heatmap показывает "зону комфорта" каждого метода
- [ ] Contour показывает границы точности

---

## TASK-6: Monte Carlo с шумом

**Приоритет**: P2
**Файл**: `analysis/06_noise_montecarlo.py`
**Зависимости**: TASK-0 (common.py)

### Что сделать

1. **Параметры**:
   ```python
   rng = np.random.default_rng(seed=42)  # воспроизводимость!
   snr_levels = [0.001, 0.01, 0.05, 0.1, 0.2]  # sigma/A_max
   x0_values = [0.0, 0.1, 0.2, 0.3, 0.4]
   M = 1000  # M_fast для отладки; потом M=10000 для финала
   ```

2. Для каждого (snr, x0):
   - Базовые амплитуды: `A = sinc(GRID - x0)`
   - M реализаций: `A_noisy = A + rng.normal(0, snr * max(A), size=(M, 3))`
   - Для каждой реализации: вычислить xe всеми методами
   - Собрать mean_error, std_error, p95_error

3. **Проверка H2**: QA более устойчив к шуму, чем EA?
   - При высоком шуме (snr=0.2): `std_qa < std_ea`?

4. **Сохранить**: `results/noise_montecarlo.csv`
5. **Графики**:
   - `plots/2d/noise_error_vs_snr.png` — mean_error vs SNR (4 кривые)
   - `plots/2d/noise_std_vs_snr.png` — std vs SNR

### Критерии приёмки
- [ ] M=1000 реализаций за < 30 секунд
- [ ] `rng seed=42` → результаты воспроизводимы
- [ ] H2 проверена: вывод в консоль
- [ ] CSV + 2 графика сохранены

---

## TASK-7: FFT-применение

**Приоритет**: P2
**Файл**: `analysis/07_fft_analysis.py`
**Зависимости**: TASK-0, `test_fft_frequency.py` (FFT-реализации)

### Что сделать

1. **Импортировать** FFT-дискриминаторы из `test_fft_frequency.py`:
   ```python
   from test_fft_frequency import METHODS, create_signal, compute_fft, make_freq_axis
   ```

2. **Sweep** для N_fft = [16, 32, 64, 128, 256]:
   - fsin sweep: ±df/4 (41 точка)
   - 5 методов: exp, sqr, lay, sd, cg
   - Вычислить MAE, MaxErr для каждого (N, method)

3. **Окна**: Hamming, Blackman, Kaiser(8), Kaiser(14)
   - Для N=32, метод EXP: sweep с каждым окном

4. **Сохранить**: `results/fft_analysis.csv`
5. **Графики**:
   - `plots/2d/fft_error_vs_nfft.png` — MAE vs N_fft (5 кривых)
   - `plots/2d/fft_error_vs_window.png` — MAE по окнам (EXP метод)

### Критерии приёмки
- [ ] Таблица [N x method x metric]
- [ ] EXP лучше остальных при всех N
- [ ] Blackman лучше Hamming для EXP (подтверждение)
- [ ] CSV + 2 графика

---

## TASK-8: Итоговый отчёт

**Приоритет**: P3
**Файл**: `analysis/08_report.py`
**Зависимости**: ВСЕ предыдущие

### Что сделать

1. **Генерировать** `results/REPORT.md` со всеми таблицами и ссылками на графики
2. **Структура отчёта**:
   - Введение + постановка задачи
   - Таблица 1: точность по зонам (из TASK-2)
   - Таблица 2: влияние шага (из TASK-4)
   - Таблица 3: экстраполяция (из TASK-1.1)
   - Таблица 4: шум (из TASK-6)
   - Таблица 5: FFT (из TASK-7)
   - Проверка гипотез H1-H5 (CONFIRMED/REJECTED + числа)
   - Рекомендации
   - Список всех графиков с подписями

### Критерии приёмки
- [ ] `REPORT.md` создан, > 200 строк
- [ ] Все 5 гипотез проверены с числовыми доказательствами
- [ ] Все графики упомянуты и подписаны
- [ ] Рекомендация "какой метод когда" сформулирована

---

## Порядок выполнения

```
TASK-0 (common.py)
   │
   ├──▶ TASK-1 (sweep) ──▶ TASK-2 (статистика) ──▶ TASK-3 (2D графики)
   │         │
   │         └──▶ TASK-4 (шаг сетки) ──▶ TASK-5 (3D графики)
   │
   ├──▶ TASK-6 (шум Monte Carlo)
   │
   └──▶ TASK-7 (FFT)
                          │
                          ▼
                    TASK-8 (отчёт) ← собирает всё
```

---

## Общие правила для исполнителя

1. **НЕ использовать pytest** — только прямой вызов `python file.py`
2. **sinc(x) = sin(x)/x** — НЕ `np.sinc` (он нормализованный!)
3. **Формулы из C-исходников** — `discr3qa.c`, `discr3ea.c`, `discrsd.c`, `discrcg.c`
4. **Воспроизводимость**: `np.random.default_rng(seed=42)` для Monte Carlo
5. **Графики**: `dark_background`, DPI=150, русские подписи
6. **Пути**: относительные! Никаких `/home/alex/...`
7. **CSV**: с заголовками, разделитель `,`, кодировка UTF-8
8. **Каждый файл** — самодостаточный: `python analysis/0X_....py` должен работать
9. **Консольный вывод**: прогресс + ключевые числа + путь к сохранённым файлам
10. **Ошибки**: не падать, а писать "[WARN] ..." и продолжать (особенно E2 несходимость)
