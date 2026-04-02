# TASKS: Интерактивная анимация дискриминаторов

**Спецификация**: `Animation/PLAN.md`
**Статус**: READY
**Каталог**: `discriminator_estimates/test_python/analysis/Animation/`

---

## TASK-A0: Каталоги и __init__.py

**Приоритет**: P0 (делать первым)
**Файлы**: `Animation/__init__.py`, `Animation/output/`
**Зависимости**: нет

### Что сделать

1. Создать `Animation/__init__.py` (пустой)
2. Создать `Animation/output/` (пустой каталог, через mkdir)
3. Проверить что `Animation/PLAN.md` на месте

### Критерии приёмки
- [ ] `Animation/__init__.py` существует
- [ ] `Animation/output/` существует
- [ ] `ls Animation/` показывает: `PLAN.md  __init__.py  output/`

---

## TASK-A1: anim_core.py — RingBuffer

**Приоритет**: P0
**Файл**: `Animation/anim_core.py`
**Зависимости**: TASK-A0

### Что сделать

1. Создать `anim_core.py` с шаблоном импортов (из PLAN.md секция 3):
   ```python
   ANIM_DIR     = Path(__file__).resolve().parent
   ANALYSIS_DIR = ANIM_DIR.parent
   MODULE_DIR   = ANALYSIS_DIR.parent.parent
   REPO_ROOT    = MODULE_DIR.parent
   sys.path.insert(0, str(REPO_ROOT))
   sys.path.insert(0, str(ANALYSIS_DIR))
   ```

2. Реализовать `RingBuffer`:
   - `__init__(self, size=200)` — `np.full(size, np.nan)`
   - `push(self, value)` — записать по `idx % size`, увеличить idx
   - `get_ordered(self)` — `np.roll(data, -(idx % n))`

3. Self-test (TestRunner):
   - `test_push_and_get` — 5 push'ей, проверить порядок
   - `test_overflow` — 210 push'ей в буфер size=200, NaN исчезли
   - `test_empty` — get_ordered на пустом = все NaN

### Критерии приёмки
- [ ] `python3 Animation/anim_core.py` — RingBuffer тесты PASS
- [ ] NaN в начале, данные в хронологическом порядке

---

## TASK-A2: anim_core.py — AnimScene.setup()

**Приоритет**: P0
**Файл**: `Animation/anim_core.py` (дополнение)
**Зависимости**: TASK-A1

### Что сделать

1. Константы в начале файла:
   ```python
   FPS = 15
   INTERVAL_MS = 1000 // FPS  # 66 ms
   METHODS = ['CG', 'QA', 'EA', 'AUTO']
   ZONE_COLORS = {
       'normal': ('#00FF00', 0.04),
       'boundary': ('#FFFF00', 0.04),
       'extreme': ('#FF0000', 0.06),
   }
   ```

2. `AnimScene.__init__(self)` — только self.fig = None

3. `AnimScene.setup(self, figsize=(14, 8), mode='export')`:
   - `plt.style.use("dark_background")` ПЕРЕД `plt.figure()`
   - `self.fig = plt.figure(figsize=figsize)`
   - GridSpec по mode:
     - `'export'`: 75% main + 25% bar
     - `'interactive'`: 60% main + 15% bar + 25% пусто (для слайдеров)
     - `'scope'`: 25% main + 4×15% scope + 15% info
   - `self.x_fine = np.linspace(-4, 4, 500)`
   - `self.rng = np.random.default_rng(seed=42)`

4. Создание artists на ax_main:
   - `self.line_sinc = ax_main.plot(x_fine, sinc(x_fine), color='#00BFFF', lw=2)[0]`
   - `self.scatter_pts = ax_main.scatter([−1,0,1], sinc([−1,0,1]), c='#FFE66D', s=120, zorder=5)`
   - `self.vline_true = ax_main.axvline(0, color='lime', ls=':', lw=2, zorder=3)`
   - `self.vlines = {}` для CG, QA, EA, AUTO (каждый axvline, AUTO lw=3)
   - `self.zone_bg = ax_main.axvspan(xlim[0], xlim[1], alpha=0.04, color='green', zorder=0)`
   - `self.text_info = ax_main.text(0.02, 0.98, '', transform=..., va='top', ...)`
   - ax_main настройки: xlim=[-4,4], ylim=[-0.3,1.15], grid, labels

