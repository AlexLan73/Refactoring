"""
test_lsq_compare_5_7_9.py -- Сравнение МНК-5, МНК-7, МНК-9 с шумом
=====================================================================

Сигнал: Hanning kernel (форма пика FFT после Hanning окна)
  H(δ) = 0.5·sinc(δ) + 0.25·sinc(δ-1) + 0.25·sinc(δ+1)

Методы:
  - 5QA / 5EA   : МНК-парабола / МНК-Гауссиан по 5 точкам
  - 7QA / 7EA   : МНК-парабола / МНК-Гауссиан по 7 точкам (НОВЫЕ)
  - 9QA / 9EA   : МНК-парабола / МНК-Гауссиан по 9 точкам (НОВЫЕ)
  - NL-Hanning  : Нелинейная подгонка к точному Hanning kernel (→ Крамер-Рао)

Графики:
  1. Медиана ошибки vs SNR (все методы)
  2. Ошибка vs смещение (чистые данные — только bias)
  3. Относительный выигрыш N-pt / 5EA vs SNR
  4. Сводная таблица в консоли

Запуск:
    python test_python/test_lsq_compare_5_7_9.py
"""

import sys
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("dark_background")
    HAS_PLOT = True
except ImportError:
    print("[SKIP] matplotlib не установлен")
    HAS_PLOT = False

try:
    from scipy.optimize import minimize_scalar
    HAS_SCIPY = True
except ImportError:
    print("[WARN] scipy не установлен — NL-Hanning пропускается")
    HAS_SCIPY = False


OUT_DIR = Path(__file__).resolve().parent.parent / "Doc" / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Hanning kernel ────────────────────────────────────────────────────────────

def _safe_sinc(x):
    """sinc(x) = sin(πx)/(πx), с защитой от x=0."""
    x = np.asarray(x, dtype=np.float64)
    r = np.ones_like(x)
    m = np.abs(x) > 1e-15
    r[m] = np.sin(np.pi * x[m]) / (np.pi * x[m])
    return r


def hanning_kernel(delta):
    """Hanning kernel: форма пика FFT после Hanning окна (в единицах бинов)."""
    d = np.asarray(delta, dtype=np.float64)
    return np.abs(0.5 * _safe_sinc(d) + 0.25 * _safe_sinc(d - 1) + 0.25 * _safe_sinc(d + 1))


# ─── МНК-5 ─────────────────────────────────────────────────────────────────────

def ref_5qa(A, x):
    """МНК-парабола по 5 точкам. Формула: знаменатель a=14, b=10."""
    step = x[1] - x[0]
    a = (2*A[0] - A[1] - 2*A[2] - A[3] + 2*A[4]) / 14.0
    b = (-2*A[0] - A[1] + A[3] + 2*A[4]) / 10.0
    if a >= -1e-30:
        return x[2]
    return x[2] + step * (-b / (2.0 * a))


def ref_5ea(A, x):
    """МНК-Гауссиан по 5 точкам: логарифмирует, затем 5QA."""
    if np.any(A <= 0):
        return ref_5qa(A, x)
    step = x[1] - x[0]
    z = np.log(A)
    a = (2*z[0] - z[1] - 2*z[2] - z[3] + 2*z[4]) / 14.0
    b = (-2*z[0] - z[1] + z[3] + 2*z[4]) / 10.0
    if a >= -1e-30:
        return x[2]
    return x[2] + step * (-b / (2.0 * a))


# ─── МНК-7 ─────────────────────────────────────────────────────────────────────
# Коэффициенты `a`:  (5·A[0] + 0·A[1] - 3·A[2] - 4·A[3] - 3·A[4] + 0·A[5] + 5·A[6]) / 84
# Коэффициенты `b`:  (-3·A[0] - 2·A[1] - A[2] + A[4] + 2·A[5] + 3·A[6]) / 28
# Примечание: A[1] и A[5] не входят в `a` — математически уникальное свойство 7pt!

def ref_7qa(A, x):
    """МНК-парабола по 7 точкам. Знаменатель a=84, b=28."""
    step = x[1] - x[0]
    a = (5*A[0] - 3*A[2] - 4*A[3] - 3*A[4] + 5*A[6]) / 84.0
    b = (-3*A[0] - 2*A[1] - A[2] + A[4] + 2*A[5] + 3*A[6]) / 28.0
    if a >= -1e-30:
        return x[3]
    return x[3] + step * (-b / (2.0 * a))


