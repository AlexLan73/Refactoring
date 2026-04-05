# Финальный план: Интерактивная анимация дискриминаторов

**Дата**: 2026-04-02
**Статус**: УТВЕРЖДЁН ✅
**Каталог**: `discriminator_estimates/test_python/analysis/Animation/`

---

## 1. Решения (зафиксированы)

| Вопрос | Решение | Почему |
|--------|---------|--------|
| Библиотека | **matplotlib** | Уже установлен, blit, виджеты, экспорт |
| Бэкенд (интерактив) | **TkAgg** | Работает на Debian, лёгкий |
| Бэкенд (экспорт) | **Agg** | Headless, без display |
| GIF writer | **PillowWriter** | Pillow уже есть, ffmpeg не нужен |
| Методы на графиках | **CG, QA, EA, AUTO** (4 шт.) | SD убран — дублирует CG |
| Стиль | **dark_background** | Единый с остальными графиками |
| Цвета | CG=#FF6B6B, QA=#4ECDC4, EA=#FFE66D, AUTO=#00FF88 | Из common.py |

---

## 2. Структура каталога

```
Animation/
├── PLAN.md                      # Этот план
├── __init__.py                  # Пустой
├── anim_core.py                 # Ядро: AnimScene — общая логика
├── anim_export.py               # Этап A: экспорт GIF (headless)
├── anim_interactive.py          # Этап B: интерактивное окно + слайдеры
├── anim_scope.py                # Этап C: осциллограф (multi-channel scope)
└── output/                      # Результаты
    ├── sweep_all.gif            # S1: sweep -1.5 → +1.5
    ├── sweep_zoom_normal.gif    # S2: zoom normal зона
    ├── noise_ramp.gif           # S3: шум растёт
    ├── step_change.gif          # S4: шаг сетки меняется
    └── auto_demo.gif            # S5: AUTO переключение EA↔E2
```

---

## 3. Общее ядро: `anim_core.py`

**Цель**: один класс `AnimScene` для ВСЕХ трёх скриптов. Без дублирования.

> ⚠️ **Импорт common.py**: `Animation/` — вложенная папка внутри `analysis/`.
> Все скрипты (`anim_core.py`, `anim_export.py`, ...) должны начинаться с:
> ```python
> import sys
> from pathlib import Path
>
> ANIM_DIR    = Path(__file__).resolve().parent          # Animation/
> ANALYSIS_DIR = ANIM_DIR.parent                          # analysis/
> MODULE_DIR   = ANALYSIS_DIR.parent.parent               # discriminator_estimates/
> REPO_ROOT    = MODULE_DIR.parent                         # Refactoring/
> sys.path.insert(0, str(REPO_ROOT))                      # для PyCore
> sys.path.insert(0, str(ANALYSIS_DIR))                   # для common
>
> from common import (sinc, ref_cg_2pt, ref_qa, ref_ea, ref_auto,
>                      select_top2, is_monotonic, COLORS)
> from PyCore.runner import TestRunner, SkipTest
> ```

### 3.1. Класс RingBuffer

```python
class RingBuffer:
    """Кольцевой буфер для scope — хранит последние N значений."""

    def __init__(self, size=200):
        self.data = np.full(size, np.nan)
        self.idx = 0

    def push(self, value):
        self.data[self.idx % len(self.data)] = value
        self.idx += 1

    def get_ordered(self):
        """Данные в хронологическом порядке (старые слева)."""
        n = len(self.data)
        return np.roll(self.data, -(self.idx % n))
```

### 3.2. Класс AnimScene

```python
class AnimScene:
    """Сцена анимации дискриминаторов.

    Отвечает за:
    - Создание figure + axes (верхний + нижний subplot)
    - Все artists (линии, точки, vline'ы, тексты)
    - Метод update(x0, snr, step) — пересчёт + перерисовка
    - НЕ знает про FuncAnimation / Slider — это снаружи
    """
```

### Поля AnimScene