5. Создание artists на ax_bar (горизонтальный barh):
   - `self.bars = ax_bar.barh(METHODS, [0]*4, color=[COLORS[m] for m in METHODS])`
   - `self.bars_text = []` — 4 текста значений (обновляются в update)
   - ax_bar: xlim=[0, 1.0], xlabel='|error|'

6. Создание history (для scope):
   - `self.history = {m: RingBuffer(200) for m in METHODS}`

### Критерии приёмки
- [ ] `AnimScene().setup(mode='export')` — figure создаётся без ошибок
- [ ] `AnimScene().setup(mode='interactive')` — figure с местом для слайдеров
- [ ] Все artists созданы и видны (сохранить один кадр как PNG для проверки)
- [ ] `python3 Animation/anim_core.py` — тест setup PASS

---

## TASK-A3: anim_core.py — AnimScene.update()

**Приоритет**: P0
**Файл**: `Animation/anim_core.py` (дополнение)
**Зависимости**: TASK-A2

### Что сделать

1. `AnimScene.update(self, x0, snr=0.0, step=1.0)`:

   **Шаг 1**: Построить сетку и амплитуды
   ```python
   grid = np.array([-step, 0.0, step])
   A = sinc(grid - x0)
   if snr > 0:
       A = A + self.rng.normal(0, snr * np.max(np.abs(A)), 3)
   ```

   **Шаг 2**: Вычислить оценки
   ```python
   A1, A2, x1, x2 = select_top2(A, grid)
   xe_cg = ref_cg_2pt(A1, A2, x1, x2)
   xe_qa = ref_qa(A, grid)
   xe_ea = ref_ea(A, grid)
   xe_auto, auto_mode = ref_auto(A, grid)
   ```

   **Шаг 3**: Вычислить ошибки
   ```python
   errors = {
       'CG': abs(xe_cg - x0), 'QA': abs(xe_qa - x0),
       'EA': abs(xe_ea - x0), 'AUTO': abs(xe_auto - x0),
   }
   estimates = {'CG': xe_cg, 'QA': xe_qa, 'EA': xe_ea, 'AUTO': xe_auto}
   ```

   **Шаг 4**: Обновить line_sinc
   ```python
   x_fine_shifted = np.linspace(-step - step*1.5, step + step*1.5, 500)
   self.line_sinc.set_xdata(x_fine_shifted)
   self.line_sinc.set_ydata(sinc(x_fine_shifted - x0))
   ```

   **Шаг 5**: Обновить scatter (3 точки)
   ```python
   self.scatter_pts.set_offsets(np.column_stack([grid, A]))
   ```

   **Шаг 6**: Обновить vlines
   ```python
   self.vline_true.set_xdata([x0, x0])
   for m in METHODS:
       self.vlines[m].set_xdata([estimates[m], estimates[m]])
   ```

   **Шаг 7**: Обновить стиль AUTO вертикали (по mode)
   ```python
   mode_names = {0: 'EA', 1: 'QA', 2: 'E2', 3: 'FAIL'}
   if auto_mode == 2:
       self.vlines['AUTO'].set_linestyle('--')
       self.vlines['AUTO'].set_linewidth(3)
   else:
       self.vlines['AUTO'].set_linestyle('-')
       self.vlines['AUTO'].set_linewidth(2.5)
   ```

   **Шаг 8**: Обновить bars (barh)
   ```python
   max_err = max(max(errors.values()), 0.01)
   self.ax_bar.set_xlim(0, max_err * 1.3)
   for i, m in enumerate(METHODS):
       self.bars[i].set_width(errors[m])
       mode_suffix = f" ({mode_names[auto_mode]})" if m == 'AUTO' else ""
       self.bars_text[i].set_text(f" {errors[m]:.4f}{mode_suffix}")
       self.bars_text[i].set_x(errors[m] + max_err * 0.02)
   ```

   **Шаг 9**: Обновить zone_bg
   ```python
   zone = classify_zone(x0)
   self.zone_bg.remove()
   xlim = self.ax_main.get_xlim()
   self.zone_bg = self.ax_main.axvspan(
       xlim[0], xlim[1],
       alpha=ZONE_COLORS[zone][1],
       color=ZONE_COLORS[zone][0], zorder=0)
   ```

   **Шаг 10**: Обновить xlim (если step изменился)
   ```python
   margin = step * 1.5
   self.ax_main.set_xlim(-step - margin, step + margin)
   ```

   **Шаг 11**: Обновить text_info
   ```python
   info = (f"x0={x0:.2f} | Zone: {zone} | AUTO: {mode_names[auto_mode]}\n"
           f"CG={errors['CG']:.4f}  QA={errors['QA']:.4f}  "
           f"EA={errors['EA']:.4f}  AUTO={errors['AUTO']:.4f}")
   self.text_info.set_text(info)
   ```

   **Шаг 12**: Push в history
   ```python
   for m in METHODS:
       self.history[m].push(errors[m])
   ```

   **Шаг 13**: Return artists
   ```python
   return self.get_artists()
   ```

