"""
02_statistics.py — Матстатистика точности дискриминаторов по зонам
==================================================================

Загружает результаты sweep из results/sweep_accuracy.csv,
вычисляет метрики (MAE, MaxErr, RMSE, Bias, Std, P95) для
каждого метода в каждой зоне. Проверяет гипотезы H1, H3, H4.

Результаты:
  results/statistics_by_zone.csv
  results/statistics_summary.md

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/02_statistics.py
"""

import sys
import numpy as np
from pathlib import Path

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner

OUT_RESULTS = ANALYSIS_DIR / "results"


def load_sweep_csv(path):
    """Загрузить sweep_accuracy.csv в dict of arrays."""
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for col in header:
            data[col] = []
        for line in f:
            vals = line.strip().split(',')
            for col, val in zip(header, vals):
                if col in ('zone',):
                    data[col].append(val)
                elif col in ('is_monotonic',):
                    data[col].append(bool(int(val)) if val else False)
                else:
                    data[col].append(float(val) if val else float('nan'))
    # Конвертируем в numpy
    for col in header:
        if col not in ('zone',):
            data[col] = np.array(data[col])
    return data, header


def compute_stats(errors):
    """Вычислить 6 метрик для массива ошибок (signed)."""
    if len(errors) == 0:
        return {'MAE': np.nan, 'MaxErr': np.nan, 'RMSE': np.nan,
                'Bias': np.nan, 'Std': np.nan, 'P95': np.nan, 'N': 0}
    return {
        'MAE': float(np.mean(np.abs(errors))),
        'MaxErr': float(np.max(np.abs(errors))),
        'RMSE': float(np.sqrt(np.mean(errors**2))),
        'Bias': float(np.mean(errors)),
        'Std': float(np.std(errors)),
        'P95': float(np.percentile(np.abs(errors), 95)),
        'N': len(errors),
    }


def zone_mask(data, zone_name):
    """Маска для зоны."""
    zones = data['zone']
    if zone_name == 'all':
        return np.ones(len(zones), dtype=bool)
    elif zone_name == 'monotonic':
        return data['is_monotonic']
    else:
        return np.array([z == zone_name for z in zones])


