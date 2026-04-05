"""
anim_core.py — Ядро анимации дискриминаторов.

Содержит:
  - RingBuffer: кольцевой буфер для scope
  - AnimScene: общая сцена (setup + update) для export/interactive/scope

Запуск self-test:
    cd discriminator_estimates/test_python
    python analysis/Animation/anim_core.py
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# --- Пути (Animation/ → analysis/ → test_python/ → discriminator_estimates/ → Refactoring/) ---
ANIM_DIR     = Path(__file__).resolve().parent          # Animation/
ANALYSIS_DIR = ANIM_DIR.parent                          # analysis/
MODULE_DIR   = ANALYSIS_DIR.parent.parent               # discriminator_estimates/
REPO_ROOT    = MODULE_DIR.parent                        # Refactoring/
sys.path.insert(0, str(REPO_ROOT))                      # для PyCore
sys.path.insert(0, str(ANALYSIS_DIR))                   # для common

from common import (sinc, hanning_kernel, ref_cg_2pt, ref_qa, ref_ea, ref_auto,
                     select_top2, classify_zone, COLORS,
                     ref_5ea, ref_5qa)
from PyCore.runner import TestRunner, SkipTest


# ══════════════════════════════════════════════════════════════════════ #
#  Константы                                                             #
# ══════════════════════════════════════════════════════════════════════ #

FPS = 8
INTERVAL_MS = 1000 // FPS  # 125 ms
METHODS = ['CG', 'QA', 'EA', 'AUTO', 'LSQ5E', 'LSQ5Q']
ZONE_COLORS = {
    'normal':   ('#00FF00', 0.04),
    'boundary': ('#FFFF00', 0.04),
    'extreme':  ('#FF0000', 0.06),
}
ZONE_NAMES_RU = {
    'normal':   'нормальная',
    'boundary': 'граничная',
    'extreme':  'экстремальная',
}
MODE_NAMES = {0: 'EA', 1: 'QA', 2: 'E2', 3: 'FAIL'}
METHOD_NAMES_RU = {
    'CG':    'ЦТ (центр тяжести)',
    'QA':    'КА (квадр. 3т)',
    'EA':    'ЭА (экспон. 3т)',
    'AUTO':  'АВТО (автовыбор)',
    'LSQ5E': 'МНК-гаусс 5т',
    'LSQ5Q': 'МНК-параб. 5т',
}


# ══════════════════════════════════════════════════════════════════════ #
#  RingBuffer                                                            #
# ══════════════════════════════════════════════════════════════════════ #

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


# ══════════════════════════════════════════════════════════════════════ #
#  AnimScene                                                             #
# ══════════════════════════════════════════════════════════════════════ #

class AnimScene:
    """Сцена анимации дискриминаторов.

    Отвечает за:
    - Создание figure + axes (main + bar subplot)
    - Все artists (линии, точки, vline'ы, тексты)
    - Метод update(x0, snr, step) — пересчёт + перерисовка
    - НЕ знает про FuncAnimation / Slider — это снаружи
    """

    def __init__(self):
        self.fig = None
        self._dynamic_xlim = False
        self._smooth = 0.0        # EMA сглаживание: 0=нет, 0.9=сильное
        self._prev_estimates = {}  # предыдущие оценки для EMA
        self._prev_errors = {}    # предыдущие ошибки для EMA

    def setup(self, figsize=(14, 8), mode='export'):
        """Создать figure и все artists.

        Args:
            figsize: размер фигуры
            mode: 'export'      — 75% main + 25% bar (для GIF)
                  'interactive' — 60% main + 15% bar + 25% пусто (слайдеры)
        """
        plt.style.use("dark_background")
        self.fig = plt.figure(figsize=figsize)

        # GridSpec по mode
        if mode == 'interactive':
            gs = self.fig.add_gridspec(nrows=4, ncols=1,
                                       height_ratios=[60, 15, 15, 10],
                                       hspace=0.35)
            self.ax_main = self.fig.add_subplot(gs[0])
            self.ax_bar  = self.fig.add_subplot(gs[1])
            # gs[2] и gs[3] — для слайдеров и кнопок (создаются снаружи)
        else:  # 'export'
            gs = self.fig.add_gridspec(nrows=2, ncols=1,
                                       height_ratios=[75, 25],
                                       hspace=0.30)
            self.ax_main = self.fig.add_subplot(gs[0])
            self.ax_bar  = self.fig.add_subplot(gs[1])

        # --- Оси X для кривой ---
        self.x_fine = np.linspace(-4, 4, 500)
        self.rng = np.random.default_rng(seed=42)

        # --- Artists на ax_main ---
        y_init = hanning_kernel(self.x_fine)
        self.line_sinc = self.ax_main.plot(
            self.x_fine, y_init, color='#00BFFF', lw=2,
            label='Hanning(x\u2212x\u2080)')[0]

        init_grid = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        init_A = hanning_kernel(init_grid)
        self.scatter_pts = self.ax_main.scatter(
            init_grid, init_A, c='#FFE66D', s=100, zorder=5,
            label='\u041e\u0442\u0441\u0447\u0451\u0442\u044b (5)')  # Отсчёты (5)

        self.vline_true = self.ax_main.axvline(
            0, color='lime', ls=':', lw=2, zorder=3,
            label='\u0418\u0441\u0442\u0438\u043d\u043d\u044b\u0439 \u043f\u0438\u043a')  # Истинный пик

        # Вертикали для каждого метода
        self.vlines = {}
        method_styles = {
            'CG':    {'color': COLORS['CG'],    'ls': '--', 'lw': 1.5},
            'QA':    {'color': COLORS['QA'],    'ls': '--', 'lw': 1.5},
            'EA':    {'color': COLORS['EA'],    'ls': '--', 'lw': 1.5},
            'AUTO':  {'color': COLORS['AUTO'],  'ls': '-',  'lw': 3},
            'LSQ5E': {'color': COLORS['LSQ5E'], 'ls': '-.', 'lw': 2},
            'LSQ5Q': {'color': COLORS['LSQ5Q'], 'ls': '-.', 'lw': 2},
        }
        for m in METHODS:
            s = method_styles[m]
            self.vlines[m] = self.ax_main.axvline(
                0, color=s['color'], ls=s['ls'], lw=s['lw'],
                zorder=4, label=METHOD_NAMES_RU[m])

        # Зоновый фон
        xlim = [-4, 4]
        self.zone_bg = self.ax_main.axvspan(
            xlim[0], xlim[1], alpha=0.04, color='green', zorder=0)

        # Текстовая информация
        self.text_info = self.ax_main.text(
            0.02, 0.98, '', transform=self.ax_main.transAxes,
            va='top', ha='left', color='white', fontsize=9,
            fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.6))

        # Настройка ax_main
        self.ax_main.set_xlim(-4, 4)
        self.ax_main.set_ylim(-0.3, 1.15)
        self.ax_main.set_xlabel('\u041a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442\u0430 x')  # Координата x
        self.ax_main.set_ylabel('\u0410\u043c\u043f\u043b\u0438\u0442\u0443\u0434\u0430')  # Амплитуда
        self.ax_main.set_title(
            '\u0414\u0438\u0441\u043a\u0440\u0438\u043c\u0438\u043d\u0430\u0442\u043e\u0440\u043d\u044b\u0435 '
            '\u043e\u0446\u0435\u043d\u043a\u0438 \u043a\u043e\u043e\u0440\u0434\u0438\u043d\u0430\u0442: '
            'Hanning kernel')  # Дискриминаторные оценки координат: Hanning kernel
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend(loc='upper right', fontsize=6, ncol=3)

        # --- Artists на ax_bar (горизонтальный barh) ---
        method_colors = [COLORS[m] for m in METHODS]
        bar_labels_short = ['ЦТ', 'КА', 'ЭА', 'АВТО', 'МНКГ', 'МНКП']
        self.bars = self.ax_bar.barh(bar_labels_short, [0]*len(METHODS), color=method_colors)
        self.bars_text = []
        for i, m in enumerate(METHODS):
            t = self.ax_bar.text(0.01, i, '', va='center', ha='left',
                                 color='white', fontsize=9, fontweight='bold')
            self.bars_text.append(t)
        self.ax_bar.set_xlim(0, 1.0)
        self.ax_bar.set_xlabel('|\u043e\u0448\u0438\u0431\u043a\u0430|')  # |ошибка|
        self.ax_bar.set_title(
            '\u041e\u0448\u0438\u0431\u043a\u0430 \u043e\u0446\u0435\u043d\u043a\u0438 '
            '(\u0447\u0435\u043c \u043c\u0435\u043d\u044c\u0448\u0435 \u2014 '
            '\u0442\u0435\u043c \u043b\u0443\u0447\u0448\u0435)',
            fontsize=10)  # Ошибка оценки (чем меньше — тем лучше)

        # --- History для scope ---
        self.history = {m: RingBuffer(200) for m in METHODS}

        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.90, bottom=0.08)
        return self.fig

    def update(self, x0, snr=0.0, step=1.0):
        """Пересчитать оценки и обновить все artists.

        Returns:
            list[Artist] — для blit
        """
        # Шаг 1: Сетка 5 точек и амплитуды
        grid5 = np.array([-2*step, -step, 0.0, step, 2*step])
        A5 = hanning_kernel(grid5 - x0)
        if snr > 0:
            A5 = A5 + self.rng.normal(0, snr * np.max(np.abs(A5)), 5)

        # 3 центральных точки (для 3-точечных методов)
        grid3 = grid5[1:4]   # [-step, 0, step]
        A3 = A5[1:4]

        # Шаг 2: Оценки — 3-точечные методы
        A1, A2, x1, x2 = select_top2(A3, grid3)
        xe_cg = ref_cg_2pt(A1, A2, x1, x2)
        xe_qa = ref_qa(A3, grid3)
        xe_ea = ref_ea(A3, grid3)
        xe_auto, auto_mode = ref_auto(A3, grid3)

        # Шаг 2b: Оценки — 5-точечные МНК
        xe_5ea = ref_5ea(A5, grid5)
        xe_5qa = ref_5qa(A5, grid5)

        # Шаг 3: Ошибки
        errors = {
            'CG': abs(xe_cg - x0), 'QA': abs(xe_qa - x0),
            'EA': abs(xe_ea - x0), 'AUTO': abs(xe_auto - x0),
            'LSQ5E': abs(xe_5ea - x0), 'LSQ5Q': abs(xe_5qa - x0),
        }
        estimates = {
            'CG': xe_cg, 'QA': xe_qa, 'EA': xe_ea, 'AUTO': xe_auto,
            'LSQ5E': xe_5ea, 'LSQ5Q': xe_5qa,
        }

        # Шаг 3b: EMA-сглаживание (если включено)
        alpha = 1.0 - self._smooth  # smooth=0 → alpha=1 (без сглаж.)
        if self._smooth > 0 and self._prev_estimates:
            for m in METHODS:
                estimates[m] = alpha * estimates[m] + (1 - alpha) * self._prev_estimates.get(m, estimates[m])
                errors[m]    = alpha * errors[m]    + (1 - alpha) * self._prev_errors.get(m, errors[m])
        self._prev_estimates = dict(estimates)
        self._prev_errors = dict(errors)

        # Шаг 4: Обновить line_sinc
        self.line_sinc.set_ydata(hanning_kernel(self.x_fine - x0))

        # Шаг 5: Обновить scatter (5 точек)
        self.scatter_pts.set_offsets(np.column_stack([grid5, A5]))

        # Шаг 6: Обновить vlines
        self.vline_true.set_xdata([x0, x0])
        for m in METHODS:
            self.vlines[m].set_xdata([estimates[m], estimates[m]])

        # Шаг 7: Стиль AUTO вертикали
        if auto_mode == 2:
            self.vlines['AUTO'].set_linestyle('--')
            self.vlines['AUTO'].set_linewidth(3)
        else:
            self.vlines['AUTO'].set_linestyle('-')
            self.vlines['AUTO'].set_linewidth(2.5)

        # Шаг 8: Обновить bars
        max_err = max(max(errors.values()), 0.01)
        self.ax_bar.set_xlim(0, max_err * 1.3)
        for i, m in enumerate(METHODS):
            self.bars[i].set_width(errors[m])
            mode_suffix = f" ({MODE_NAMES[auto_mode]})" if m == 'AUTO' else ""
            self.bars_text[i].set_text(f" {errors[m]:.4f}{mode_suffix}")
            self.bars_text[i].set_x(errors[m] + max_err * 0.02)

        # Шаг 9: Обновить zone_bg (НЕ удалять/пересоздавать!)
        zone = classify_zone(x0)
        self.zone_bg.set_facecolor(ZONE_COLORS[zone][0])
        self.zone_bg.set_alpha(ZONE_COLORS[zone][1])

        # Шаг 10: Динамический xlim (только для S4 step_change)
        if self._dynamic_xlim:
            margin = step * 1.5
            self.ax_main.set_xlim(-step - margin, step + margin)

        # Шаг 11: Текст (русский)
        zone_ru = ZONE_NAMES_RU.get(zone, zone)
        info = (f"x\u2080={x0:.2f} | \u0417\u043e\u043d\u0430: {zone_ru}"
                f" | \u0410\u0412\u0422\u041e: {MODE_NAMES[auto_mode]}\n"
                f"\u0426\u0422={errors['CG']:.4f}  "
                f"\u041a\u0410={errors['QA']:.4f}  "
                f"\u042d\u0410={errors['EA']:.4f}  "
                f"\u0410\u0412\u0422\u041e={errors['AUTO']:.4f}\n"
                f"\u041c\u041d\u041a\u0413={errors['LSQ5E']:.4f}  "
                f"\u041c\u041d\u041a\u041f={errors['LSQ5Q']:.4f}")
        self.text_info.set_text(info)

        # Шаг 12: Push в history
        for m in METHODS:
            self.history[m].push(errors[m])

        # Шаг 13: Return artists
        return self.get_artists()

    def get_artists(self):
        """Все artists для FuncAnimation(blit=True)."""
        return [self.line_sinc, self.scatter_pts, self.vline_true,
                *self.vlines.values(), self.text_info, self.zone_bg,
                *self.bars.patches, *self.bars_text]


# ══════════════════════════════════════════════════════════════════════ #
#  Self-tests                                                            #
# ══════════════════════════════════════════════════════════════════════ #

class TestRingBuffer:
    """Тесты RingBuffer."""

    def test_push_and_get(self):
        """5 push'ей — порядок сохранён."""
        rb = RingBuffer(10)
        for v in [1, 2, 3, 4, 5]:
            rb.push(v)
        ordered = rb.get_ordered()
        # Последние 5 = [1,2,3,4,5], остальные NaN
        values = ordered[~np.isnan(ordered)]
        assert list(values) == [1, 2, 3, 4, 5], f"Got: {values}"
        print("  [PASS] test_push_and_get")

    def test_overflow(self):
        """210 push'ей в буфер size=200 — NaN исчезли."""
        rb = RingBuffer(200)
        for i in range(210):
            rb.push(float(i))
        ordered = rb.get_ordered()
        assert not np.any(np.isnan(ordered)), "NaN should be gone after overflow"
        # Первый элемент = 10 (самый старый из оставшихся)
        assert ordered[0] == 10.0, f"First element: {ordered[0]}"
        assert ordered[-1] == 209.0, f"Last element: {ordered[-1]}"
        print("  [PASS] test_overflow")

    def test_empty(self):
        """Пустой буфер — всё NaN."""
        rb = RingBuffer(5)
        ordered = rb.get_ordered()
        assert np.all(np.isnan(ordered)), "Empty buffer should be all NaN"
        print("  [PASS] test_empty")


class TestAnimSceneSetup:
    """Тесты AnimScene.setup()."""

    def test_setup_export(self):
        """setup(mode='export') — figure создаётся."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        fig = scene.setup(figsize=(8, 6), mode='export')
        assert fig is not None
        assert scene.ax_main is not None
        assert scene.ax_bar is not None
        assert len(scene.x_fine) == 500
        plt.close(fig)
        print("  [PASS] test_setup_export")

    def test_setup_interactive(self):
        """setup(mode='interactive') — figure с местом для слайдеров."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        fig = scene.setup(figsize=(14, 9), mode='interactive')
        assert fig is not None
        plt.close(fig)
        print("  [PASS] test_setup_interactive")

    def test_artists_exist(self):
        """Все artists созданы."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        assert scene.line_sinc is not None
        assert scene.scatter_pts is not None
        assert scene.vline_true is not None
        assert len(scene.vlines) == 6
        assert scene.zone_bg is not None
        assert scene.text_info is not None
        assert len(scene.bars) == 6
        assert len(scene.bars_text) == 6
        assert len(scene.history) == 6
        plt.close(scene.fig)
        print("  [PASS] test_artists_exist")


class TestAnimSceneUpdate:
    """Тесты AnimScene.update()."""

    def test_update_normal(self):
        """x0=0.2, snr=0, step=1 — errors dict корректен."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        artists = scene.update(0.2, 0, 1.0)
        assert isinstance(artists, list)
        assert len(artists) > 0
        plt.close(scene.fig)
        print("  [PASS] test_update_normal")

    def test_update_extreme(self):
        """x0=1.3 — extreme зона, update без ошибок."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        scene.update(1.3, 0, 1.0)
        txt = scene.text_info.get_text()
        assert '\u044d\u043a\u0441\u0442\u0440\u0435\u043c\u0430\u043b\u044c\u043d\u0430\u044f' in txt, f"Expected extreme zone, got: {txt}"
        plt.close(scene.fig)
        print("  [PASS] test_update_extreme")

    def test_update_noise(self):
        """x0=0.2, snr=0.1 — errors > 0."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        scene.update(0.2, 0.1, 1.0)
        plt.close(scene.fig)
        print("  [PASS] test_update_noise")

    def test_update_dynamic_xlim(self):
        """x0=0.2, step=0.5, dynamic_xlim — xlim обновился."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        scene._dynamic_xlim = True
        scene.update(0.2, 0, 0.5)
        xlim = scene.ax_main.get_xlim()
        assert xlim[0] > -4, f"xlim should be narrower: {xlim}"
        plt.close(scene.fig)
        print("  [PASS] test_update_dynamic_xlim")

    def test_render_frame(self):
        """Сохранить один кадр в PNG — размер > 0."""
        import matplotlib
        matplotlib.use("Agg")
        scene = AnimScene()
        scene.setup(figsize=(8, 6), mode='export')
        scene.update(0.3, 0, 1.0)
        out = ANIM_DIR / "output"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "_test_frame.png"
        scene.fig.savefig(str(path), dpi=100)
        assert path.exists()
        assert path.stat().st_size > 10000, f"PNG too small: {path.stat().st_size}"
        path.unlink()  # очистка
        plt.close(scene.fig)
        print("  [PASS] test_render_frame (PNG > 10KB)")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all([
        TestRingBuffer(),
        TestAnimSceneSetup(),
        TestAnimSceneUpdate(),
    ])
    runner.print_summary(results)