2. `AnimScene.get_artists(self)`:
   ```python
   return [self.line_sinc, self.scatter_pts, self.vline_true,
           *self.vlines.values(), self.text_info, self.zone_bg,
           *self.bars.patches, *self.bars_text]
   ```

3. Self-test:
   - `test_update_normal` — x0=0.2, snr=0, step=1 → errors dict корректен
   - `test_update_monotonic` — x0=1.3 → auto_mode=2 (E2)
   - `test_update_noise` — x0=0.2, snr=0.1 → errors > 0
   - `test_update_step` — x0=0.2, step=0.5 → xlim обновился
   - `test_render_frame` — сохранить один кадр в PNG, проверить размер файла > 0

### Критерии приёмки
- [ ] `scene.update(0.2, 0, 1.0)` — возвращает list of artists
- [ ] `scene.update(1.3, 0, 1.0)` — AUTO mode = 2 (E2)
- [ ] PNG одного кадра валидный (> 10KB)
- [ ] `python3 Animation/anim_core.py` — все тесты PASS

---

## TASK-A4: anim_export.py — S1 sweep_all.gif

**Приоритет**: P0 (первый видимый результат!)
**Файл**: `Animation/anim_export.py`
**Зависимости**: TASK-A3

### Что сделать

1. Создать `anim_export.py` со структурой из PLAN.md (секция 4):
   - `matplotlib.use("Agg")` (headless)
   - Шаблон импортов (Animation → analysis → Refactoring)
   - `sys.path.insert(0, str(ANIM_DIR))` для `from anim_core import AnimScene`
   - `OUT.mkdir(parents=True, exist_ok=True)`

2. Функция `export(name, x0_fn, snr_fn, step_fn, n_frames, fps, dpi)`:
   - `AnimScene().setup(figsize=(8, 6), mode='export')`
   - `init()` — вызывает `scene.update(x0_fn(0), ...)`, возвращает `get_artists()`
   - `update(frame)` — вызывает `scene.update(x0_fn(frame), ...)`
   - `FuncAnimation(fig, update, frames=n_frames, init_func=init, blit=True)`
   - `anim.save(path, writer='pillow', fps=fps, dpi=dpi)`
   - `plt.close(fig)`

3. Сценарий S1:
   ```python
   export("sweep_all",
          x0_fn  = lambda f: -1.5 + 3.0 * f / 74,
          snr_fn = lambda f: 0.0,
          step_fn= lambda f: 1.0,
          n_frames=75, fps=15)
   ```

4. TestRunner тест:
   - `test_sweep_all` — экспорт + проверка: GIF exists, n_frames >= 10 (PIL)

### Критерии приёмки
- [ ] `python3 Animation/anim_export.py` — без ошибок
- [ ] `output/sweep_all.gif` существует
- [ ] GIF валидный: >= 10 кадров, размер 800×600
- [ ] GIF визуально: sinc двигается, оценки следят, зоны раскрашены