| Поле | Тип | Описание |
|------|-----|----------|
| `fig` | Figure | Фигура matplotlib |
| `ax_main` | Axes | Верхний график: sinc + оценки |
| `ax_bar` | Axes | Нижний график: bar chart ошибок |
| `line_sinc` | Line2D | Кривая sinc(x - x0) |
| `scatter_pts` | PathCollection | 3 жёлтых точки |
| `vline_true` | Line2D | Вертикаль истинного пика |
| `vlines` | dict[str, Line2D] | Вертикали: CG, QA, EA, AUTO |
| `bars` | BarContainer | Bar chart ошибок |
| `text_info` | Text | Текст: ошибки + mode + zone |
| `zone_bg` | Polygon | Фон по зоне (полупрозрачный) |
| `x_fine` | ndarray | Ось X для кривой (500 точек) |
| `history` | dict[str, RingBuffer] | Буферы ошибок (для scope) |
| `rng` | Generator | np.random.default_rng(seed=42) |

### 3.3. Вспомогательная функция classify_zone

```python
def classify_zone(x0):
    """Классификация зоны по смещению пика."""
    ax0 = abs(x0)
    if ax0 <= 0.5:
        return 'normal'
    if ax0 <= 1.0:
        return 'boundary'
    return 'extreme'
```

### 3.4. Метод setup()

```python
def setup(self, figsize=(14, 8), mode='export'):
    """Создать figure и все artists.

    Args:
        figsize: размер фигуры
        mode: 'export'     — верхний + bar chart (для GIF)
              'interactive' — верхний + bar chart + место для слайдеров
              'scope'       — верхний + 4 канала scope
    """
```

- GridSpec разбивает фигуру по mode
- `plt.style.use("dark_background")` — **обязательно перед** `plt.figure()`
- x_fine = np.linspace(-4, 4, 500)
- Начальные данные: x0=0, snr=0, step=1
- **Bar chart — горизонтальный** (`barh`):
  ```python
  method_names = ['CG', 'QA', 'EA', 'AUTO']
  method_colors = [COLORS[m] for m in method_names]
  self.bars = self.ax_bar.barh(method_names, [0, 0, 0, 0], color=method_colors)
  self.ax_bar.set_xlim(0, 1.0)
  self.ax_bar.set_xlabel('|error|')
  # Тексты значений (обновляются в update)
  self.bars_text = []
  for i, name in enumerate(method_names):
      t = self.ax_bar.text(0.01, i, '', va='center', ha='left',
                           color='white', fontsize=9, fontweight='bold')
      self.bars_text.append(t)
  ```
- **zone_bg**: создаётся через `axvspan`, обновляется в update:
  ```python
  self.zone_bg = self.ax_main.axvspan(
      self.ax_main.get_xlim()[0], self.ax_main.get_xlim()[1],
      alpha=0.04, color='green', zorder=0)
  ```

### 3.4. Метод update()

```python
def update(self, x0, snr=0.0, step=1.0):
    """Пересчитать оценки и обновить все artists.

    Алгоритм:
    1. grid = [-step, 0, +step]
    2. A = sinc(grid - x0)
    3. если snr > 0: A += self.rng.normal(0, snr * max(A), 3)
    4. Вычислить оценки:
         A1, A2, x1, x2 = select_top2(A, grid)
         xe_cg = ref_cg_2pt(A1, A2, x1, x2)
         xe_qa = ref_qa(A, grid)
         xe_ea = ref_ea(A, grid)
         xe_auto, auto_mode = ref_auto(A, grid)  # ← кортеж (float, int)!
         # auto_mode: 0=EA, 1=QA fallback, 2=E2 extrap, 3=E2 fail
    5. Вычислить ошибки: err_X = abs(xe_X - x0)
    6. Обновить line_sinc, scatter, vlines, bars, bars_text, text_info
    7. Обновить zone_bg (зона) через classify_zone(x0)
    8. Пушить ошибки в history (RingBuffer)

    Returns:
        list[Artist] — для blit
    """
```

### 3.5. Метод get_artists()

```python
def get_artists(self):
    """Все artists для FuncAnimation(blit=True)."""
    return [self.line_sinc, self.scatter_pts, self.vline_true,
            *self.vlines.values(), self.text_info, self.zone_bg,
            *self.bars.patches, *self.bars_text]
```

---

## 4. Этап A: `anim_export.py` — GIF-экспорт (делаем ПЕРВЫМ)

**Запуск**: `python3 Animation/anim_export.py`

### 5 сценариев

#### S1: `sweep_all.gif` — основной sweep

```
Параметры:
  x0:     -1.5 → +1.5 (линейно)
  SNR:    0
  step:   1.0
  Кадры:  75 (шаг x0 = 0.04)
  FPS:    15
  Время:  5 сек
  DPI:    100
  Размер: 800 × 600 px
```