def ref_7ea(A, x):
    """МНК-Гауссиан по 7 точкам."""
    if np.any(A <= 0):
        return ref_7qa(A, x)
    step = x[1] - x[0]
    z = np.log(A)
    a = (5*z[0] - 3*z[2] - 4*z[3] - 3*z[4] + 5*z[6]) / 84.0
    b = (-3*z[0] - 2*z[1] - z[2] + z[4] + 2*z[5] + 3*z[6]) / 28.0
    if a >= -1e-30:
        return x[3]
    return x[3] + step * (-b / (2.0 * a))


# ─── МНК-9 ─────────────────────────────────────────────────────────────────────
# Коэффициенты `a`:  (28·A[0]+7·A[1]-8·A[2]-17·A[3]-20·A[4]-17·A[5]-8·A[6]+7·A[7]+28·A[8]) / 924
# Коэффициенты `b`:  (-4·A[0]-3·A[1]-2·A[2]-A[3]+A[5]+2·A[6]+3·A[7]+4·A[8]) / 60

def ref_9qa(A, x):
    """МНК-парабола по 9 точкам. Знаменатель a=924, b=60."""
    step = x[1] - x[0]
    a = (28*A[0] + 7*A[1] - 8*A[2] - 17*A[3] - 20*A[4]
         - 17*A[5] - 8*A[6] + 7*A[7] + 28*A[8]) / 924.0
    b = (-4*A[0] - 3*A[1] - 2*A[2] - A[3]
         + A[5] + 2*A[6] + 3*A[7] + 4*A[8]) / 60.0
    if a >= -1e-30:
        return x[4]
    return x[4] + step * (-b / (2.0 * a))


def ref_9ea(A, x):
    """МНК-Гауссиан по 9 точкам."""
    if np.any(A <= 0):
        return ref_9qa(A, x)
    step = x[1] - x[0]
    z = np.log(A)
    a = (28*z[0] + 7*z[1] - 8*z[2] - 17*z[3] - 20*z[4]
         - 17*z[5] - 8*z[6] + 7*z[7] + 28*z[8]) / 924.0
    b = (-4*z[0] - 3*z[1] - 2*z[2] - z[3]
         + z[5] + 2*z[6] + 3*z[7] + 4*z[8]) / 60.0
    if a >= -1e-30:
        return x[4]
    return x[4] + step * (-b / (2.0 * a))


# ─── Нелинейная подгонка к Hanning kernel (Крамер-Рао) ────────────────────────