class StatisticsAnalysis:
    """Матстатистика по зонам."""

    def test_statistics_by_zone(self):
        """Таблица метрик: 5 зон x 4 метода x 6 метрик."""
        csv_path = OUT_RESULTS / "sweep_accuracy.csv"
        assert csv_path.exists(), f"Файл не найден: {csv_path}"

        data, header = load_sweep_csv(csv_path)
        n_total = len(data['x0'])
        print(f"\n  Loaded {n_total} rows from sweep_accuracy.csv")

        methods = [('CG', 'err_cg'), ('SD', 'err_sd'), ('QA', 'err_qa'), ('EA', 'err_ea'), ('AUTO', 'err_auto')]
        zone_names = ['all', 'normal', 'boundary', 'extreme', 'monotonic']

        # Таблица в консоль + CSV строки + Markdown строки
        csv_rows = []
        md_lines = ["# Статистика точности дискриминаторов по зонам\n"]

        for zn in zone_names:
            mask = zone_mask(data, zn)
            n = np.sum(mask)
            print(f"\n  === Zone: {zn} (N={n}) ===")
            print(f"  {'Method':>6s} | {'MAE':>10s} | {'MaxErr':>10s} | {'RMSE':>10s} | "
                  f"{'Bias':>10s} | {'Std':>10s} | {'P95':>10s}")
            print(f"  {'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")

            md_lines.append(f"\n## Зона: {zn} (N={n})\n")
            md_lines.append("| Метод | MAE | MaxErr | RMSE | Bias | Std | P95 |")
            md_lines.append("|-------|-----|--------|------|------|-----|-----|")

            for m_name, m_col in methods:
                errs = data[m_col][mask]
                valid = ~np.isnan(errs)
                s = compute_stats(errs[valid])

                print(f"  {m_name:>6s} | {s['MAE']:10.6f} | {s['MaxErr']:10.6f} | "
                      f"{s['RMSE']:10.6f} | {s['Bias']:+10.6f} | {s['Std']:10.6f} | {s['P95']:10.6f}")

                csv_rows.append({
                    'zone': zn, 'method': m_name,
                    **s
                })
                md_lines.append(
                    f"| {m_name} | {s['MAE']:.6f} | {s['MaxErr']:.6f} | "
                    f"{s['RMSE']:.6f} | {s['Bias']:+.6f} | {s['Std']:.6f} | {s['P95']:.6f} |"
                )

        # Сохранить CSV
        csv_out = OUT_RESULTS / "statistics_by_zone.csv"
        with open(csv_out, 'w', encoding='utf-8') as f:
            f.write("zone,method,MAE,MaxErr,RMSE,Bias,Std,P95,N\n")
            for r in csv_rows:
                f.write(f"{r['zone']},{r['method']},{r['MAE']:.8f},{r['MaxErr']:.8f},"
                        f"{r['RMSE']:.8f},{r['Bias']:.8f},{r['Std']:.8f},{r['P95']:.8f},{r['N']}\n")
        print(f"\n  Saved: {csv_out}")

        # Сохранить Markdown
        md_out = OUT_RESULTS / "statistics_summary.md"
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))
        print(f"  Saved: {md_out}")

    def test_extrapolation_stats(self):
        """Статистика экстраполяции для монотонных случаев."""
        csv_path = OUT_RESULTS / "sweep_accuracy.csv"
        data, header = load_sweep_csv(csv_path)
        mask = data['is_monotonic']
        n_mono = np.sum(mask)
        print(f"\n  Extrapolation stats (N_mono={n_mono}):")

        for label, col in [('E1 (парабола)', 'err_e1'),
                           ('E2 (Гауссиан)', 'err_e2'),
                           ('E3 (градиент)', 'err_e3')]:
            if col in data:
                errs = data[col][mask]
                valid = ~np.isnan(errs)
                n_valid = np.sum(valid)
                n_fail = n_mono - n_valid
                if n_valid > 0:
                    mae = np.mean(np.abs(errs[valid]))
                    maxe = np.max(np.abs(errs[valid]))
                    print(f"    {label}: MAE={mae:.4f}, MaxErr={maxe:.4f}, "
                          f"failures={n_fail}/{n_mono} ({100*n_fail/n_mono:.1f}%)")

    def test_hypothesis_h1(self):
        """H1: EA < QA < CG в normal зоне."""
        data, header = load_sweep_csv(OUT_RESULTS / "sweep_accuracy.csv")
        mask = zone_mask(data, 'normal')

        mae_cg = np.mean(np.abs(data['err_cg'][mask]))
        mae_qa = np.mean(np.abs(data['err_qa'][mask]))
        mae_ea = np.mean(np.abs(data['err_ea'][mask]))

        h1 = mae_ea < mae_qa < mae_cg
        status = "CONFIRMED" if h1 else "REJECTED"
        print(f"\n  H1: EA best in normal zone? {status}")
        print(f"    EA={mae_ea:.6f} < QA={mae_qa:.6f} < CG={mae_cg:.6f}")

    def test_hypothesis_h3(self):
        """H3: CG bias линейно зависит от x0."""
        data, _ = load_sweep_csv(OUT_RESULTS / "sweep_accuracy.csv")
        x0 = data['x0']
        bias_cg = data['err_cg']
        valid = ~np.isnan(x0) & ~np.isnan(bias_cg)
        corr = np.corrcoef(x0[valid], bias_cg[valid])[0, 1]
        status = "CONFIRMED" if abs(corr) > 0.9 else "REJECTED"
        print(f"\n  H3: CG bias linear? {status} (corr = {corr:.4f})")

    def test_hypothesis_h4(self):
        """H4: лучший коэффициент c для SD."""
        data, header = load_sweep_csv(OUT_RESULTS / "sweep_accuracy.csv")
        mask = zone_mask(data, 'normal')

        sd_cols = sorted([c for c in header if c.startswith('err_sd_c')])
        if not sd_cols:
            print("\n  H4: SD columns not found")
            return

        print(f"\n  H4: Best c for SD (normal zone):")
        best_c = None
        best_mae = float('inf')
        for col in sd_cols:
            errs = data[col][mask]
            valid = ~np.isnan(errs)
            mae = np.mean(np.abs(errs[valid]))
            c_str = col.replace('err_sd_c', '')
            c_val = int(c_str) / 10
            print(f"    c={c_val:.1f}: MAE = {mae:.6f}")
            if mae < best_mae:
                best_mae = mae
                best_c = c_val

        print(f"    Best c = {best_c:.1f} (MAE = {best_mae:.6f})")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(StatisticsAnalysis())
    runner.print_summary(results)