Содержание кадра:
```
┌─────────────────────────────────────────────────┐
│ x0 = 0.35 | Zone: normal | AUTO: EA             │
│                                                  │
│  sinc(x - x0)  (голубая кривая)                  │
│  ● ● ● (жёлтые точки — 3 отсчёта)               │
│  ┊ зелёный пунктир = истинный пик                │
│  │ красный пунктир = CG                          │
│  │ бирюзовый пунктир = QA                        │
│  │ жёлтый пунктир = EA                           │
│  ██ зелёная толстая = AUTO                       │
│                                                  │
│  [зелёный фон = normal зона]                     │
├──────────────────────────────────────────────────┤
│  CG ████████████████████ 0.234                   │
│  QA ██ 0.008                                     │
│  EA █ 0.005                                      │
│ AUTO █ 0.005 (EA)                                │
└──────────────────────────────────────────────────┘
```

#### S2: `sweep_zoom_normal.gif` — zoom

```
x0:     -0.5 → +0.5
xlim:   -2 → +2 (zoom)
Кадры:  50, FPS: 15
Смысл:  EA/QA точные, CG далеко — видно на крупном плане
```

#### S3: `noise_ramp.gif` — шум растёт

```
x0:     0.2 (фиксирован)
SNR:    0.0 → 0.25 (линейно)
Кадры:  75, FPS: 15, seed: 42
Смысл:  QA "взрывается", EA/AUTO плавно деградируют
Фишка:  точки "дрожат", вертикали QA мечутся
```

#### S4: `step_change.gif` — шаг сетки

```
x0:     0.2 (фиксирован)
step:   0.3 → 2.5 (линейно)
Кадры:  60, FPS: 15
Смысл:  сетка расширяется, точность падает
Фишка:  xlim динамически расширяется, точки разъезжаются
```

#### S5: `auto_demo.gif` — AUTO переключение (range шире!)

```
x0:     -2.0 → +2.0  (⚠️ шире чем S1! чтобы чаще monotonic зона)
Кадры:  75, FPS: 15
Смысл:  AUTO = EA в центре, → E2 по краям (|x0| > ~1.0)
Фишка:  момент переключения EA→E2 выделен:
        - текст info показывает "AUTO: E2" / "AUTO: EA"
        - линия AUTO меняет стиль (сплошная → пунктир)
```

### Структура кода

```python
"""anim_export.py — Экспорт GIF (headless).

Запуск:
    cd discriminator_estimates/test_python
    python analysis/Animation/anim_export.py
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

# --- Пути (Animation/ → analysis/ → ...) ---
ANIM_DIR     = Path(__file__).resolve().parent
ANALYSIS_DIR = ANIM_DIR.parent
REPO_ROOT    = ANALYSIS_DIR.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))
sys.path.insert(0, str(ANIM_DIR))

from anim_core import AnimScene
from PyCore.runner import TestRunner
from matplotlib.animation import FuncAnimation, PillowWriter

OUT = Path(__file__).resolve().parent / "output"
OUT.mkdir(parents=True, exist_ok=True)  # ← создать output/ если нет!

def export(name, x0_fn, snr_fn, step_fn, n_frames=75, fps=15, dpi=100):
    """Универсальный экспортёр."""
    scene = AnimScene()
    scene.setup(figsize=(8, 6), mode='export')

    def init():
        """Начальный кадр (init_func ДОЛЖНА вызвать update!)."""
        scene.update(x0_fn(0), snr_fn(0), step_fn(0))
        return scene.get_artists()

    def update(frame):
        return scene.update(x0_fn(frame), snr_fn(frame), step_fn(frame))

    anim = FuncAnimation(scene.fig, update, frames=n_frames,
                         init_func=init,  # ← НЕ scene.get_artists!
                         blit=True, interval=1000//fps)
    path = OUT / f"{name}.gif"
    anim.save(str(path), writer='pillow', fps=fps, dpi=dpi)
    plt.close(scene.fig)
    print(f"  [OK] {path.name} ({n_frames} frames, {fps} fps)")
    return path


class TestExportGIF:
    """Тесты экспорта GIF (через TestRunner)."""

    def test_sweep_all(self):
        """S1: sweep -1.5 → +1.5."""
        p = export("sweep_all",
                   x0_fn  = lambda f: -1.5 + 3.0 * f / 74,
                   snr_fn = lambda f: 0.0,
                   step_fn= lambda f: 1.0)
        assert p.exists(), f"GIF not created: {p}"
        # Верификация: проверить что GIF валидный
        from PIL import Image
        im = Image.open(str(p))
        assert im.n_frames >= 10, f"Too few frames: {im.n_frames}"
        print(f"  [OK] {p.name}: {im.n_frames} frames, {im.size}")

    # S2-S5: аналогично с разными лямбдами


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(TestExportGIF())
    runner.print_summary(results)
```

