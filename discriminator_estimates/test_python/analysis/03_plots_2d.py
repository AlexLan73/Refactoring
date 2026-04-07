"""
03_plots_2d.py — 6 типов 2D графиков точности дискриминаторов
==============================================================

Графики по данным sweep_accuracy.csv:
  1. abs_error_vs_x0.png        — |ошибка| vs x0 (лог. Y)
  2. signed_error_vs_x0.png     — знаковая ошибка vs x0 (bias)
  3. ratio_xe_x0.png            — xe/x0 vs x0 (идеал = 1)
  4. sinc_animation_frames.png  — 9 кадров (3x3), sinc + оценки
  5. boxplot_by_zone.png        — box-plot по зонам
  6. error_histogram.png        — гистограмма ошибок

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/03_plots_2d.py
"""

import sys
import numpy as np
from pathlib import Path

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))

from common import sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, ref_auto, select_top2, GRID_DEFAULT, COLORS
from PyCore.runner import TestRunner

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

OUT_PLOTS = MODULE_DIR / "Doc" / "plots" / "2_no_noise"
OUT_PLOTS.mkdir(parents=True, exist_ok=True)
OUT_RESULTS = ANALYSIS_DIR / "results"


def load_sweep():
    """Загрузить sweep_accuracy.csv."""
    path = OUT_RESULTS / "sweep_accuracy.csv"
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for col in header:
            data[col] = []
        for line in f:
            vals = line.strip().split(',')
            for col, val in zip(header, vals):
                if col == 'zone':
                    data[col].append(val)
                elif col == 'is_monotonic':
                    data[col].append(bool(int(val)) if val else False)
                else:
                    data[col].append(float(val) if val else float('nan'))
    for col in header:
        if col not in ('zone',):
            data[col] = np.array(data[col])
    return data


