"""
05_plots_3d.py — 3D графики: surface, heatmap, contour
========================================================

Визуализация зависимости ошибки от двух параметров (x0, step).

Результаты:
  plots/3d/surface_error_{method}.png  (4 файла)
  plots/3d/heatmap_error_{method}.png  (4 файла)
  plots/3d/contour_error_{method}.png  (4 файла)
  plots/3d/surface_all_methods.png     (1 файл)

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/05_plots_3d.py
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

from common import sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, select_top2, SD_COEFF_DEFAULT, COLORS
from PyCore.runner import TestRunner

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

OUT_PLOTS = MODULE_DIR / "Doc" / "plots" / "4_3d"
OUT_PLOTS.mkdir(parents=True, exist_ok=True)

METHODS_MAP = {'CG': 'cg', 'SD': 'sd', 'QA': 'qa', 'EA': 'ea'}


def generate_error_grid(step_values=None, n_x0=51):
    """Генерировать 2D сетку ошибок (x0 vs step) для всех 4 методов.

    Returns:
        step_arr, x0_norm_arr, errors dict {method: 2D array}
    """
    if step_values is None:
        step_values = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 2.0])

    # Нормализованный x0: от -1 до +1 (в долях шага)
    x0_norm = np.linspace(-0.95, 0.95, n_x0)

    errors = {m: np.zeros((len(step_values), n_x0)) for m in ['cg', 'sd', 'qa', 'ea']}

    for si, step in enumerate(step_values):
        grid = np.array([-step, 0.0, step])
        for xi, x0n in enumerate(x0_norm):
            x0 = x0n * step
            A = sinc(grid - x0)

            # QA, EA
            xe_qa = ref_qa(A, grid)
            xe_ea = ref_ea(A, grid)

            # CG, SD
            a1, a2, xx1, xx2 = select_top2(A, grid)
            xe_cg = ref_cg_2pt(a1, a2, xx1, xx2)
            xe_sd = ref_sd(SD_COEFF_DEFAULT, a1, a2, xx1, xx2)

            errors['cg'][si, xi] = abs(xe_cg - x0)
            errors['sd'][si, xi] = abs(xe_sd - x0)
            errors['qa'][si, xi] = abs(xe_qa - x0)
            errors['ea'][si, xi] = abs(xe_ea - x0)

    return step_values, x0_norm, errors


def plot_surface(step_arr, x0_norm, errors, method, label, path):
    """Surface plot для одного метода."""
    X, Y = np.meshgrid(x0_norm, step_arr)
    Z = errors[method]

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85, edgecolor='none')

    ax.set_xlabel('x0 / step (норм.)', fontsize=11)
    ax.set_ylabel('Шаг сетки', fontsize=11)
    ax.set_zlabel('|ошибка|', fontsize=11)
    ax.set_title(f'Surface: {label}', fontsize=14)
    fig.colorbar(surf, shrink=0.5, label='|error|')

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_heatmap(step_arr, x0_norm, errors, method, label, path):
    """Heatmap: log10(|error|)."""
    Z = errors[method].copy()
    Z[Z < 1e-15] = 1e-15
    Z_log = np.log10(Z)

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.pcolormesh(x0_norm, step_arr, Z_log, cmap='viridis', shading='auto')
    ax.set_xlabel('x0 / step (норм.)', fontsize=12)
    ax.set_ylabel('Шаг сетки', fontsize=12)
    ax.set_title(f'Heatmap log₁₀|ошибка|: {label}', fontsize=14)
    cb = fig.colorbar(im, label='log₁₀|error|')

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_contour(step_arr, x0_norm, errors, method, label, path):
    """Contour plot."""
    Z = errors[method]
    levels = [0.001, 0.01, 0.05, 0.1, 0.2, 0.5]

    fig, ax = plt.subplots(figsize=(14, 7))
    cs = ax.contour(x0_norm, step_arr, Z, levels=levels, colors='white', linewidths=1.5)
    ax.clabel(cs, fmt='%.3f', fontsize=9)
    cf = ax.contourf(x0_norm, step_arr, Z, levels=20, cmap='viridis', alpha=0.8)
    fig.colorbar(cf, label='|error|')

    ax.set_xlabel('x0 / step (норм.)', fontsize=12)
    ax.set_ylabel('Шаг сетки', fontsize=12)
    ax.set_title(f'Contour: {label}', fontsize=14)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_surface_all(step_arr, x0_norm, errors, path):
    """Сводный 2x2: surface для всех 4 методов."""
    X, Y = np.meshgrid(x0_norm, step_arr)

    fig = plt.figure(figsize=(16, 14))
    methods = [('cg', 'CG'), ('sd', 'SD'), ('qa', 'QA'), ('ea', 'EA')]

    # Общая шкала
    vmax = max(np.max(errors[m]) for m, _ in methods)

    for idx, (m, label) in enumerate(methods):
        ax = fig.add_subplot(2, 2, idx + 1, projection='3d')
        Z = errors[m]
        ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85, edgecolor='none',
                        vmin=0, vmax=vmax)
        ax.set_xlabel('x0/step', fontsize=9)
        ax.set_ylabel('step', fontsize=9)
        ax.set_zlabel('|err|', fontsize=9)
        ax.set_title(label, fontsize=13, color=COLORS[label])

    fig.suptitle('Ошибка дискриминаторов: x0 vs шаг сетки', fontsize=15, y=0.98)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


class Plots3DAnalysis:
    """Генерация 3D графиков."""

    def test_generate_all_3d(self):
        """Генерация всех 3D графиков (surface + heatmap + contour)."""
        print("\n  Generating error grid...")
        step_arr, x0_norm, errors = generate_error_grid()
        print(f"  Grid: {len(step_arr)} steps x {len(x0_norm)} x0 points")

        methods = [('cg', 'CG'), ('sd', 'SD'), ('qa', 'QA'), ('ea', 'EA')]
        n_files = 0

        for m, label in methods:
            # Surface
            p = OUT_PLOTS / f"surface_error_{m}.png"
            plot_surface(step_arr, x0_norm, errors, m, label, p)
            n_files += 1

            # Heatmap
            p = OUT_PLOTS / f"heatmap_error_{m}.png"
            plot_heatmap(step_arr, x0_norm, errors, m, label, p)
            n_files += 1

            # Contour
            p = OUT_PLOTS / f"contour_error_{m}.png"
            plot_contour(step_arr, x0_norm, errors, m, label, p)
            n_files += 1

        # Summary 2x2
        p = OUT_PLOTS / "surface_all_methods.png"
        plot_surface_all(step_arr, x0_norm, errors, p)
        n_files += 1

        print(f"  Generated {n_files} PNG files in {OUT_PLOTS}")

        # Проверка
        files = list(OUT_PLOTS.glob("*.png"))
        assert len(files) >= 13, f"Expected >= 13 files, got {len(files)}"
        print(f"  [OK] {len(files)} files in plots/3d/")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(Plots3DAnalysis())
    runner.print_summary(results)