---

## 5. Этап B: `anim_interactive.py` — Интерактивное окно

**Запуск**: `python3 Animation/anim_interactive.py`

### Макет (1400 × 900 px)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│              ВЕРХНИЙ ГРАФИК: sinc + оценки (60%)                │
│                                                                 │
│   sinc кривая + точки + вертикали CG/QA/EA/AUTO                │
│   Фон по зоне (зелёный / жёлтый / красный)                     │
│   Заголовок: x0, zone, AUTO mode                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│   BAR CHART ошибок (15%)                                        │
│   CG ████████ 0.234   QA ██ 0.008   EA █ 0.005   AUTO █ 0.005 │
├─────────────────────────────────────────────────────────────────┤
│   СЛАЙДЕРЫ (15%)                                                │
│                                                                 │
│   x0:   [━━━━━━━●━━━━━━━] 0.25    (-1.5 .. +1.5)              │
│   SNR:  [●━━━━━━━━━━━━━━] 0.00    (0.00 .. 0.30)              │
│   step: [━━━━━━━●━━━━━━━] 1.00    (0.20 .. 2.50)              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│   КНОПКИ + ИНФО (10%)                                           │
│                                                                 │
│   [▶ Play] [⏸ Pause] [⏺ Rec GIF] [↺ Reset]                   │
│                                                                 │
│   CG=0.234  QA=0.008  EA=0.005  AUTO=0.005 (EA)               │
│   Zone: normal  │  Monotonic: No  │  Frame: —                   │
└─────────────────────────────────────────────────────────────────┘
```

### Два режима

#### Manual — слайдеры

```python
slider_x0.on_changed(on_slider_change)
slider_snr.on_changed(on_slider_change)
slider_step.on_changed(on_slider_change)

def on_slider_change(val):
    scene.update(slider_x0.val, slider_snr.val, slider_step.val)
    fig.canvas.draw_idle()
```

- НЕТ FuncAnimation
- Мгновенный отклик через `draw_idle()`
- Шум: новый на каждое движение слайдера

#### Play — автоматический sweep

```python
timer = fig.canvas.new_timer(interval=50)  # 20 fps
timer.add_callback(play_step)

x0_play = -1.5

def play_step():
    global x0_play
    x0_play += 0.02
    if x0_play > 1.5:
        x0_play = -1.5  # loop
    slider_x0.set_val(x0_play)

def on_play(event):
    timer.start()

def on_pause(event):
    timer.stop()
```

- `new_timer` вместо FuncAnimation (нет конфликта с виджетами)
- Слайдер x0 двигается автоматически (визуально!)
- SNR и step можно менять ПОКА играет
- Кнопка Pause останавливает таймер

#### Record GIF

```python
def on_record(event):
    timer.stop()
    scene.rng = np.random.default_rng(seed=42)  # ← сброс rng для воспроизводимости!
    frames = []
    for x0 in np.linspace(-1.5, 1.5, 75):
        scene.update(x0, slider_snr.val, slider_step.val)
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
        img = Image.frombuffer('RGBA', fig.canvas.get_width_height(), buf)
        frames.append(img.convert('RGB'))
    path = OUT / "recorded.gif"
    frames[0].save(str(path), save_all=True,
                   append_images=frames[1:], duration=66, loop=0)
    print(f"Saved: {path}")
```

### Кнопки

| Кнопка | Label | Callback | Действие |
|--------|-------|----------|----------|
| Play | "▶ Play" | `on_play` | Запуск таймера |
| Pause | "⏸ Pause" | `on_pause` | Остановка таймера |
| Rec | "⏺ Rec GIF" | `on_record` | Sweep → GIF |
| Reset | "↺ Reset" | `on_reset` | x0=0, SNR=0, step=1 |

### Расположение (fig.add_axes)

```python
fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(nrows=20, ncols=1, hspace=0.3)

