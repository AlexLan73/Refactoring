"""
01_sweep_accuracy.py — Sweep пика sinc(x) по сетке + экстраполяция
===================================================================

Основной эксперимент: смещаем максимум sinc(x - x0) от x0 = -1.5 до +1.5
с шагом ~0.01 (301 точка). Для каждого x0 вычисляем оценки 4 методов
(CG, SD, QA, EA) + экстраполяцию для монотонных случаев.

Результаты:
  results/sweep_accuracy.csv  — основная таблица
  results/extrapolation.csv   — таблица экстраполяции (монотонные случаи)

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/01_sweep_accuracy.py
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

from common import (sinc, ref_cg_2pt, ref_qa, ref_ea, ref_sd, ref_ea_c,
                     ref_auto,
                     select_top2, is_monotonic, classify_zone,
                     extrap_parabolic, extrap_gaussian, extrap_gradient,
                     GRID_DEFAULT, SD_COEFF_DEFAULT)
from PyCore.runner import TestRunner

# --- Директории результатов ---
OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_RESULTS.mkdir(parents=True, exist_ok=True)


def run_sweep(n_points=301, x0_range=(-1.5, 1.5), grid=None, c_sd=SD_COEFF_DEFAULT):
    """Основной sweep: x0 от -1.5 до +1.5.

    Returns:
        dict с массивами: x0, xe_cg, xe_sd, xe_qa, xe_ea, err_*, zone, is_mono, ...
    """
    if grid is None:
        grid = GRID_DEFAULT
    x0_arr = np.linspace(x0_range[0], x0_range[1], n_points)

    # Массивы результатов
    xe_cg = np.full(n_points, np.nan)
    xe_sd = np.full(n_points, np.nan)
    xe_qa = np.full(n_points, np.nan)
    xe_ea = np.full(n_points, np.nan)
    xe_auto = np.full(n_points, np.nan)
    auto_mode = np.zeros(n_points, dtype=int)
    xe_e1 = np.full(n_points, np.nan)
    xe_e2 = np.full(n_points, np.nan)
    xe_e3 = np.full(n_points, np.nan)
    A1_arr = np.zeros(n_points)
    A2_arr = np.zeros(n_points)
    A3_arr = np.zeros(n_points)
    mono_arr = np.zeros(n_points, dtype=bool)
    zone_arr = np.empty(n_points, dtype='U10')

    for i, x0 in enumerate(x0_arr):
        # 3 отсчёта sinc(x - x0)
        A = sinc(grid - x0)
        A1_arr[i], A2_arr[i], A3_arr[i] = A[0], A[1], A[2]

        # Зона и монотонность
        zone_arr[i] = classify_zone(x0)
        mono = is_monotonic(A[0], A[1], A[2])
        mono_arr[i] = mono

        # 3-точечные: QA, EA
        xe_qa[i] = ref_qa(A, grid)
        xe_ea[i] = ref_ea(A, grid)

        # AUTO: автоматический дискриминатор
        xe_auto[i], auto_mode[i] = ref_auto(A, grid)

        # 2-точечные: CG, SD (выбор 2 из 3 по максимальным амплитудам)
        a1, a2, xx1, xx2 = select_top2(A, grid)
        xe_cg[i] = ref_cg_2pt(a1, a2, xx1, xx2)
        xe_sd[i] = ref_sd(c_sd, a1, a2, xx1, xx2)

        # Экстраполяция для монотонных случаев
        if mono:
            xe_e1[i] = extrap_parabolic(A[0], A[1], A[2],
                                        grid[0], grid[1], grid[2])
            xe_e2[i] = extrap_gaussian(A[0], A[1], A[2],
                                       grid[0], grid[1], grid[2])
            xe_e3[i] = extrap_gradient(A[0], A[1], A[2],
                                       grid[0], grid[1], grid[2])

    # Ошибки
    err_cg = xe_cg - x0_arr
    err_sd = xe_sd - x0_arr
    err_qa = xe_qa - x0_arr
    err_ea = xe_ea - x0_arr
    err_auto = xe_auto - x0_arr
    err_e1 = xe_e1 - x0_arr
    err_e2 = xe_e2 - x0_arr
    err_e3 = xe_e3 - x0_arr

    return {
        'x0': x0_arr, 'A1': A1_arr, 'A2': A2_arr, 'A3': A3_arr,
        'xe_cg': xe_cg, 'xe_sd': xe_sd, 'xe_qa': xe_qa, 'xe_ea': xe_ea,
        'xe_auto': xe_auto, 'auto_mode': auto_mode,
        'xe_e1': xe_e1, 'xe_e2': xe_e2, 'xe_e3': xe_e3,
        'err_cg': err_cg, 'err_sd': err_sd, 'err_qa': err_qa, 'err_ea': err_ea,
        'err_auto': err_auto,
        'err_e1': err_e1, 'err_e2': err_e2, 'err_e3': err_e3,
        'is_monotonic': mono_arr, 'zone': zone_arr,
    }


def run_sd_sweep(n_points=301, x0_range=(-1.5, 1.5)):
    """Sweep SD с разными коэффициентами c."""
    grid = GRID_DEFAULT
    x0_arr = np.linspace(x0_range[0], x0_range[1], n_points)
    c_values = [0.5, 1.0, 1.5, 2.0]
    sd_results = {}

    for c in c_values:
        xe = np.zeros(n_points)
        for i, x0 in enumerate(x0_arr):
            A = sinc(grid - x0)
            a1, a2, xx1, xx2 = select_top2(A, grid)
            xe[i] = ref_sd(c, a1, a2, xx1, xx2)
        key = f"xe_sd_c{int(c*10):02d}"
        sd_results[key] = xe
        sd_results[f"err_sd_c{int(c*10):02d}"] = xe - x0_arr

    return sd_results


def save_sweep_csv(data, sd_data, path):
    """Сохранить основную таблицу в CSV."""
    n = len(data['x0'])
    header = [
        'x0', 'A1', 'A2', 'A3',
        'xe_cg', 'xe_sd', 'xe_qa', 'xe_ea', 'xe_auto',
        'xe_e1', 'xe_e2', 'xe_e3',
        'err_cg', 'err_sd', 'err_qa', 'err_ea', 'err_auto',
        'err_e1', 'err_e2', 'err_e3',
        'auto_mode', 'is_monotonic', 'zone',
    ]
    # Добавляем SD с разными c
    sd_cols = sorted([k for k in sd_data if k.startswith('xe_sd_c')])
    sd_err_cols = sorted([k for k in sd_data if k.startswith('err_sd_c')])
    header.extend(sd_cols)
    header.extend(sd_err_cols)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join(header) + '\n')
        for i in range(n):
            row = [
                f"{data['x0'][i]:.6f}",
                f"{data['A1'][i]:.10f}",
                f"{data['A2'][i]:.10f}",
                f"{data['A3'][i]:.10f}",
                f"{data['xe_cg'][i]:.10f}",
                f"{data['xe_sd'][i]:.10f}",
                f"{data['xe_qa'][i]:.10f}",
                f"{data['xe_ea'][i]:.10f}",
                f"{data['xe_auto'][i]:.10f}",
                f"{data['xe_e1'][i]:.10f}" if not np.isnan(data['xe_e1'][i]) else '',
                f"{data['xe_e2'][i]:.10f}" if not np.isnan(data['xe_e2'][i]) else '',
                f"{data['xe_e3'][i]:.10f}" if not np.isnan(data['xe_e3'][i]) else '',
                f"{data['err_cg'][i]:.10f}",
                f"{data['err_sd'][i]:.10f}",
                f"{data['err_qa'][i]:.10f}",
                f"{data['err_ea'][i]:.10f}",
                f"{data['err_auto'][i]:.10f}",
                f"{data['err_e1'][i]:.10f}" if not np.isnan(data['err_e1'][i]) else '',
                f"{data['err_e2'][i]:.10f}" if not np.isnan(data['err_e2'][i]) else '',
                f"{data['err_e3'][i]:.10f}" if not np.isnan(data['err_e3'][i]) else '',
                str(int(data['auto_mode'][i])),
                '1' if data['is_monotonic'][i] else '0',
                data['zone'][i],
            ]
            for col in sd_cols + sd_err_cols:
                row.append(f"{sd_data[col][i]:.10f}")
            f.write(','.join(row) + '\n')


def save_extrapolation_csv(data, path):
    """Сохранить таблицу экстраполяции (только монотонные случаи)."""
    mask = data['is_monotonic']
    n = np.sum(mask)
    if n == 0:
        return

    header = ['x0', 'A1', 'A2', 'A3',
              'xe_e1', 'xe_e2', 'xe_e3',
              'err_e1', 'err_e2', 'err_e3', 'zone']

    with open(path, 'w', encoding='utf-8') as f:
        f.write(','.join(header) + '\n')
        for i in range(len(data['x0'])):
            if not mask[i]:
                continue
            row = [
                f"{data['x0'][i]:.6f}",
                f"{data['A1'][i]:.10f}",
                f"{data['A2'][i]:.10f}",
                f"{data['A3'][i]:.10f}",
                f"{data['xe_e1'][i]:.10f}" if not np.isnan(data['xe_e1'][i]) else '',
                f"{data['xe_e2'][i]:.10f}" if not np.isnan(data['xe_e2'][i]) else '',
                f"{data['xe_e3'][i]:.10f}" if not np.isnan(data['xe_e3'][i]) else '',
                f"{data['err_e1'][i]:.10f}" if not np.isnan(data['err_e1'][i]) else '',
                f"{data['err_e2'][i]:.10f}" if not np.isnan(data['err_e2'][i]) else '',
                f"{data['err_e3'][i]:.10f}" if not np.isnan(data['err_e3'][i]) else '',
                data['zone'][i],
            ]
            f.write(','.join(row) + '\n')


class SweepAnalysis:
    """Sweep x0 от -1.5 до +1.5 с сохранением результатов."""

    def test_sweep_basic(self):
        """Sweep: 301 точка, x0 = [-1.50, +1.50]."""
        print("\n  Sweep: 301 points, x0 = [-1.50, +1.50]")
        data = run_sweep(n_points=301)
        sd_data = run_sd_sweep(n_points=301)

        # Статистика
        n_mono = np.sum(data['is_monotonic'])
        n_total = len(data['x0'])
        print(f"  Monotonic cases: {n_mono}/{n_total} ({100*n_mono/n_total:.1f}%)")

        # E2 несходимость
        mono_mask = data['is_monotonic']
        e2_nan = np.sum(np.isnan(data['xe_e2'][mono_mask]))
        print(f"  E2 convergence failures: {e2_nan}/{n_mono} ({100*e2_nan/n_mono:.1f}%)")

        # Сохранить CSV
        csv_path = OUT_RESULTS / "sweep_accuracy.csv"
        save_sweep_csv(data, sd_data, csv_path)
        print(f"  Saved: {csv_path}")

        ext_path = OUT_RESULTS / "extrapolation.csv"
        save_extrapolation_csv(data, ext_path)
        print(f"  Saved: {ext_path}")

        # Проверка: при x0=0 3-точечные методы дают ≈ 0
        # 2-точечные (CG, SD) имеют bias из-за select_top2 — это нормально
        idx0 = n_total // 2  # центральная точка
        assert abs(data['x0'][idx0]) < 0.01
        for m in ['qa', 'ea']:
            err = abs(data[f'err_{m}'][idx0])
            assert err < 0.01, f"{m} at x0=0: err={err}"
        print(f"  [OK] x0=0: QA err={abs(data['err_qa'][idx0]):.6f}, "
              f"EA err={abs(data['err_ea'][idx0]):.6f}")
        print(f"         CG err={abs(data['err_cg'][idx0]):.6f} (2pt bias — expected), "
              f"SD err={abs(data['err_sd'][idx0]):.6f}")

        # AUTO статистика
        err_auto_abs = np.abs(data['err_auto'])
        mae_auto_all = np.mean(err_auto_abs)
        mae_auto_norm = np.mean(err_auto_abs[data['zone'] == 'normal'])
        mae_auto_mono = np.mean(err_auto_abs[mono_mask])
        modes = data['auto_mode']
        n_ea = np.sum(modes == 0)
        n_qa = np.sum(modes == 1)
        n_e2 = np.sum(modes == 2)
        n_e2f = np.sum(modes == 3)
        print(f"\n  AUTO: MAE(all)={mae_auto_all:.6f}, MAE(normal)={mae_auto_norm:.6f}, "
              f"MAE(mono)={mae_auto_mono:.6f}")
        print(f"  AUTO modes: EA={n_ea}, QA_fallback={n_qa}, E2={n_e2}, E2_fail={n_e2f}")

        # Проверка порядка точности при x0=0.2
        idx02 = np.argmin(np.abs(data['x0'] - 0.2))
        err_cg = abs(data['err_cg'][idx02])
        err_qa = abs(data['err_qa'][idx02])
        err_ea = abs(data['err_ea'][idx02])
        err_at = abs(data['err_auto'][idx02])
        print(f"  x0=0.2: CG={err_cg:.6f}, QA={err_qa:.6f}, EA={err_ea:.6f}, AUTO={err_at:.6f}")

        # SD с разными c
        print(f"\n  SD sweep with c = [0.5, 1.0, 1.5, 2.0]:")
        normal_mask = data['zone'] == 'normal'
        for c_val in [0.5, 1.0, 1.5, 2.0]:
            key = f"err_sd_c{int(c_val*10):02d}"
            mae = np.mean(np.abs(sd_data[key][normal_mask]))
            print(f"    c={c_val:.1f}: MAE(normal) = {mae:.6f}")

        self._data = data
        self._sd_data = sd_data

    def test_extrapolation_quality(self):
        """Проверка качества экстраполяции для монотонных случаев."""
        data = run_sweep(n_points=301)
        mono = data['is_monotonic']

        if not np.any(mono):
            print("  [WARN] No monotonic cases found")
            return

        # Сравнить E1, E2, E3
        for label, key in [('E1 parabolic', 'err_e1'),
                           ('E2 gaussian', 'err_e2'),
                           ('E3 gradient', 'err_e3')]:
            errs = np.abs(data[key][mono])
            valid = ~np.isnan(errs)
            if np.any(valid):
                mae = np.nanmean(errs[valid])
                max_err = np.nanmax(errs[valid])
                n_valid = np.sum(valid)
                print(f"  {label}: MAE={mae:.4f}, MaxErr={max_err:.4f} ({n_valid} valid)")
            else:
                print(f"  {label}: no valid results")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(SweepAnalysis())
    runner.print_summary(results)
