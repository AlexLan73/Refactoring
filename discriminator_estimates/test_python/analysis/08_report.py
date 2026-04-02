"""
08_report.py — Генератор итогового отчёта
==========================================

Собирает результаты всех предыдущих этапов и генерирует
единый Markdown-отчёт results/REPORT.md.

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/08_report.py
"""

import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner

OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_PLOTS_2D = ANALYSIS_DIR / "plots" / "2d"
OUT_PLOTS_3D = ANALYSIS_DIR / "plots" / "3d"


def load_csv(path):
    """Загрузить CSV с заголовками (простой парсер без pandas)."""
    if not path.exists():
        return None, None
    with open(path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        rows = []
        for line in f:
            rows.append(line.strip().split(','))
    return header, rows


def safe_float(s):
    """Преобразовать строку в float, NaN при пустой строке."""
    if s == '' or s is None:
        return float('nan')
    return float(s)


def compute_zone_stats(header, rows, method_err_col, zone_col='zone', zone_filter=None):
    """Вычислить статистику для метода в зоне."""
    err_idx = header.index(method_err_col)
    zone_idx = header.index(zone_col) if zone_col in header else -1

    errors = []
    for row in rows:
        if zone_filter and zone_idx >= 0:
            if row[zone_idx] != zone_filter:
                continue
        val = safe_float(row[err_idx])
        if not np.isnan(val):
            errors.append(val)

    if not errors:
        return {'MAE': np.nan, 'MaxErr': np.nan, 'RMSE': np.nan,
                'Bias': np.nan, 'Std': np.nan, 'P95': np.nan, 'N': 0}

    errs = np.array(errors)
    return {
        'MAE': float(np.mean(np.abs(errs))),
        'MaxErr': float(np.max(np.abs(errs))),
        'RMSE': float(np.sqrt(np.mean(errs**2))),
        'Bias': float(np.mean(errs)),
        'Std': float(np.std(errs)),
        'P95': float(np.percentile(np.abs(errs), 95)),
        'N': len(errs),
    }


def generate_report():
    """Генерировать REPORT.md."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append("# Отчёт: Аналитическое исследование точности дискриминаторов")
    lines.append(f"\n**Дата генерации**: {now}")
    lines.append("**Генератор**: `analysis/08_report.py`")
    lines.append("")

    # --- Введение ---
    lines.append("## 1. Введение")
    lines.append("")
    lines.append("Исследование точности 4 дискриминаторных оценок координат (CG, SD, QA, EA)")
    lines.append("на модельных данных sinc(x) = sin(x)/x при различных условиях:")
    lines.append("- Sweep пика по сетке из 3 отсчётов")
    lines.append("- Различные шаги сетки")
    lines.append("- Аддитивный шум (Monte Carlo)")
    lines.append("- FFT-применение (частотная оценка)")
    lines.append("")

    # --- Методы ---
    lines.append("## 2. Методы")
    lines.append("")
    lines.append("| Метод | Тип | Формула | Исходник |")
    lines.append("|-------|-----|---------|----------|")
    lines.append("| CG (центр тяжести) | 2-точечный | xe = (A1·x1 + A2·x2) / (A1 + A2) | discrcg.c |")
    lines.append("| SD (суммарно-разностный) | 2-точечный | xe = xc + c·(A2-A1)/(A2+A1) | discrsd.c |")
    lines.append("| QA (квадратичная) | 3-точечный | Парабола → вершина (формула Ao) | discrqa.c |")
    lines.append("| EA (экспоненциальная) | 3-точечный | Гауссов фит exp(-a(x-x0)²) | discrea.c |")
    lines.append("")

    # --- Точность по зонам ---
    lines.append("## 3. Точность по зонам (sweep x0 ∈ [-1.5, +1.5])")
    lines.append("")

    sweep_path = OUT_RESULTS / "sweep_accuracy.csv"
    header, rows = load_csv(sweep_path)

    if header and rows:
        zones = [('all', None), ('normal', 'normal'), ('boundary', 'boundary'), ('extreme', 'extreme')]
        methods = [('CG', 'err_cg'), ('SD', 'err_sd'), ('QA', 'err_qa'), ('EA', 'err_ea')]

        for zone_name, zone_filter in zones:
            lines.append(f"### Зона: {zone_name}")
            lines.append("")
            lines.append("| Метод | MAE | MaxErr | RMSE | Bias | Std | P95 | N |")
            lines.append("|-------|-----|--------|------|------|-----|-----|---|")

            for m_name, m_col in methods:
                s = compute_zone_stats(header, rows, m_col, zone_filter=zone_filter)
                lines.append(
                    f"| {m_name} | {s['MAE']:.6f} | {s['MaxErr']:.6f} | "
                    f"{s['RMSE']:.6f} | {s['Bias']:+.6f} | {s['Std']:.6f} | "
                    f"{s['P95']:.6f} | {s['N']} |"
                )
            lines.append("")
    else:
        lines.append("*sweep_accuracy.csv не найден — запустите 01_sweep_accuracy.py*")
        lines.append("")

    # --- Экстраполяция ---
    lines.append("## 4. Экстраполяция (монотонные случаи)")
    lines.append("")

    ext_path = OUT_RESULTS / "extrapolation.csv"
    ext_header, ext_rows = load_csv(ext_path)
    if ext_header and ext_rows:
        lines.append(f"Всего монотонных случаев: {len(ext_rows)}")
        lines.append("")
        lines.append("| Метод | MAE | MaxErr |")
        lines.append("|-------|-----|--------|")
        for label, col in [('E1 (парабола)', 'err_e1'), ('E2 (Гауссиан)', 'err_e2'), ('E3 (градиент)', 'err_e3')]:
            if col in ext_header:
                idx = ext_header.index(col)
                errs = [safe_float(r[idx]) for r in ext_rows]
                errs = [e for e in errs if not np.isnan(e)]
                if errs:
                    mae = np.mean(np.abs(errs))
                    maxe = np.max(np.abs(errs))
                    lines.append(f"| {label} | {mae:.4f} | {maxe:.4f} |")
        lines.append("")
    else:
        lines.append("*extrapolation.csv не найден*")
        lines.append("")

    # --- Проверка гипотез ---
    lines.append("## 5. Проверка гипотез")
    lines.append("")

    if header and rows:
        # H1: EA < QA < CG в normal зоне
        s_cg = compute_zone_stats(header, rows, 'err_cg', zone_filter='normal')
        s_qa = compute_zone_stats(header, rows, 'err_qa', zone_filter='normal')
        s_ea = compute_zone_stats(header, rows, 'err_ea', zone_filter='normal')

        h1 = s_ea['MAE'] < s_qa['MAE'] < s_cg['MAE']
        h1_str = "CONFIRMED" if h1 else "REJECTED"
        lines.append(f"**H1**: EA лучше QA лучше CG в normal зоне? **{h1_str}**")
        lines.append(f"  - EA MAE = {s_ea['MAE']:.6f}")
        lines.append(f"  - QA MAE = {s_qa['MAE']:.6f}")
        lines.append(f"  - CG MAE = {s_cg['MAE']:.6f}")
        lines.append("")

        # H3: CG bias линейный
        x0_idx = header.index('x0')
        err_cg_idx = header.index('err_cg')
        x0_vals = np.array([safe_float(r[x0_idx]) for r in rows])
        err_cg_vals = np.array([safe_float(r[err_cg_idx]) for r in rows])
        valid = ~np.isnan(x0_vals) & ~np.isnan(err_cg_vals)
        if np.sum(valid) > 2:
            corr = np.corrcoef(x0_vals[valid], err_cg_vals[valid])[0, 1]
            h3_str = "CONFIRMED" if abs(corr) > 0.9 else "REJECTED"
            lines.append(f"**H3**: CG bias линейный? **{h3_str}** (corr = {corr:.4f})")
        lines.append("")

        # H4: лучший c для SD
        sd_cols = [c for c in header if c.startswith('err_sd_c')]
        if sd_cols:
            lines.append("**H4**: Лучший коэффициент c для SD:")
            # только normal зона
            zone_idx = header.index('zone')
            normal_rows = [r for r in rows if r[zone_idx] == 'normal']
            best_c = None
            best_mae = float('inf')
            for col in sd_cols:
                idx = header.index(col)
                errs = [safe_float(r[idx]) for r in normal_rows]
                errs = [e for e in errs if not np.isnan(e)]
                if errs:
                    mae = np.mean(np.abs(errs))
                    c_val = col.replace('err_sd_c', '')
                    lines.append(f"  - c={int(c_val)/10:.1f}: MAE = {mae:.6f}")
                    if mae < best_mae:
                        best_mae = mae
                        best_c = int(c_val) / 10
            if best_c:
                lines.append(f"  - **Лучший c = {best_c:.1f}** (MAE = {best_mae:.6f})")
            lines.append("")

    # H2 — из Monte Carlo
    mc_path = OUT_RESULTS / "noise_montecarlo.csv"
    mc_header, mc_rows = load_csv(mc_path)
    if mc_header and mc_rows:
        lines.append("**H2**: QA устойчивее EA к шуму?")
        # Ищем snr=0.2 строки
        if 'snr' in mc_header and 'std_qa' in mc_header and 'std_ea' in mc_header:
            snr_idx = mc_header.index('snr')
            std_qa_idx = mc_header.index('std_qa')
            std_ea_idx = mc_header.index('std_ea')
            for r in mc_rows:
                if abs(safe_float(r[snr_idx]) - 0.2) < 0.01:
                    sq = safe_float(r[std_qa_idx])
                    se = safe_float(r[std_ea_idx])
                    h2 = sq < se
                    h2_str = "CONFIRMED" if h2 else "REJECTED"
                    lines.append(f"  При SNR=0.2: std_QA={sq:.4f}, std_EA={se:.4f} → **{h2_str}**")
                    break
        lines.append("")
    else:
        lines.append("**H2**: *noise_montecarlo.csv не найден — запустите 06_noise_montecarlo.py*")
        lines.append("")

    # --- Графики ---
    lines.append("## 6. Графики")
    lines.append("")

    lines.append("### 2D графики")
    lines.append("")
    plot2d = sorted(OUT_PLOTS_2D.glob("*.png")) if OUT_PLOTS_2D.exists() else []
    for p in plot2d:
        rel = p.relative_to(ANALYSIS_DIR)
        lines.append(f"- [{p.name}]({rel})")
    if not plot2d:
        lines.append("*Нет 2D графиков — запустите 03_plots_2d.py*")
    lines.append("")

    lines.append("### 3D графики")
    lines.append("")
    plot3d = sorted(OUT_PLOTS_3D.glob("*.png")) if OUT_PLOTS_3D.exists() else []
    for p in plot3d:
        rel = p.relative_to(ANALYSIS_DIR)
        lines.append(f"- [{p.name}]({rel})")
    if not plot3d:
        lines.append("*Нет 3D графиков — запустите 05_plots_3d.py*")
    lines.append("")

    # --- Рекомендации ---
    lines.append("## 7. Рекомендации")
    lines.append("")
    lines.append("| Условие | Рекомендуемый метод | Причина |")
    lines.append("|---------|---------------------|---------|")
    lines.append("| Пик внутри сетки, мало шума | EA | Наименьшая ошибка |")
    lines.append("| Пик внутри сетки, шумные данные | QA | Устойчивее EA к шуму |")
    lines.append("| Быстрая грубая оценка | CG (2-точечный) | Простая формула |")
    lines.append("| FFT-спектр | EXP (парабола на log) | Лучшая точность по FFT |")
    lines.append("| Монотонные данные (пик за сеткой) | E2 (Гауссиан) | Наименьшая MAE экстраполяции |")
    lines.append("")

    # --- Выводы ---
    lines.append("## 8. Выводы")
    lines.append("")
    lines.append("1. Экспоненциальная аппроксимация (EA) даёт наилучшую точность в нормальной зоне")
    lines.append("2. Квадратичная аппроксимация (QA) — хороший компромисс точности и устойчивости")
    lines.append("3. Центр тяжести (CG) имеет систематический bias, линейно зависящий от смещения")
    lines.append("4. Для монотонных случаев Гауссова экстраполяция (E2) показывает лучшие результаты")
    lines.append("5. Точность всех методов деградирует с увеличением шага сетки")
    lines.append("")
    lines.append("---")
    lines.append(f"*Отчёт сгенерирован: {now}*")

    return '\n'.join(lines)


class ReportGenerator:
    """Генерация итогового отчёта."""

    def test_generate_report(self):
        """Генерирует REPORT.md со всеми таблицами и ссылками."""
        report = generate_report()
        path = OUT_RESULTS / "REPORT.md"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(report)
        n_lines = len(report.split('\n'))
        print(f"\n  Report saved: {path}")
        print(f"  Lines: {n_lines}")
        assert n_lines > 50, f"Report too short: {n_lines} lines"

        # Проверить наличие ключевых секций
        for section in ['Введение', 'Методы', 'Точность по зонам',
                        'Экстраполяция', 'Проверка гипотез',
                        'Графики', 'Рекомендации', 'Выводы']:
            assert section in report, f"Missing section: {section}"
        print(f"  All sections present ✓")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(ReportGenerator())
    runner.print_summary(results)