ax_main = fig.add_subplot(gs[0:12, 0])      # sinc (60%)
ax_bar  = fig.add_subplot(gs[12:15, 0])      # bar  (15%)

# Слайдеры — отдельные axes (абсолютные координаты)
ax_sl_x0   = fig.add_axes([0.15, 0.18, 0.70, 0.02])
ax_sl_snr  = fig.add_axes([0.15, 0.14, 0.70, 0.02])
ax_sl_step = fig.add_axes([0.15, 0.10, 0.70, 0.02])

# Кнопки
ax_btn_play  = fig.add_axes([0.15, 0.03, 0.12, 0.04])
ax_btn_pause = fig.add_axes([0.30, 0.03, 0.12, 0.04])
ax_btn_rec   = fig.add_axes([0.45, 0.03, 0.15, 0.04])
ax_btn_reset = fig.add_axes([0.63, 0.03, 0.12, 0.04])
```

---

## 6. Этап C: `anim_scope.py` — Осциллограф

**Запуск**: `python3 Animation/anim_scope.py`

### Макет (1200 × 800 px)

```
┌────────────────────────────────────────────────┐
│  sinc(x-x0) + точки + оценки (компактно) 25%  │
├────────────────────────────────────────────────┤
│  CG  ────/\──────/\──────/\──── 0.45    (15%) │
├────────────────────────────────────────────────┤
│  QA  ──────────────────/‾‾‾── 0.07      (15%) │
├────────────────────────────────────────────────┤
│  EA  ──────────────────────── 0.01       (15%) │
├────────────────────────────────────────────────┤
│  AUTO ─────────────────────── 0.01       (15%) │
│                                                │
│  ◄── 200 кадров (10 сек) ──►                   │
│  Фон: ██norm ██bound ██extr                    │
├────────────────────────────────────────────────┤
│  [▶ Play]  Frame: 142/301  │  x0=0.42   (15%) │
└────────────────────────────────────────────────┘
```

### 4 канала scope (отдельные Axes)

```python
gs = fig.add_gridspec(nrows=8, ncols=1, hspace=0.15)
ax_sinc  = fig.add_subplot(gs[0:2, 0])   # sinc  (25%)
ax_cg    = fig.add_subplot(gs[2, 0])      # CG    (12.5%)
ax_qa    = fig.add_subplot(gs[3, 0])      # QA    (12.5%)
ax_ea    = fig.add_subplot(gs[4, 0])      # EA    (12.5%)
ax_auto  = fig.add_subplot(gs[5, 0])      # AUTO  (12.5%)
# gs[6:8] — кнопки и инфо
```

Каждый канал:
- Своя Y-шкала (CG: 0..1, QA/EA/AUTO: 0..0.5)
- Линия ошибки = `RingBuffer.get_ordered()`
- Фон горизонтально раскрашен по зонам (normal=зел, boundary=жёлт, extreme=красн)
- Текст справа: текущее значение ошибки

> ⚠️ **RingBuffer и NaN**: первые ~200 кадров буфер содержит NaN.
> matplotlib **пропускает NaN** при рисовании Line2D — это OK.
> Но `ax.set_ylim(auto=True)` может глючить на NaN — лучше
> фиксировать ylim вручную для каждого канала.

Обновление: `FuncAnimation` с `blit=True`, sweep x0 от -1.5 до +1.5.

> **fps синхронизация**: GIF экспортируется с `fps=15` (interval=66ms).
> Интерактивный Play использует `timer interval=50` (20fps).
> Для визуальной согласованности рекомендуется `FPS = 15` как константа:
> ```python
> FPS = 15
> INTERVAL_MS = 1000 // FPS  # = 66 ms
> ```

---

## 7. Технические решения

### 7.1. blit=True для экспорта и scope

```python
anim = FuncAnimation(fig, update, frames=N, blit=True, interval=50)
```

Все изменяемые artists возвращаются из `update()`.
Статические элементы (оси, сетка, заголовки) рисуются один раз.

### 7.2. Таймер вместо FuncAnimation для interactive

```python
timer = fig.canvas.new_timer(interval=50)
timer.add_callback(step_func)
```

Причина: FuncAnimation(blit=True) конфликтует с Slider.
Timer + draw_idle() работает стабильно.

### 7.3. xlim — фиксированный по умолчанию, динамический для S4

```python
# По умолчанию: xlim=[-4, 4] (из setup), x_fine=np.linspace(-4, 4, 500)
# Динамический xlim — ТОЛЬКО для S4 (step_change):
if dynamic_xlim:
    margin = step * 1.5
    ax_main.set_xlim(-step - margin, step + margin)
