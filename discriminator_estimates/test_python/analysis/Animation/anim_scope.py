"""
anim_scope.py — Осциллограф: sinc + 4 канала scope ошибок.

Layout:
  - Верхний: sinc(x-x0) + 3 точки + оценки (компактный)
  - 4 канала: CG, QA, EA, AUTO — бегущие линии ошибок
  - Кнопки Play/Pause внизу

Запуск:
    cd discriminator_estimates/test_python
    python analysis/Animation/anim_scope.py
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
from pathlib import Path

# --- Пути ---
ANIM_DIR     = Path(__file__).resolve().parent
ANALYSIS_DIR = ANIM_DIR.parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent
REPO_ROOT    = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))
sys.path.insert(0, str(ANIM_DIR))

from anim_core import AnimScene, RingBuffer, METHODS, INTERVAL_MS, FPS
from common import sinc, COLORS


def main():
    # --- Собственный layout (НЕ через AnimScene.setup mode='scope') ---
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(nrows=8, ncols=1, hspace=0.4)

    ax_sinc = fig.add_subplot(gs[0:2, 0])
    ax_cg   = fig.add_subplot(gs[2, 0])
    ax_qa   = fig.add_subplot(gs[3, 0])
    ax_ea   = fig.add_subplot(gs[4, 0])
    ax_auto = fig.add_subplot(gs[5, 0])
    ax_info = fig.add_subplot(gs[6, 0])
    # gs[7] — кнопки

    scope_axes = {'CG': ax_cg, 'QA': ax_qa, 'EA': ax_ea, 'AUTO': ax_auto}

    # --- Настроить AnimScene вручную (используем для вычислений) ---
    scene = AnimScene()
    # Ручной setup — минимум для вычислений и sinc-графика
    scene.fig = fig
    scene.ax_main = ax_sinc
    scene.x_fine = np.linspace(-4, 4, 500)
    scene.rng = np.random.default_rng(seed=42)
    scene.history = {m: RingBuffer(200) for m in METHODS}
    scene._dynamic_xlim = False

    # --- Artists на ax_sinc (компактный sinc-график) ---
    y_init = sinc(scene.x_fine)
    scene.line_sinc = ax_sinc.plot(
        scene.x_fine, y_init, color='#00BFFF', lw=1.5)[0]

    init_grid = np.array([-1.0, 0.0, 1.0])
    init_A = sinc(init_grid)
    scene.scatter_pts = ax_sinc.scatter(
        init_grid, init_A, c='#FFE66D', s=80, zorder=5)

    scene.vline_true = ax_sinc.axvline(0, color='lime', ls=':', lw=1.5, zorder=3)
    scene.vlines = {}
    for m in METHODS:
        scene.vlines[m] = ax_sinc.axvline(
            0, color=COLORS[m], ls='--', lw=1.0 if m != 'AUTO' else 2.0, zorder=4)

    scene.zone_bg = ax_sinc.axvspan(-4, 4, alpha=0.04, color='green', zorder=0)
    scene.text_info = ax_sinc.text(
        0.02, 0.95, '', transform=ax_sinc.transAxes,
        va='top', ha='left', color='white', fontsize=8,
        fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.6))

    ax_sinc.set_xlim(-4, 4)
    ax_sinc.set_ylim(-0.3, 1.15)
    ax_sinc.set_title('Discriminator Scope', fontsize=10)
    ax_sinc.grid(True, alpha=0.2)

    # --- Создать bar chart фиктивный (нужен для scene.update) ---
    # Вместо отдельного ax_bar используем ax_info
    scene.ax_bar = ax_info
    scene.bars = ax_info.barh(METHODS, [0]*4,
                               color=[COLORS[m] for m in METHODS], height=0.6)
    scene.bars_text = []
    for i, m in enumerate(METHODS):
        t = ax_info.text(0.01, i, '', va='center', ha='left',
                         color='white', fontsize=8, fontweight='bold')
        scene.bars_text.append(t)
    ax_info.set_xlim(0, 1.0)
    ax_info.set_xlabel('|error|', fontsize=8)
    ax_info.tick_params(labelsize=7)

    # --- Scope каналы ---
    scope_ylims = {'CG': (0, 1.0), 'QA': (0, 0.5), 'EA': (0, 0.5), 'AUTO': (0, 0.5)}
    scope_lines = {}
    x_scope = np.arange(200)

    for m in METHODS:
        ax = scope_axes[m]
        line, = ax.plot(x_scope, np.full(200, np.nan),
                        color=COLORS[m], lw=1.0)
        scope_lines[m] = line
        ax.set_ylim(scope_ylims[m])
        ax.set_xlim(0, 200)
        ax.set_ylabel(m, color=COLORS[m], fontsize=9, fontweight='bold')
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.15)
        # Убрать x-метки кроме нижнего
        if m != 'AUTO':
            ax.set_xticklabels([])

    ax_auto.set_xlabel('Samples', fontsize=8)

    # --- Sweep данные ---
    x0_arr = np.linspace(-1.5, 1.5, 301)

    # --- FuncAnimation ---
    def update(frame):
        x0 = x0_arr[frame % len(x0_arr)]
        artists = scene.update(x0, 0, 1.0)
        # Обновить scope линии из history
        for m in METHODS:
            scope_lines[m].set_ydata(scene.history[m].get_ordered())
        return artists + list(scope_lines.values())

    anim = FuncAnimation(fig, update, frames=len(x0_arr),
                         interval=INTERVAL_MS, blit=False, repeat=True)

    # --- Кнопки Play/Pause ---
    ax_btn_play  = fig.add_axes([0.30, 0.01, 0.15, 0.03])
    ax_btn_pause = fig.add_axes([0.55, 0.01, 0.15, 0.03])

    btn_play  = Button(ax_btn_play,  '\u25b6 Play')
    btn_pause = Button(ax_btn_pause, '\u23f8 Pause')

    def on_play(event):
        anim.resume()

    def on_pause(event):
        anim.pause()

    btn_play.on_clicked(on_play)
    btn_pause.on_clicked(on_pause)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.show()


if __name__ == "__main__":
    main()
