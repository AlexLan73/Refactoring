"""
06_noise_montecarlo.py — Monte Carlo анализ с шумом
====================================================

Для фиксированных x0 и шагов добавляем шум к амплитудам:
A_noisy = A + N(0, sigma), sigma = snr * max(A).
M реализаций, статистика.

Результаты:
  results/noise_montecarlo.csv
  plots/2d/noise_error_vs_snr.png
  plots/2d/noise_std_vs_snr.png

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/06_noise_montecarlo.py
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

from common import sinc, ref_cg_2pt, ref_qa, ref_sd, select_top2, SD_COEFF_DEFAULT, COLORS, GRID_DEFAULT
from PyCore.runner import TestRunner

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

# Воспроизводимость
rng = np.random.default_rng(seed=42)

OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_PLOTS = ANALYSIS_DIR / "plots" / "2d"
OUT_RESULTS.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)


def ref_ea_fast(A, x):
    """EA без scipy — используем формулу из C-кода (ref_ea_c) для скорости."""
    from common import ref_ea_c
    xe, ok = ref_ea_c(float(A[0]), float(A[1]), float(A[2]),
                       float(x[0]), float(x[1]), float(x[2]))
    return xe


def run_montecarlo(snr_levels=None, x0_values=None, M=1000, grid=None):
    """Monte Carlo: M реализаций для каждого (snr, x0).

    Returns:
        list of dicts with results for each (snr, x0) combination
    """
    if snr_levels is None:
        snr_levels = [0.001, 0.01, 0.05, 0.1, 0.2]
    if x0_values is None:
        x0_values = [0.0, 0.1, 0.2, 0.3, 0.4]
    if grid is None:
        grid = GRID_DEFAULT

    results = []

    for snr in snr_levels:
        print(f"    SNR = {snr:.3f} ...", end="", flush=True)
        for x0 in x0_values:
            A_base = sinc(grid - x0)
            sigma = snr * np.max(A_base)
            noise = rng.normal(0, sigma, size=(M, 3))
            A_noisy = A_base[np.newaxis, :] + noise

            xe = {'cg': np.zeros(M), 'sd': np.zeros(M),
                  'qa': np.zeros(M), 'ea': np.zeros(M)}

            for i in range(M):
                A_row = A_noisy[i]

                # QA
                xe['qa'][i] = ref_qa(A_row, grid)

                # EA (быстрая версия через C-формулу)
                xe['ea'][i] = ref_ea_fast(A_row, grid)

                # CG, SD
                a1, a2, xx1, xx2 = select_top2(A_row, grid)
                xe['cg'][i] = ref_cg_2pt(a1, a2, xx1, xx2)
                xe['sd'][i] = ref_sd(SD_COEFF_DEFAULT, a1, a2, xx1, xx2)

            for m in ['cg', 'sd', 'qa', 'ea']:
                err = xe[m] - x0
                results.append({
                    'snr': snr, 'x0': x0, 'method': m,
                    'mean_err': float(np.mean(np.abs(err))),
                    'std_err': float(np.std(err)),
                    'p95_err': float(np.percentile(np.abs(err), 95)),
                    'bias': float(np.mean(err)),
                })
        print(" done")

    return results


def save_csv(results, path):
    """Сохранить результаты Monte Carlo в CSV."""
    # Группируем по (snr, x0) — одна строка с метриками всех методов
    from itertools import groupby

    header = ['snr', 'x0']
    for m in ['cg', 'sd', 'qa', 'ea']:
        header.extend([f'mean_{m}', f'std_{m}', f'p95_{m}', f'bias_{m}'])

    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join(header) + '\n')

        # Собираем по (snr, x0)
        key_data = {}
        for r in results:
            key = (r['snr'], r['x0'])
            if key not in key_data:
                key_data[key] = {}
            key_data[key][r['method']] = r

        for (snr, x0), methods in sorted(key_data.items()):
            row = [f"{snr:.6f}", f"{x0:.4f}"]
            for m in ['cg', 'sd', 'qa', 'ea']:
                d = methods.get(m, {})
                row.append(f"{d.get('mean_err', 0):.8f}")
                row.append(f"{d.get('std_err', 0):.8f}")
                row.append(f"{d.get('p95_err', 0):.8f}")
                row.append(f"{d.get('bias', 0):.8f}")
            f.write(','.join(row) + '\n')


def plot_error_vs_snr(results, x0_plot=0.2, path=None):
    """График: mean |error| vs SNR для x0=0.2."""
    fig, ax = plt.subplots(figsize=(14, 7))

    method_labels = {'cg': 'CG', 'sd': 'SD', 'qa': 'QA', 'ea': 'EA'}

    for m in ['cg', 'sd', 'qa', 'ea']:
        data = [r for r in results if r['method'] == m and abs(r['x0'] - x0_plot) < 0.001]
        snrs = [r['snr'] for r in data]
        maes = [r['mean_err'] for r in data]
        ax.plot(snrs, maes, 'o-', color=COLORS[method_labels[m]],
                linewidth=2, markersize=8, label=method_labels[m])

    ax.set_xlabel('SNR (sigma / A_max)', fontsize=12)
    ax.set_ylabel('Средняя абсолютная ошибка', fontsize=12)
    ax.set_title(f'Влияние шума на точность дискриминаторов (x0={x0_plot})', fontsize=14)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_std_vs_snr(results, x0_plot=0.2, path=None):
    """График: std vs SNR для x0=0.2."""
    fig, ax = plt.subplots(figsize=(14, 7))

    method_labels = {'cg': 'CG', 'sd': 'SD', 'qa': 'QA', 'ea': 'EA'}

    for m in ['cg', 'sd', 'qa', 'ea']:
        data = [r for r in results if r['method'] == m and abs(r['x0'] - x0_plot) < 0.001]
        snrs = [r['snr'] for r in data]
        stds = [r['std_err'] for r in data]
        ax.plot(snrs, stds, 'o-', color=COLORS[method_labels[m]],
                linewidth=2, markersize=8, label=method_labels[m])

    ax.set_xlabel('SNR (sigma / A_max)', fontsize=12)
    ax.set_ylabel('Std ошибки', fontsize=12)
    ax.set_title(f'Разброс ошибки vs шум (x0={x0_plot})', fontsize=14)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


class MonteCarloAnalysis:
    """Monte Carlo анализ с шумом."""

    def test_montecarlo(self):
        """M=1000 реализаций, 5 SNR x 5 x0."""
        print("\n  Monte Carlo: M=1000, 5 SNR levels, 5 x0 values")
        results = run_montecarlo(M=1000)

        # Таблица для x0=0.2
        print(f"\n  Results for x0=0.2:")
        print(f"  {'SNR':>8s} | {'MAE CG':>10s} | {'MAE QA':>10s} | {'MAE EA':>10s} | {'Std QA':>10s} | {'Std EA':>10s}")
        print(f"  {'-'*8}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        for snr in [0.001, 0.01, 0.05, 0.1, 0.2]:
            cg = [r for r in results if r['method'] == 'cg' and abs(r['snr'] - snr) < 0.0001 and abs(r['x0'] - 0.2) < 0.001]
            qa = [r for r in results if r['method'] == 'qa' and abs(r['snr'] - snr) < 0.0001 and abs(r['x0'] - 0.2) < 0.001]
            ea = [r for r in results if r['method'] == 'ea' and abs(r['snr'] - snr) < 0.0001 and abs(r['x0'] - 0.2) < 0.001]
            if cg and qa and ea:
                print(f"  {snr:8.3f} | {cg[0]['mean_err']:10.6f} | {qa[0]['mean_err']:10.6f} | "
                      f"{ea[0]['mean_err']:10.6f} | {qa[0]['std_err']:10.6f} | {ea[0]['std_err']:10.6f}")

        # H2: QA устойчивее EA к шуму при SNR=0.2
        qa_02 = [r for r in results if r['method'] == 'qa' and abs(r['snr'] - 0.2) < 0.001 and abs(r['x0'] - 0.2) < 0.001]
        ea_02 = [r for r in results if r['method'] == 'ea' and abs(r['snr'] - 0.2) < 0.001 and abs(r['x0'] - 0.2) < 0.001]
        if qa_02 and ea_02:
            h2 = qa_02[0]['std_err'] < ea_02[0]['std_err']
            h2_str = "CONFIRMED" if h2 else "REJECTED"
            print(f"\n  H2: QA more robust than EA at SNR=0.2?")
            print(f"    std_QA={qa_02[0]['std_err']:.6f}, std_EA={ea_02[0]['std_err']:.6f} → {h2_str}")

        # CSV
        csv_path = OUT_RESULTS / "noise_montecarlo.csv"
        save_csv(results, csv_path)
        print(f"\n  Saved: {csv_path}")

        # Графики
        p1 = OUT_PLOTS / "noise_error_vs_snr.png"
        plot_error_vs_snr(results, x0_plot=0.2, path=p1)
        print(f"  Saved: {p1}")

        p2 = OUT_PLOTS / "noise_std_vs_snr.png"
        plot_std_vs_snr(results, x0_plot=0.2, path=p2)
        print(f"  Saved: {p2}")

        print(f"  [OK] Monte Carlo complete")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(MonteCarloAnalysis())
    runner.print_summary(results)