---

## TASK-A5: anim_export.py — S2-S5 остальные сценарии

**Приоритет**: P0
**Файл**: `Animation/anim_export.py` (дополнение)
**Зависимости**: TASK-A4

### Что сделать

1. S2: `sweep_zoom_normal`
   ```python
   export("sweep_zoom_normal",
          x0_fn  = lambda f: -0.5 + 1.0 * f / 49,
          snr_fn = lambda f: 0.0,
          step_fn= lambda f: 1.0,
          n_frames=50)
   ```
   Перед export: нужно задать xlim=[-2, 2] (zoom). Либо добавить параметр `xlim_override` в setup/export.

2. S3: `noise_ramp`
   ```python
   export("noise_ramp",
          x0_fn  = lambda f: 0.2,
          snr_fn = lambda f: 0.25 * f / 74,
          step_fn= lambda f: 1.0,
          n_frames=75)
   ```
   ⚠️ Перед S3: сбросить `scene.rng = np.random.default_rng(seed=42)`

3. S4: `step_change`
   ```python
   export("step_change",
          x0_fn  = lambda f: 0.2,
          snr_fn = lambda f: 0.0,
          step_fn= lambda f: 0.3 + 2.2 * f / 59,
          n_frames=60)
   ```

4. S5: `auto_demo`
   ```python
   export("auto_demo",
          x0_fn  = lambda f: -1.5 + 3.0 * f / 74,
          snr_fn = lambda f: 0.0,
          step_fn= lambda f: 1.0,
          n_frames=75)
   ```
   Фишка: в update() для S5 — момент переключения EA↔E2 выделить текстом "→ EXTRAP E2".
   Можно реализовать как параметр AnimScene или отдельную логику в export.

5. TestRunner тесты:
   - `test_sweep_zoom` — GIF exists + frames
   - `test_noise_ramp` — GIF exists + frames
   - `test_step_change` — GIF exists + frames
   - `test_auto_demo` — GIF exists + frames

### Критерии приёмки
- [ ] 5 GIF-файлов в `output/`
- [ ] Каждый >= 10 кадров
- [ ] `noise_ramp.gif` — видно "дрожание" точек
- [ ] `step_change.gif` — сетка расширяется
- [ ] `auto_demo.gif` — видно переключение EA↔E2

---

## TASK-A6: anim_interactive.py — окно + слайдеры (Manual)

**Приоритет**: P0
**Файл**: `Animation/anim_interactive.py`
**Зависимости**: TASK-A3

### Что сделать

1. Создать `anim_interactive.py`:
   - `matplotlib.use("TkAgg")` (интерактивный бэкенд)
   - Шаблон импортов
   - `from matplotlib.widgets import Slider, Button`

2. `AnimScene().setup(figsize=(14, 9), mode='interactive')`

3. Создать 3 слайдера:
   ```python
   ax_sl_x0   = fig.add_axes([0.15, 0.18, 0.70, 0.02])
   ax_sl_snr  = fig.add_axes([0.15, 0.14, 0.70, 0.02])
   ax_sl_step = fig.add_axes([0.15, 0.10, 0.70, 0.02])

   slider_x0   = Slider(ax_sl_x0,   'x0',   -1.5, 1.5,  valinit=0.0,  valstep=0.01)
   slider_snr  = Slider(ax_sl_snr,  'SNR',   0.0,  0.30, valinit=0.0,  valstep=0.005)
   slider_step = Slider(ax_sl_step, 'Step',  0.2,  2.5,  valinit=1.0,  valstep=0.1)
   ```

4. Callback:
   ```python
   def on_slider_change(val):
       scene.update(slider_x0.val, slider_snr.val, slider_step.val)
       fig.canvas.draw_idle()

   slider_x0.on_changed(on_slider_change)
   slider_snr.on_changed(on_slider_change)
   slider_step.on_changed(on_slider_change)
   ```

5. Начальный update + `plt.show()`