```

Фиксированный xlim гарантирует что sinc виден при любом x0 ∈ [-1.5, 1.5].

### 7.4. Индикация переключения AUTO mode

```python
mode_names = {0: 'EA', 1: 'QA', 2: 'E2', 3: 'FAIL'}  # 3 = E2 не сошлась!
mode_colors = {0: '#FFE66D', 1: '#4ECDC4', 2: '#00FF88', 3: '#FF6B6B'}

# AUTO вертикаль меняет стиль:
if mode == 2:  # E2 экстраполяция
    vline_auto.set_linestyle('--')    # пунктир = экстраполяция
    vline_auto.set_linewidth(3)
else:
    vline_auto.set_linestyle('-')     # сплошная = EA/QA
    vline_auto.set_linewidth(2.5)
```

### 7.5. Фон по зонам (axvspan)

```python
ZONE_COLORS = {
    'normal': ('#00FF00', 0.04),    # зелёный, очень прозрачный
    'boundary': ('#FFFF00', 0.04),  # жёлтый
    'extreme': ('#FF0000', 0.06),   # красный, чуть ярче
}

# Обновляется в update():
zone = classify_zone(x0)

# ⚠️ КРИТИЧНО: НЕ вызывать remove()! Это ломает blit.
# Просто менять цвет и прозрачность:
self.zone_bg.set_facecolor(ZONE_COLORS[zone][0])
self.zone_bg.set_alpha(ZONE_COLORS[zone][1])

# zone_bg создаётся в setup() с xlim=[-4, 4] — покрывает весь график.
# При динамическом xlim (S4) zone_bg автоматически растягивается
# вместе с осями, т.к. axvspan привязан к data coordinates.
```

> ✅ zone_bg — один объект на всю жизнь figure. Создан в setup(), обновляется
> через set_facecolor()/set_alpha(). Никогда не remove()!

### 7.6. GIF размер

| Параметр | Значение |
|----------|---------|
| DPI | 100 |
| Размер | 800 × 600 px |
| FPS | 15 |
| Цикл | loop=0 (бесконечный) |
| Writer | PillowWriter |
| Ожидание | 3-8 МБ/файл |

---

## 8. Задачи (обновлено 2026-04-02, после ревью)

> **Статус**: common.py ✅ готов, 8 скриптов (01-08) ✅ готовы.
> Animation/ — только PLAN.md, код ещё не написан.

### Фаза 0: Подготовка

| # | Задача | Файл | Статус | Примечание |
|---|--------|------|--------|------------|
| 0.1 | Создать `__init__.py` (пустой) | `Animation/__init__.py` | ⬜ | Нужен для import |
| 0.2 | Создать `output/` (каталог) | `Animation/output/` | ⬜ | + `.gitkeep` |

### Фаза 1: Ядро (anim_core.py)

| # | Задача | Статус | Примечание |
|---|--------|--------|------------|
| 1.1 | `RingBuffer` класс | ⬜ | push(), get_ordered(), size=200 |
| 1.2 | `AnimScene.__init__()` + `setup()` | ⬜ | GridSpec, dark_background, все artists |
| 1.3 | `AnimScene.update(x0, snr, step)` | ⬜ | ⚠️ Использовать `ref_ea_c` вместо `ref_ea` (см. R-01) |
| 1.4 | `AnimScene.get_artists()` | ⬜ | Для blit=True |
| 1.5 | Импорт `classify_zone` из `common.py` | ⬜ | ⚠️ НЕ дублировать! (см. R-02) |
| 1.6 | Smoke test: рендер 1 кадра в PNG | ⬜ | `fig.savefig("test_frame.png")` |

### Фаза 2: GIF-экспорт (anim_export.py)

| # | Задача | Статус | Примечание |
|---|--------|--------|------------|
| 2.1 | Каркас: `export()` + `TestExportGIF` | ⬜ | PillowWriter, Agg backend |
| 2.2 | S1: `sweep_all.gif` (75 кадров) | ⬜ | x0: -1.5→+1.5, основной |
| 2.3 | S2: `sweep_zoom_normal.gif` (50 кадров) | ⬜ | x0: -0.5→+0.5, zoom |
| 2.4 | S3: `noise_ramp.gif` (75 кадров) | ⬜ | SNR: 0→0.25, seed=42 |
| 2.5 | S4: `step_change.gif` (60 кадров) | ⬜ | step: 0.3→2.5, динамический xlim |
| 2.6 | S5: `auto_demo.gif` (75 кадров) | ⬜ | AUTO EA↔E2 переключение |
| 2.7 | **ТЕСТ**: все 5 GIF валидны (PIL check) | ⬜ | frames count + size check |

### Фаза 3: Интерактив (anim_interactive.py)

| # | Задача | Статус | Примечание |
|---|--------|--------|------------|
| 3.1 | Окно + GridSpec (14×9) | ⬜ | TkAgg backend |
| 3.2 | 3 слайдера: x0, SNR, step | ⬜ | Manual mode: draw_idle() |
| 3.3 | Play/Pause (timer, 20fps) | ⬜ | new_timer, НЕ FuncAnimation |
| 3.4 | Record GIF кнопка | ⬜ | rng reset seed=42 |
| 3.5 | Reset кнопка | ⬜ | x0=0, SNR=0, step=1 |
| 3.6 | **ТЕСТ**: слайдеры + Play + Record | ⬜ | Визуальная проверка |

### Фаза 4: Осциллограф (anim_scope.py)

| # | Задача | Статус | Примечание |
|---|--------|--------|------------|
| 4.1 | Layout: sinc + 4 канала scope | ⬜ | 8-row GridSpec |
| 4.2 | RingBuffer → Line2D для каждого канала | ⬜ | NaN-safe, фикс ylim |
| 4.3 | Фон по зонам (цветные полосы) | ⬜ | normal/boundary/extreme |
| 4.4 | FuncAnimation sweep + blit | ⬜ | 15fps, x0: -1.5→+1.5 |
| 4.5 | **ТЕСТ**: scope работает | ⬜ | Визуальная проверка |

### Контрольные точки (после каждой можно остановиться)

```
  [0-1.6] → smoke test: один кадр рендерится (минимальный результат)
  [0-2.7] → 5 GIF-файлов для документации ← ОСНОВНАЯ ЦЕЛЬ
  [0-3.6] → интерактивное окно "как Simulink Scope"
  [0-4.5] → полный комплект + осциллограф