def plot1_abs_error(data):
    """1. Абсолютная ошибка |xe - x0| vs x0 (лог. Y)."""
    x0 = data['x0']
    fig, ax = plt.subplots(figsize=(14, 8))

    for label, col in [('CG', 'err_cg'), ('SD', 'err_sd'), ('QA', 'err_qa'), ('EA', 'err_ea'), ('AUTO', 'err_auto')]:
        err = np.abs(data[col])
        err[err < 1e-15] = 1e-15
        ax.plot(x0, err, color=COLORS[label], linewidth=1.5, label=label, alpha=0.9)

    ax.set_yscale('log')
    # Границы зон — закрашенные полосы
    ax.axvspan(-1.5, -1.0, alpha=0.08, color='red')
    ax.axvspan(-1.0, -0.5, alpha=0.06, color='yellow')
    ax.axvspan(-0.5, 0.5, alpha=0.06, color='green')
    ax.axvspan(0.5, 1.0, alpha=0.06, color='yellow')
    ax.axvspan(1.0, 1.5, alpha=0.08, color='red')
    for xb in [-1.0, -0.5, 0.5, 1.0]:
        ax.axvline(xb, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)

    # Подписи зон вверху
    ylim = ax.get_ylim()
    yt = ylim[1] * 0.3
    ax.text(-1.25, yt, 'EXTREME\n(пик за сеткой)', ha='center', fontsize=8, color='#FF9999', style='italic')
    ax.text(-0.75, yt, 'BOUNDARY\n(пик у края)', ha='center', fontsize=8, color='#FFFF99', style='italic')
    ax.text(0.0, yt, 'NORMAL\n(рабочий режим)', ha='center', fontsize=8, color='#99FF99', style='italic')
    ax.text(0.75, yt, 'BOUNDARY\n(пик у края)', ha='center', fontsize=8, color='#FFFF99', style='italic')
    ax.text(1.25, yt, 'EXTREME\n(пик за сеткой)', ha='center', fontsize=8, color='#FF9999', style='italic')

    # Аннотации с пояснениями
    ax.annotate('EA и QA: ошибка < 1%\nшага сетки!',
                xy=(0, 0.005), fontsize=9, color='#99FF99',
                xytext=(0.3, 0.0005), arrowprops=dict(arrowstyle='->', color='#99FF99', lw=1),
                ha='left')
    ax.annotate('CG/SD: ~20% ошибка\n(используют только 2 точки)',
                xy=(0, 0.23), fontsize=9, color='#FF9999',
                xytext=(-1.4, 0.05), arrowprops=dict(arrowstyle='->', color='#FF9999', lw=1),
                ha='left')

    ax.set_xlabel('Истинное положение пика x0 (отсчёты сетки в {-1, 0, +1})', fontsize=12)
    ax.set_ylabel('Абсолютная ошибка |xe - x0| (логарифмическая шкала)', fontsize=12)
    ax.set_title('Точность дискриминаторов: чем ниже кривая — тем точнее метод', fontsize=14)
    ax.legend(fontsize=11, title='Метод (тип)', title_fontsize=10)
    ax.grid(True, alpha=0.3)

    path = OUT_PLOTS / "abs_error_vs_x0.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def plot2_signed_error(data):
    """2. Знаковая ошибка (xe - x0) vs x0."""
    x0 = data['x0']
    fig, ax = plt.subplots(figsize=(14, 7))

    for label, col in [('CG', 'err_cg'), ('SD', 'err_sd'), ('QA', 'err_qa'), ('EA', 'err_ea'), ('AUTO', 'err_auto')]:
        ax.plot(x0, data[col], color=COLORS[label], linewidth=1.5, label=label, alpha=0.9)

    ax.axhline(0, color='lime', linestyle='--', linewidth=1.5, alpha=0.7, label='Идеал: ошибка = 0')
    ax.set_xlabel('Истинное положение пика x0', fontsize=12)
    ax.set_ylabel('xe - x0 (положительное = завышает, отрицательное = занижает)', fontsize=12)
    ax.set_title('Систематическое смещение (bias): + значит "сдвигает оценку вправо"', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Пояснение
    ax.text(0.02, 0.02, 'QA и EA: bias ~ 0 (без систематической ошибки)\n'
            'CG и SD: сильный bias (тянут оценку к большему отсчёту)',
            transform=ax.transAxes, fontsize=9, color='#AAAAAA',
            verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7))

    path = OUT_PLOTS / "signed_error_vs_x0.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def plot3_ratio(data):
    """3. Отношение xe/x0 vs x0."""
    x0 = data['x0']
    mask = np.abs(x0) > 0.01  # исключить деление на ~0

    fig, ax = plt.subplots(figsize=(14, 7))

    for label, xe_col in [('CG', 'xe_cg'), ('SD', 'xe_sd'), ('QA', 'xe_qa'), ('EA', 'xe_ea'), ('AUTO', 'xe_auto')]:
        ratio = data[xe_col][mask] / x0[mask]
        ax.plot(x0[mask], ratio, color=COLORS[label], linewidth=1.5, label=label, alpha=0.9)

    ax.axhline(1.0, color='lime', linestyle='--', linewidth=1.5, alpha=0.7, label='Идеал: xe/x0 = 1.0')
    ax.axhspan(0.9, 1.1, alpha=0.05, color='green')  # ±10% зона
    ax.set_xlabel('Истинное положение пика x0', fontsize=12)
    ax.set_ylabel('xe / x0 (1.0 = идеально, >1 = завышает, <1 = занижает)', fontsize=12)
    ax.set_title('Линейность дискриминатора: насколько пропорциональна оценка?', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-2, 4)

    ax.text(0.02, 0.02, 'Зелёная полоса = допуск ±10%\n'
            'EA/QA: почти идеальны в normal зоне\n'
            'CG: всегда "недооценивает" (xe/x0 < 1)',
            transform=ax.transAxes, fontsize=9, color='#AAAAAA',
            verticalalignment='bottom',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7))

    path = OUT_PLOTS / "ratio_xe_x0.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def plot4_sinc_frames():
    """4. 9 кадров (3x3): sinc(x-x0) + оценки."""
    x0_values = [-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]
    x_fine = np.linspace(-3, 3, 500)
    grid = GRID_DEFAULT

    fig, axes = plt.subplots(3, 3, figsize=(14, 14))

    for idx, x0 in enumerate(x0_values):
        ax = axes[idx // 3, idx % 3]
        y = sinc(x_fine - x0)
        A = sinc(grid - x0)

        ax.plot(x_fine, y, 'c-', linewidth=1.5)
        ax.plot(grid, A, 'yo', markersize=10, zorder=5)

        # Оценки
        xe_qa = ref_qa(A, grid)
        xe_ea = ref_ea(A, grid)
        xe_at, mode_at = ref_auto(A, grid)
        a1, a2, xx1, xx2 = select_top2(A, grid)
        xe_cg = ref_cg_2pt(a1, a2, xx1, xx2)

        ax.axvline(x0, color='lime', linestyle=':', linewidth=1.5, alpha=0.7)
        ax.axvline(xe_cg, color=COLORS['CG'], linestyle='--', linewidth=1)
        ax.axvline(xe_qa, color=COLORS['QA'], linestyle='--', linewidth=1)
        ax.axvline(xe_ea, color=COLORS['EA'], linestyle='--', linewidth=1)
        ax.axvline(xe_at, color=COLORS['AUTO'], linestyle='-', linewidth=2, alpha=0.8)

        # Ошибки для подписи
        mode_names = {0: 'EA', 1: 'QA', 2: 'E2', 3: 'E2!'}
        err_at = abs(xe_at - x0)
        ax.set_title(f'x0={x0:.2f} | AUTO({mode_names[mode_at]})={err_at:.3f}',
                     fontsize=9, color=COLORS['AUTO'])
        ax.set_xlim(-3, 3)
        ax.set_ylim(-0.3, 1.1)
        ax.grid(True, alpha=0.2)

    # Общая легенда
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='lime', linestyle=':', label='Истинный пик'),
        Line2D([0], [0], color=COLORS['CG'], linestyle='--', label='CG'),
        Line2D([0], [0], color=COLORS['QA'], linestyle='--', label='QA'),
        Line2D([0], [0], color=COLORS['EA'], linestyle='--', label='EA'),
        Line2D([0], [0], color=COLORS['AUTO'], linestyle='-', linewidth=2, label='AUTO'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=11)
    fig.suptitle('Как дискриминаторы "следят" за пиком sinc(x) при его движении\n'
                 '(зелёная линия = истинный пик, цветные пунктиры = оценки методов)',
                 fontsize=13, y=0.99)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    path = OUT_PLOTS / "sinc_animation_frames.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def plot5_boxplot(data):
    """5. Box-plot ошибок по зонам."""
    fig, ax = plt.subplots(figsize=(14, 7))

    methods = ['CG', 'SD', 'QA', 'EA', 'AUTO']
    err_cols = {'CG': 'err_cg', 'SD': 'err_sd', 'QA': 'err_qa', 'EA': 'err_ea', 'AUTO': 'err_auto'}
    zones = ['normal', 'boundary', 'extreme']

    positions = []
    box_data = []
    colors_list = []
    tick_positions = []
    tick_labels = []

    for zi, zone in enumerate(zones):
        mask = np.array([z == zone for z in data['zone']])
        for mi, m in enumerate(methods):
            pos = zi * 6 + mi
            positions.append(pos)
            errs = np.abs(data[err_cols[m]][mask])
            box_data.append(errs[~np.isnan(errs)])
            colors_list.append(COLORS[m])
        tick_positions.append(zi * 6 + 2)
        tick_labels.append(zone)

    bp = ax.boxplot(box_data, positions=positions, widths=0.7,
                    patch_artist=True, showfliers=False)

    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticks(tick_positions)
    zone_labels = [
        'normal\n(|x0| < 0.5)\nрабочий режим',
        'boundary\n(0.5 < |x0| < 1.0)\nпик у края',
        'extreme\n(|x0| > 1.0)\nпик за сеткой'
    ]
    ax.set_xticklabels(zone_labels, fontsize=10)
    ax.set_ylabel('Абсолютная ошибка |xe - x0|', fontsize=12)
    ax.set_title('Распределение ошибок: ящик = 25%-75%, линия = медиана, усы = 1.5×IQR', fontsize=13)
    ax.grid(True, alpha=0.3, axis='y')

    # Легенда
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=COLORS[m], alpha=0.7,
                             label=f'{m} ({"2-точ." if m in ["CG","SD"] else "3-точ."})') for m in methods]
    ax.legend(handles=legend_elements, fontsize=11)

    ax.text(0.02, 0.97, 'В normal зоне QA/EA почти не видны — ошибка на порядок меньше CG/SD',
            transform=ax.transAxes, fontsize=9, color='#AAAAAA',
            verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))

    path = OUT_PLOTS / "boxplot_by_zone.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def plot6_histogram(data):
    """6. Гистограмма ошибок (2x2, по методу)."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    methods = [('CG', 'err_cg', axes[0, 0]),
               ('SD', 'err_sd', axes[0, 1]),
               ('QA', 'err_qa', axes[0, 2]),
               ('EA', 'err_ea', axes[1, 0]),
               ('AUTO', 'err_auto', axes[1, 1])]

    descriptions = {
        'CG': 'CG: широкое (2-точечный, грубый)',
        'SD': 'SD: похож на CG, чуть уже',
        'QA': 'QA: узкий + хвосты (extreme)',
        'EA': 'EA: самый узкий (лучший)',
        'AUTO': 'AUTO: EA+E2 (адаптивный!)',
    }
    # Скрыть пустой subplot
    axes[1, 2].set_visible(False)

    for label, col, ax in methods:
        errs = data[col]
        valid = ~np.isnan(errs)
        ax.hist(errs[valid], bins=50, color=COLORS[label], alpha=0.8, edgecolor='white', linewidth=0.3)
        ax.axvline(0, color='lime', linestyle='--', linewidth=1, alpha=0.5, label='Идеал (0)')
        ax.set_title(descriptions[label], fontsize=11, color=COLORS[label])
        ax.set_xlabel('xe - x0 (< 0 = занижает, > 0 = завышает)', fontsize=9)
        ax.set_ylabel('Количество случаев', fontsize=10)
        ax.grid(True, alpha=0.3)

    fig.suptitle('Гистограммы ошибок: узкий пик = точный метод, широкий = грубый', fontsize=13, y=1.01)
    fig.tight_layout()

    path = OUT_PLOTS / "error_histogram.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


class Plots2DAnalysis:
    """Генерация 6 типов 2D графиков."""

    def test_generate_all_2d(self):
        """Генерация всех 6 графиков."""
        data = load_sweep()
        n = len(data['x0'])
        print(f"\n  Loaded {n} rows from sweep_accuracy.csv")

        p1 = plot1_abs_error(data)
        print(f"  [1/6] {p1.name}")

        p2 = plot2_signed_error(data)
        print(f"  [2/6] {p2.name}")

        p3 = plot3_ratio(data)
        print(f"  [3/6] {p3.name}")

        p4 = plot4_sinc_frames()
        print(f"  [4/6] {p4.name}")

        p5 = plot5_boxplot(data)
        print(f"  [5/6] {p5.name}")

        p6 = plot6_histogram(data)
        print(f"  [6/6] {p6.name}")

        # Проверка
        files = list(OUT_PLOTS.glob("*.png"))
        # Учитываем что в 2d/ могут быть файлы от других скриптов
        my_files = [f for f in files if f.name in [
            'abs_error_vs_x0.png', 'signed_error_vs_x0.png', 'ratio_xe_x0.png',
            'sinc_animation_frames.png', 'boxplot_by_zone.png', 'error_histogram.png']]
        assert len(my_files) == 6, f"Expected 6 plot files, got {len(my_files)}"
        print(f"\n  [OK] All 6 2D plots generated in {OUT_PLOTS}")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(Plots2DAnalysis())
    runner.print_summary(results)