### Критерии приёмки
- [ ] `python3 Animation/anim_interactive.py` — открывается окно
- [ ] Слайдер x0: двигается → sinc и оценки обновляются
- [ ] Слайдер SNR: точки "дрожат"
- [ ] Слайдер step: сетка расширяется/сужается
- [ ] Фон меняет цвет при смене зоны

---

## TASK-A7: anim_interactive.py — кнопки Play/Pause/Record/Reset

**Приоритет**: P0
**Файл**: `Animation/anim_interactive.py` (дополнение)
**Зависимости**: TASK-A6

### Что сделать

1. Создать 4 кнопки:
   ```python
   ax_btn_play  = fig.add_axes([0.15, 0.03, 0.12, 0.04])
   ax_btn_pause = fig.add_axes([0.30, 0.03, 0.12, 0.04])
   ax_btn_rec   = fig.add_axes([0.45, 0.03, 0.15, 0.04])
   ax_btn_reset = fig.add_axes([0.63, 0.03, 0.12, 0.04])

   btn_play  = Button(ax_btn_play,  '▶ Play')
   btn_pause = Button(ax_btn_pause, '⏸ Pause')
   btn_rec   = Button(ax_btn_rec,   '⏺ Rec GIF')
   btn_reset = Button(ax_btn_reset, '↺ Reset')
   ```

2. Play — `fig.canvas.new_timer(interval=INTERVAL_MS)`:
   ```python
   def play_step():
       nonlocal x0_play
       x0_play += 0.02
       if x0_play > 1.5:
           x0_play = -1.5
       slider_x0.set_val(x0_play)  # → вызовет on_slider_change

   def on_play(event):
       timer.start()

   def on_pause(event):
       timer.stop()
   ```

3. Record GIF:
   ```python
   def on_record(event):
       timer.stop()
       scene.rng = np.random.default_rng(seed=42)
       frames = []
       for x0 in np.linspace(-1.5, 1.5, 75):
           scene.update(x0, slider_snr.val, slider_step.val)
           fig.canvas.draw()
           buf = fig.canvas.buffer_rgba()
           img = Image.frombuffer('RGBA', fig.canvas.get_width_height(), buf)
           frames.append(img.convert('RGB'))
       path = OUT / "recorded.gif"
       frames[0].save(str(path), save_all=True,
                      append_images=frames[1:], duration=INTERVAL_MS, loop=0)
       print(f"Saved: {path}")
   ```

4. Reset:
   ```python
   def on_reset(event):
       timer.stop()
       slider_x0.set_val(0.0)
       slider_snr.set_val(0.0)
       slider_step.set_val(1.0)
   ```

### Критерии приёмки
- [ ] Play → x0 слайдер двигается автоматически
- [ ] Pause → останавливается
- [ ] Play → Pause → Play → возобновляется
- [ ] Rec GIF → `output/recorded.gif` создан и валиден
- [ ] Reset → все слайдеры на начальные значения
- [ ] Можно менять SNR/step ПОКА играет Play

---

## TASK-A8: anim_scope.py — осциллограф

**Приоритет**: P1
**Файл**: `Animation/anim_scope.py`
**Зависимости**: TASK-A3

### Что сделать

1. Создать `anim_scope.py`:
   - `matplotlib.use("TkAgg")`
   - `AnimScene().setup(figsize=(12, 8), mode='scope')`

2. Создать 4 scope-канала (отдельные Axes):
   ```python
   gs = fig.add_gridspec(nrows=8, ncols=1, hspace=0.15)
   ax_sinc = fig.add_subplot(gs[0:2, 0])
   ax_cg   = fig.add_subplot(gs[2, 0])
   ax_qa   = fig.add_subplot(gs[3, 0])
   ax_ea   = fig.add_subplot(gs[4, 0])
   ax_auto = fig.add_subplot(gs[5, 0])
   ```

3. Для каждого канала:
   - `line_scope_X = ax_X.plot(range(200), np.full(200, np.nan), color=COLORS[X])[0]`
   - `ax_X.set_ylim(0, ...)` — фиксированный (CG: 0..1, QA/EA/AUTO: 0..0.5)
   - `ax_X.set_ylabel(X, color=COLORS[X])`
   - Фоновые полосы по зонам (вертикальные)