```

### Итого: 22 задачи (4 фазы)

---

## 9. Что НЕ делаем (осознанно)

| Что | Почему нет |
|-----|-----------|
| SD на графиках | Дублирует CG |
| Звуковые сигналы | Перебор |
| Plotly/Dash | Лишняя зависимость |
| Manim | Не интерактивный, тяжёлый |
| MP4 экспорт | ffmpeg не установлен, GIF хватит |
| Jupyter виджеты | Работаем в терминале |
| 3D-анимация | Overkill |

---

## 10. Зависимости (все уже есть)

| Библиотека | Для чего | Статус |
|------------|----------|--------|
| matplotlib 3.10.1 | Анимация + виджеты | ✅ |
| numpy | Вычисления | ✅ |
| scipy | curve_fit для EA | ✅ |
| Pillow | GIF-экспорт | ✅ |
| TkAgg | Интерактивный бэкенд | ✅ |
| common.py | sinc, ref_*, COLORS | ✅ |

**Ничего ставить не нужно!**

---

---

## 11. Верификация после каждой контрольной точки

```bash
# После [1-5]: проверить GIF
python3 -c "
from PIL import Image
im = Image.open('Animation/output/sweep_all.gif')
print(f'OK: {im.n_frames} frames, {im.size}')
"

# После [1-6]: проверить все 5 GIF
for f in sweep_all sweep_zoom_normal noise_ramp step_change auto_demo; do
  python3 -c "from PIL import Image; im=Image.open('Animation/output/${f}.gif'); print(f'${f}: {im.n_frames} frames')"
done

# После [1-10]: запустить интерактив (визуально)
python3 Animation/anim_interactive.py
# Проверить: слайдеры двигаются, Play/Pause работает, Record GIF сохраняет

# После [1-12]: scope
python3 Animation/anim_scope.py
```

---

*План утверждён. Готов к реализации по команде Alex.*
*Ревью: Кодо (старшая AI) — 5 критических + 7 важных фиксов внесены, 2026-04-02*
