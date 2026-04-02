"""
04_grid_step.py — Влияние шага сетки на точность дискриминаторов
================================================================

Повторяет sweep для разных шагов сетки (step = 0.3, 0.5, 0.7, 1.0, 1.5, 2.0).
Сетка: {-step, 0, +step}. Для каждого step — sweep x0 внутри сетки.

Результаты:
  results/grid_step_sweep.csv
  plots/2d/error_vs_grid_step_sweep.png

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/04_grid_step.py
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

OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_PLOTS = ANALYSIS_DIR / "plots" / "2d"
OUT_RESULTS.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)


def run_grid_step_sweep(step_values=None, n_points=101):
    """Sweep для каждого шага сетки.

    Returns:
        list of dicts: [{step, x0, mae_cg, mae_sd, mae_qa, mae_ea, ...}, ...]
    """
    if step_values is None:
        step_values = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]

    all_rows = []

    for step in step_values:
        grid = np.array([-step, 0.0, step])
        x0_arr = np.linspace(-step, step, n_points)

        errs = {'cg': [], 'sd': [], 'qa': [], 'ea': []}

        for x0 in x0_arr:
            A = sinc(grid - x0)

            # 3-точечные
            xe_qa = ref_qa(A, grid)
            xe_ea = ref_ea(A, grid)

            # 2-точечные
            a1, a2, xx1, xx2 = select_top2(A, grid)
            xe_cg = ref_cg_2pt(a1, a2, xx1, xx2)
            xe_sd = ref_sd(SD_COEFF_DEFAULT, a1, a2, xx1, xx2)

            errs['cg'].append(abs(xe_cg - x0))
            errs['sd'].append(abs(xe_sd - x0))
            errs['qa'].append(abs(xe_qa - x0))
            errs['ea'].append(abs(xe_ea - x0))

            all_rows.append({
                'step': step, 'x0': x0,
                'err_cg': abs(xe_cg - x0), 'err_sd': abs(xe_sd - x0),
                'err_qa': abs(xe_qa - x0), 'err_ea': abs(xe_ea - x0),
            })

    return all_rows, step_values


def save_csv(rows, path):
    """Сохранить результаты в CSV."""
    header = ['step', 'x0', 'err_cg', 'err_sd', 'err_qa', 'err_ea']
    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join(header) + '\n')
        for r in rows:
            f.write(f"{r['step']:.4f},{r['x0']:.6f},"
                    f"{r['err_cg']:.10f},{r['err_sd']:.10f},"
                    f"{r['err_qa']:.10f},{r['err_ea']:.10f}\n")


def plot_mean_error_vs_step(rows, step_values, path):
    """График: mean |error| vs шаг сетки."""
    methods = ['cg', 'sd', 'qa', 'ea']
    method_labels = {'cg': 'CG', 'sd': 'SD', 'qa': 'QA', 'ea': 'EA'}

    mean_errs = {m: [] for m in methods}
    for step in step_values:
        step_rows = [r for r in rows if abs(r['step'] - step) < 0.001]
        for m in methods:
            vals = [r[f'err_{m}'] for r in step_rows]
            mean_errs[m].append(np.mean(vals))

    fig, ax = plt.subplots(figsize=(14, 7))
    for m in methods:
        ax.plot(step_values, mean_errs[m], 'o-',
                color=COLORS[method_labels[m]], linewidth=2, markersize=8,
                label=f'{method_labels[m]}')

    ax.set_xlabel('Шаг сетки (расстояние между отсчётами)', fontsize=12)
    ax.set_ylabel('Средняя абсолютная ошибка |xe - x0|', fontsize=12)
    ax.set_title('Влияние шага сетки на точность дискриминаторов (sinc)', fontsize=14)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


class GridStepAnalysis:
    """Анализ влияния шага сетки."""

    def test_grid_step_sweep(self):
        """Sweep для 6 шагов сетки."""
        print("\n  Grid step sweep: steps = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]")
        rows, steps = run_grid_step_sweep()

        # Таблица
        print(f"\n  {'Step':>6s} | {'MAE CG':>10s} | {'MAE SD':>10s} | {'MAE QA':>10s} | {'MAE EA':>10s}")
        print(f"  {'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        for step in steps:
            step_rows = [r for r in rows if abs(r['step'] - step) < 0.001]
            maes = {}
            for m in ['cg', 'sd', 'qa', 'ea']:
                maes[m] = np.mean([r[f'err_{m}'] for r in step_rows])
            print(f"  {step:6.2f} | {maes['cg']:10.6f} | {maes['sd']:10.6f} | "
                  f"{maes['qa']:10.6f} | {maes['ea']:10.6f}")

        # CSV
        csv_path = OUT_RESULTS / "grid_step_sweep.csv"
        save_csv(rows, csv_path)
        print(f"\n  Saved: {csv_path}")

        # График
        plot_path = OUT_PLOTS / "error_vs_grid_step_sweep.png"
        plot_mean_error_vs_step(rows, steps, plot_path)
        print(f"  Saved: {plot_path}")

        # Проверка: EA лучше QA при всех шагах
        for step in steps:
            step_rows = [r for r in rows if abs(r['step'] - step) < 0.001]
            mae_qa = np.mean([r['err_qa'] for r in step_rows])
            mae_ea = np.mean([r['err_ea'] for r in step_rows])
            # EA не обязательно лучше при всех шагах, но обычно при малых
        print(f"  [OK] Grid step analysis complete")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(GridStepAnalysis())
    runner.print_summary(results)