4. FuncAnimation sweep:
   ```python
   x0_arr = np.linspace(-1.5, 1.5, 301)

   def update(frame):
       x0 = x0_arr[frame % len(x0_arr)]
       artists = scene.update(x0, 0, 1.0)
       # Обновить scope линии из history
       for m, ax_ch, line_ch in channels:
           line_ch.set_ydata(scene.history[m].get_ordered())
       return artists + scope_lines
   ```

5. Кнопка Play/Pause внизу

### Критерии приёмки
- [ ] `python3 Animation/anim_scope.py` — окно с 5 subplot'ами
- [ ] Верхний: sinc + оценки (компактно)
- [ ] 4 канала scope: линии бегут слева направо
- [ ] CG-линия "горбатая" (ошибка большая в extreme)
- [ ] EA/AUTO-линии почти плоские (маленькая ошибка)
- [ ] Каждый канал имеет свой масштаб Y

---

## TASK-A9: Верификация и финальные проверки

**Приоритет**: P1
**Зависимости**: TASK-A5, TASK-A7, TASK-A8

### Что сделать

1. Запустить скрипты верификации (из PLAN.md секция 11):
   ```bash
   # Проверить все 5 GIF
   python3 -c "
   from PIL import Image
   for name in ['sweep_all','sweep_zoom_normal','noise_ramp','step_change','auto_demo']:
       im = Image.open(f'Animation/output/{name}.gif')
       print(f'{name}: {im.n_frames} frames, {im.size}')
   "
   ```

2. Запустить интерактив — визуальная проверка:
   - `python3 Animation/anim_interactive.py`
   - Подвигать все 3 слайдера
   - Нажать Play → Pause → Rec GIF → Reset

3. Запустить scope:
   - `python3 Animation/anim_scope.py`
   - Дождаться полного цикла sweep

4. Проверить размеры GIF (< 15 МБ каждый)

### Критерии приёмки
- [ ] 5 GIF в output/, каждый < 15 МБ
- [ ] Интерактивное окно работает без crash
- [ ] Scope работает без crash
- [ ] Все цвета соответствуют COLORS из common.py

---

## Порядок выполнения (граф зависимостей)

```
TASK-A0 (__init__.py + output/)
    │
    ▼
TASK-A1 (RingBuffer)
    │
    ▼
TASK-A2 (AnimScene.setup)
    │
    ▼
TASK-A3 (AnimScene.update)
    │
    ├──────────────────┬────────────────┐
    ▼                  ▼                ▼
TASK-A4 (S1 GIF)   TASK-A6 (окно)   TASK-A8 (scope)
    │                  │
    ▼                  ▼
TASK-A5 (S2-S5)    TASK-A7 (кнопки)
    │                  │
    └──────────┬───────┘
               ▼
         TASK-A9 (верификация)
```

**Параллельно можно**: A4+A6+A8 (после A3).
**Последовательно**: A0→A1→A2→A3 (core), A4→A5 (export), A6→A7 (interactive).

---

## Оценка времени

| Таск | Время | Кумулятивно |
|------|-------|-------------|
| A0 | 1 мин | 1 мин |
| A1 | 10 мин | 11 мин |
| A2 | 20 мин | 31 мин |
| A3 | 25 мин | 56 мин |
| A4 | 10 мин | 1 ч 06 мин |
| A5 | 15 мин | 1 ч 21 мин |
| A6 | 20 мин | 1 ч 41 мин |
| A7 | 15 мин | 1 ч 56 мин |
| A8 | 20 мин | 2 ч 16 мин |
| A9 | 5 мин | **2 ч 21 мин** |

### Контрольные точки (можно остановиться)

```
  После A4  → sweep_all.gif работает (минимальный результат)
  После A5  → 5 GIF для документации
  После A7  → интерактивное окно "как Simulink Scope"
  После A9  → полный комплект + scope + верификация
```

---

*Таски готовы к исполнению.*