def ref_nl_hanning(A, x):
    """Нелинейная подгонка к точному Hanning kernel.

    Минимизирует ||A - scale·H(x - x_peak)||²
    по x_peak (1D поиск). Приближается к нижней границе Крамера-Рао.

    Использует scipy.optimize.minimize_scalar.
    """
    if not HAS_SCIPY:
        return ref_5ea(A[:5], x[:5]) if len(A) >= 5 else x[len(x)//2]

    x = np.asarray(x, dtype=np.float64)
    A = np.asarray(A, dtype=np.float64)
    step = x[1] - x[0]
    x_center = x[len(x) // 2]

    def cost(delta):
        """delta: смещение пика от x_center в единицах бинов."""
        x_peak = x_center + delta * step
        offsets = (x - x_peak) / step
        h_pred = hanning_kernel(offsets)
        # Оптимальный масштаб: scale* = Σ(A·h) / Σ(h²)
        denom = np.dot(h_pred, h_pred)
        if denom < 1e-30:
            return 1e30
        scale = np.dot(A, h_pred) / denom
        return np.sum((A - scale * h_pred) ** 2)

    res = minimize_scalar(cost, bounds=(-0.6, 0.6), method='bounded')
    return x_center + res.x * step


# ─── Конфигурация методов ──────────────────────────────────────────────────────

STEP = 0.5  # zero-pad ×2

GRIDS = {
    '5pt': np.array([-2, -1, 0, 1, 2]) * STEP,
    '7pt': np.array([-3, -2, -1, 0, 1, 2, 3]) * STEP,
    '9pt': np.array([-4, -3, -2, -1, 0, 1, 2, 3, 4]) * STEP,
}

METHODS = {
    '5QA': (ref_5qa, '5pt', '#4ECDC4', '--'),
    '5EA': (ref_5ea, '5pt', '#FFE66D', '--'),
    '7QA': (ref_7qa, '7pt', '#C792EA', '-'),
    '7EA': (ref_7ea, '7pt', '#45B7D1', '-'),
    '9QA': (ref_9qa, '9pt', '#FF6B6B', '-.'),
    '9EA': (ref_9ea, '9pt', '#98FB98', '-.'),
    'NL':  (ref_nl_hanning, '9pt', '#FFFFFF', ':'),
}


# ─── Монте-Карло ───────────────────────────────────────────────────────────────

def run_montecarlo(snr_range, n_trials=1000, n_shifts=21):
    """Монте-Карло: медиана ошибки vs SNR для всех методов.

    Returns: dict {method_name: list[median_error per SNR]}
    """
    np.random.seed(42)
    shifts = np.linspace(-STEP * 0.45, STEP * 0.45, n_shifts)

    results = {name: [] for name in METHODS}

    for snr_db in snr_range:
        trial_errors = {name: [] for name in METHODS}

        for d0 in shifts:
            # Эталонный сигнал на самой широкой сетке (9pt)
            x9 = GRIDS['9pt']
            A9_clean = hanning_kernel(x9 - d0)
            noise_level = np.max(A9_clean) * 10 ** (-snr_db / 20.0)

            for _ in range(n_trials):
                noise = noise_level * np.random.randn(9)
                A9 = np.maximum(A9_clean + noise, 1e-10)

                for name, (fn, grid_key, _, _) in METHODS.items():
                    x = GRIDS[grid_key]
                    n = len(x)
                    # Центрируем: берём центральные n точек из 9
                    i0 = (9 - n) // 2
                    A = A9[i0:i0 + n]
                    try:
                        est = fn(A, x)
                        trial_errors[name].append(abs(est - d0))
                    except Exception:
                        trial_errors[name].append(STEP)

        for name in METHODS:
            results[name].append(np.median(trial_errors[name]))

    return results


def run_bias_sweep(n_pts=91):
    """Чистые данные (без шума): ошибка vs смещение — измеряем только bias."""
    shifts = np.linspace(-STEP * 0.48, STEP * 0.48, n_pts)
    errors = {name: [] for name in METHODS}

    for d0 in shifts:
        x9 = GRIDS['9pt']
        A9 = hanning_kernel(x9 - d0)

        for name, (fn, grid_key, _, _) in METHODS.items():
            x = GRIDS[grid_key]
            n = len(x)
            i0 = (9 - n) // 2
            A = A9[i0:i0 + n]
            try:
                est = fn(A, x)
                errors[name].append(abs(est - d0))
            except Exception:
                errors[name].append(STEP)

    return shifts, errors


# ─── Печать сводной таблицы ────────────────────────────────────────────────────

def print_summary_table(snr_range, results):
    """Выводит таблицу: метод × SNR → медиана ошибки (в процентах шага)."""
    header = f"{'SNR':>5} | " + " | ".join(f"{name:>6}" for name in METHODS)
    sep = "-" * len(header)
    print("\n" + "=" * 60)
    print("Медиана ошибки [% шага (0.5 bin)]  —  Hanning kernel, zp×2")
    print("=" * 60)
    print(header)
    print(sep)
    for i, snr in enumerate(snr_range):
        row = f"{snr:>4}дБ | "
        vals = []
        for name in METHODS:
            err_pct = results[name][i] / STEP * 100
            vals.append(f"{err_pct:>6.1f}")
        row += " | ".join(vals)
        print(row)
    print(sep)
    print("Единицы: % от шага h=0.5 бин")

    # Выигрыш лучшего N-pt над 5EA
    print("\nВыигрыш (5EA / лучший): 5EA/5EA, 5EA/7best, 5EA/9best")
    print(f"{'SNR':>5} | {'5EA':>6} | {'7best':>7} | {'9best':>7} | {'NL':>6} | Ratio7 | Ratio9")
    print(sep)
    for i, snr in enumerate(snr_range):
        ref = results['5EA'][i]
        best7 = min(results['7QA'][i], results['7EA'][i])
        best9 = min(results['9QA'][i], results['9EA'][i])
        nl    = results['NL'][i]
        r7 = ref / best7 if best7 > 1e-15 else 0
        r9 = ref / best9 if best9 > 1e-15 else 0
        print(f"{snr:>4}дБ | {ref/STEP*100:>6.1f} | {best7/STEP*100:>7.1f} | "
              f"{best9/STEP*100:>7.1f} | {nl/STEP*100:>6.1f} | {r7:>6.2f}× | {r9:>6.2f}×")


# ─── Графики ───────────────────────────────────────────────────────────────────

def plot_all(snr_range, mc_results, bias_shifts, bias_errors):
    if not HAS_PLOT:
        return

    # Таблица расшифровок внизу — строки: [сокращение, цвет-патч, расшифровка]
    LEGEND_ROWS = [
        ('5QA', '#4ECDC4', 'МНК-парабола, 5 точек  {−2,−1,0,+1,+2}·h',       'Квадратичная аппроксимация, быстрая при низком SNR'),
        ('5EA', '#FFE66D', 'МНК-Гауссиан, 5 точек  {−2,−1,0,+1,+2}·h',        'Логарифмирует, затем парабола — лучший при SNR ≥ 25 дБ'),
        ('7QA', '#C792EA', 'МНК-парабола, 7 точек  {−3..+3}·h',                'Лучший при SNR 10–20 дБ, выигрыш ~1.5× над 5EA'),
        ('7EA', '#45B7D1', 'МНК-Гауссиан, 7 точек  {−3..+3}·h',               'Нестабилен: крайние точки малы → log(шум) = взрыв'),
        ('9QA', '#FF6B6B', 'МНК-парабола, 9 точек  {−4..+4}·h',               'Насыщается на ~10% из-за сильного bias (широкое покрытие)'),
        ('9EA', '#98FB98', 'МНК-Гауссиан, 9 точек  {−4..+4}·h',               'Нестабилен ещё сильнее, чем 7EA — не применять'),
        ('NL',  '#FFFFFF', 'Нелинейная подгонка к точному Hanning kernel',     'Ближе к границе Крамера-Рао, но на практике — не лучший'),
    ]

    # Компоновка: 3 графика сверху + таблица снизу
    fig = plt.figure(figsize=(22, 11))
    gs = fig.add_gridspec(2, 3, height_ratios=[3.5, 1], hspace=0.45, wspace=0.32)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax_table = fig.add_subplot(gs[1, :])   # таблица на всю ширину

    fig.suptitle(
        'МНК-5 / МНК-7 / МНК-9 на Hanning kernel  (шаг = 0.5 бин, zero-pad ×2)',
        fontsize=14, y=0.98
    )

    # ── График 1: Медиана ошибки vs SNR ──────────────────────────────────────
    for name, (_, _, color, ls) in METHODS.items():
        lw = 2.5 if name == 'NL' else (2.0 if name[0] in ('7', '9') else 1.5)
        errs_pct = [e / STEP * 100 for e in mc_results[name]]
        ax1.plot(snr_range, errs_pct, color=color, linestyle=ls, linewidth=lw,
                 label=name, marker='o', markersize=3)

    ax1.set_xlabel('SNR (дБ)', fontsize=11)
    ax1.set_ylabel('Медиана ошибки (% шага)', fontsize=11)
    ax1.set_title('График 1: Шумоустойчивость vs SNR', fontsize=12)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    ax1.set_ylim(0.1, 100)

    # ── График 2: Bias vs смещение (чистые данные) ───────────────────────────
    for name, (_, _, color, ls) in METHODS.items():
        lw = 2.5 if name == 'NL' else (2.0 if name[0] in ('7', '9') else 1.5)
        bias_pct = [e / STEP * 100 for e in bias_errors[name]]
        ax2.plot(bias_shifts / STEP, bias_pct, color=color, linestyle=ls,
                 linewidth=lw, label=name)

    ax2.set_xlabel('Смещение пика (доли шага h)', fontsize=11)
    ax2.set_ylabel('Ошибка (% шага) — только bias', fontsize=11)
    ax2.set_title('График 2: Систематическая ошибка (без шума)', fontsize=12)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')
    ax2.set_ylim(1e-5, 20)
    ax2.axhline(1.0, color='gray', linestyle=':', alpha=0.5)

    # ── График 3: Относительный выигрыш vs SNR ───────────────────────────────
    ref_errs = np.array(mc_results['5EA'])
    for name in ['7QA', '7EA', '9QA', '9EA', 'NL']:
        _, _, color, ls = METHODS[name]
        lw = 2.5 if name == 'NL' else 2.0
        ratio = ref_errs / np.maximum(np.array(mc_results[name]), 1e-15)
        ax3.plot(snr_range, ratio, color=color, linestyle=ls, linewidth=lw,
                 label=f'5EA / {name}', marker='o', markersize=3)

    ax3.axhline(1.0, color='white', linestyle='--', alpha=0.4, linewidth=1,
                label='= 5EA (граница)')
    ax3.set_xlabel('SNR (дБ)', fontsize=11)
    ax3.set_ylabel('5EA / X  (>1 значит X лучше)', fontsize=11)
    ax3.set_title('График 3: Выигрыш метода X над 5EA', fontsize=12)
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.5, 4.0)

    # ── Таблица расшифровок ───────────────────────────────────────────────────
    ax_table.axis('off')

    col_labels = ['Сокращение', 'Метод (полное название)', 'Примечание']
    table_data = [[row[0], row[2], row[3]] for row in LEGEND_ROWS]
    cell_colors = [
        [row[1], row[1], row[1]] for row in LEGEND_ROWS
    ]
    # Цвет фона для каждой строки — цвет метода (приглушённый)
    row_colors = [[row[1]] * 3 for row in LEGEND_ROWS]

    tbl = ax_table.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc='left',
        loc='center',
        bbox=[0, -0.05, 1, 1.1],
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9.5)

    # Заголовок таблицы — тёмный фон, белый текст
    for col in range(3):
        cell = tbl[0, col]
        cell.set_facecolor('#333333')
        cell.set_text_props(color='white', fontweight='bold')

    # Строки данных — цвет соответствует линии на графике (приглушённый)
    alpha_map = {'#4ECDC4': '#1a6b68', '#FFE66D': '#7a6e25',
                 '#C792EA': '#6b4a8c', '#45B7D1': '#1a5a6b',
                 '#FF6B6B': '#7a2929', '#98FB98': '#3a7a3a',
                 '#FFFFFF': '#555555'}
    for row_idx, legend_row in enumerate(LEGEND_ROWS):
        bg = alpha_map.get(legend_row[1], '#333333')
        for col in range(3):
            cell = tbl[row_idx + 1, col]
            cell.set_facecolor(bg)
            cell.set_text_props(color='white')
            cell.set_edgecolor('#555555')

    # Ширина колонок
    tbl.auto_set_column_width([0, 1, 2])

    ax_table.set_title('Расшифровка сокращений', fontsize=11,
                       pad=6, loc='left', color='white')

    path = OUT_DIR / "lsq_5_7_9_noise_comparison.png"
    fig.savefig(path, dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"\n[Plot] Сохранён: {path}")


# ─── Главный запуск ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("МНК-5 / МНК-7 / МНК-9 : Сравнение шумоустойчивости")
    print("Сигнал: Hanning kernel, шаг = 0.5 бин (zero-pad ×2)")
    print("=" * 60)

    SNR_RANGE = [5, 10, 15, 20, 25, 30, 35, 40]
    N_TRIALS  = 1000   # испытаний на каждый SNR × смещение
    N_SHIFTS  = 21     # смещений пика

    print(f"\nМонте-Карло: {N_TRIALS} trials × {N_SHIFTS} shifts × {len(SNR_RANGE)} SNR ...")
    mc_results = run_montecarlo(SNR_RANGE, n_trials=N_TRIALS, n_shifts=N_SHIFTS)
    print("OK")

    print("\nBias sweep (чистые данные) ...")
    bias_shifts, bias_errors = run_bias_sweep()
    print("OK")

    print_summary_table(SNR_RANGE, mc_results)
    plot_all(SNR_RANGE, mc_results, bias_shifts, bias_errors)

    print("\nГотово! Графики: discriminator_estimates/Doc/plots/lsq_5_7_9_noise_comparison.png")
