"""
09_lsq_compare.py — Сравнение МНК-дискриминаторов по 5, 7, 9 точкам
====================================================================

Сигнал: Hanning kernel (форма пика FFT после Hanning окна).
  H(δ) = 0.5·sinc_n(δ) + 0.25·sinc_n(δ−1) + 0.25·sinc_n(δ+1)

Методы:
  5QA / 5EA  — МНК-парабола / МНК-Гауссиан по 5 точкам
  7QA / 7EA  — МНК-парабола / МНК-Гауссиан по 7 точкам
  9QA / 9EA  — МНК-парабола / МНК-Гауссиан по 9 точкам

Графики (plots/2d/):
  1. lsq_bias_vs_x0.png       — знаковая ошибка (bias) vs смещение x0
  2. lsq_abs_error_vs_x0.png  — |ошибка| vs x0 (лог. Y)
  3. lsq_error_vs_snr.png     — медиана |ошибки| vs SNR (Монте-Карло)
  4. lsq_gain_vs_snr.png      — выигрыш N-pt / 5EA vs SNR

Запуск:
    cd discriminator_estimates/test_python
    python analysis/09_lsq_compare.py
"""

import sys
import numpy as np
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

OUT_CLEAN = MODULE_DIR / "Doc" / "plots" / "2_no_noise"
OUT_NOISE = MODULE_DIR / "Doc" / "plots" / "3_noise"
OUT_CLEAN.mkdir(parents=True, exist_ok=True)
OUT_NOISE.mkdir(parents=True, exist_ok=True)

# ─── Hanning kernel ────────────────────────────────────────────────────────────

def _safe_sinc(x):
    x = np.asarray(x, dtype=np.float64)
    r = np.ones_like(x)
    m = np.abs(x) > 1e-15
    r[m] = np.sin(np.pi * x[m]) / (np.pi * x[m])
    return r


def hanning_kernel(delta):
    """H(δ) = 0.5·sinc_n(δ) + 0.25·sinc_n(δ−1) + 0.25·sinc_n(δ+1)."""
    d = np.asarray(delta, dtype=np.float64)
    return np.abs(0.5 * _safe_sinc(d) + 0.25 * _safe_sinc(d - 1) + 0.25 * _safe_sinc(d + 1))


# ─── МНК-5 ─────────────────────────────────────────────────────────────────────

def ref_5qa(A, x):
    """МНК-парабола по 5 точкам. Коэф. a из знаменателя 14, b из 10."""
    step = x[1] - x[0]
    a = (2*A[0] - A[1] - 2*A[2] - A[3] + 2*A[4]) / 14.0
    b = (-2*A[0] - A[1] + A[3] + 2*A[4]) / 10.0
    if a >= -1e-30:
        return x[2]
    return x[2] + step * (-b / (2.0 * a))


def ref_5ea(A, x):
    """МНК-Гауссиан по 5 точкам: log(A) → 5QA."""
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

def ref_7qa(A, x):
    """МНК-парабола по 7 точкам. Коэф. a из 84, b из 28."""
    step = x[1] - x[0]
    a = (5*A[0] - 3*A[2] - 4*A[3] - 3*A[4] + 5*A[6]) / 84.0
    b = (-3*A[0] - 2*A[1] - A[2] + A[4] + 2*A[5] + 3*A[6]) / 28.0
    if a >= -1e-30:
        return x[3]
    return x[3] + step * (-b / (2.0 * a))


def ref_7ea(A, x):
    """МНК-Гауссиан по 7 точкам: log(A) → 7QA."""
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

def ref_9qa(A, x):
    """МНК-парабола по 9 точкам. Коэф. a из 924, b из 60."""
    step = x[1] - x[0]
    a = (28*A[0] + 7*A[1] - 8*A[2] - 17*A[3] - 20*A[4]
         - 17*A[5] - 8*A[6] + 7*A[7] + 28*A[8]) / 924.0
    b = (-4*A[0] - 3*A[1] - 2*A[2] - A[3]
         + A[5] + 2*A[6] + 3*A[7] + 4*A[8]) / 60.0
    if a >= -1e-30:
        return x[4]
    return x[4] + step * (-b / (2.0 * a))


def ref_9ea(A, x):
    """МНК-Гауссиан по 9 точкам: log(A) → 9QA."""
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


# ─── Конфигурация ──────────────────────────────────────────────────────────────

STEP = 0.5  # шаг сетки (zero-pad ×2)

GRIDS = {
    '5pt': np.array([-2, -1, 0, 1, 2], dtype=float) * STEP,
    '7pt': np.array([-3, -2, -1, 0, 1, 2, 3], dtype=float) * STEP,
    '9pt': np.array([-4, -3, -2, -1, 0, 1, 2, 3, 4], dtype=float) * STEP,
}

METHODS = {
    '5QA': (ref_5qa, '5pt', '#4ECDC4', '--'),
    '5EA': (ref_5ea, '5pt', '#FFE66D', '--'),
    '7QA': (ref_7qa, '7pt', '#C792EA', '-'),
    '7EA': (ref_7ea, '7pt', '#45B7D1', '-'),
    '9QA': (ref_9qa, '9pt', '#FF6B6B', '-.'),
    '9EA': (ref_9ea, '9pt', '#98FB98', '-.'),
}


# ─── Вычисление ошибки на чистых данных ───────────────────────────────────────

def compute_bias(shifts):
    """Знаковая ошибка xe − x0 без шума для каждого метода."""
    results = {name: [] for name in METHODS}
    for x0 in shifts:
        for name, (fn, grid_key, _, _) in METHODS.items():
            grid = GRIDS[grid_key]
            A = hanning_kernel((grid - x0) / STEP)
            xe = fn(A, grid)
            results[name].append(xe - x0)
    return results


# ─── Монте-Карло ───────────────────────────────────────────────────────────────

def run_montecarlo(snr_db_range, n_trials=1000, n_shifts=21):
    """Медиана |ошибки| vs SNR (Монте-Карло)."""
    np.random.seed(42)
    shifts = np.linspace(-STEP * 0.45, STEP * 0.45, n_shifts)
    results = {name: [] for name in METHODS}

    for snr_db in snr_db_range:
        snr_lin = 10 ** (snr_db / 20.0)
        errors = {name: [] for name in METHODS}

        for x0 in shifts:
            for _ in range(n_trials):
                for name, (fn, grid_key, _, _) in METHODS.items():
                    grid = GRIDS[grid_key]
                    A_clean = hanning_kernel((grid - x0) / STEP)
                    noise = np.random.randn(len(grid)) / snr_lin
                    A = np.abs(A_clean + noise)
                    xe = fn(A, grid)
                    errors[name].append(abs(xe - x0))

        for name in METHODS:
            results[name].append(np.median(errors[name]))

    return results


# ─── Графики ───────────────────────────────────────────────────────────────────

def plot_bias_vs_x0(shifts, bias_results):
    """График 1: Знаковая ошибка (bias) vs смещение x0."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, (_, _, color, ls) in METHODS.items():
        ax.plot(shifts, bias_results[name], color=color, ls=ls,
                linewidth=1.8, label=name)

    ax.axhline(0, color='white', lw=0.5, alpha=0.4)
    ax.set_xlabel('Истинное смещение x0 (в единицах шага сетки)', fontsize=12)
    ax.set_ylabel('Систематическая ошибка  xe − x0', fontsize=12)
    ax.set_title('МНК-дискриминаторы: систематическая ошибка (bias) без шума', fontsize=13)
    ax.legend(fontsize=10, ncol=2)
    ax.grid(True, alpha=0.25)

    path = OUT_CLEAN / "lsq_bias_vs_x0.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 2_no_noise/{path.name}")
    return path


def plot_abs_error_vs_x0(shifts, bias_results):
    """График 2: |ошибка| vs x0, лог. ось Y."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, (_, _, color, ls) in METHODS.items():
        vals = np.abs(bias_results[name])
        ax.semilogy(shifts, np.where(vals < 1e-12, 1e-12, vals),
                    color=color, ls=ls, linewidth=1.8, label=name)

    ax.set_xlabel('Истинное смещение x0 (в единицах шага сетки)', fontsize=12)
    ax.set_ylabel('|ошибка|  |xe − x0|  (лог. шкала)', fontsize=12)
    ax.set_title('МНК-дискриминаторы: модуль ошибки без шума (лог. Y)', fontsize=13)
    ax.legend(fontsize=10, ncol=2)
    ax.grid(True, alpha=0.25, which='both')

    path = OUT_CLEAN / "lsq_abs_error_vs_x0.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 2_no_noise/{path.name}")
    return path


def plot_error_vs_snr(snr_range, mc_results):
    """График 3: Медиана |ошибки| vs SNR."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for name, (_, _, color, ls) in METHODS.items():
        ax.semilogy(snr_range, mc_results[name], color=color, ls=ls,
                    linewidth=1.8, label=name)

    ax.set_xlabel('SNR (дБ)', fontsize=12)
    ax.set_ylabel('Медиана |xe − x0| (лог. шкала)', fontsize=12)
    ax.set_title('МНК-дискриминаторы: точность vs ОСШ (Монте-Карло, 1000 испытаний)', fontsize=13)
    ax.legend(fontsize=10, ncol=2)
    ax.grid(True, alpha=0.25, which='both')

    path = OUT_NOISE / "lsq_error_vs_snr.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 3_noise/{path.name}")
    return path


def plot_gain_vs_snr(snr_range, mc_results):
    """График 4: Выигрыш (gain) метода vs 5EA."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ref = np.array(mc_results['5EA'])

    for name, (_, _, color, ls) in METHODS.items():
        if name == '5EA':
            continue
        gain = ref / np.where(np.array(mc_results[name]) < 1e-15, 1e-15,
                              np.array(mc_results[name]))
        ax.plot(snr_range, gain, color=color, ls=ls,
                linewidth=1.8, label=f'{name} / 5EA')

    ax.axhline(1.0, color='white', lw=0.8, alpha=0.5, linestyle=':')
    ax.set_xlabel('SNR (дБ)', fontsize=12)
    ax.set_ylabel('Выигрыш относительно 5EA  (> 1 = лучше)', fontsize=12)
    ax.set_title('МНК-дискриминаторы: относительный выигрыш vs ОСШ', fontsize=13)
    ax.legend(fontsize=10, ncol=2)
    ax.grid(True, alpha=0.25)

    path = OUT_NOISE / "lsq_gain_vs_snr.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 3_noise/{path.name}")
    return path


# ─── main ──────────────────────────────────────────────────────────────────────

def main():
    print("09_lsq_compare.py: генерация графиков МНК 5/7/9 точек")

    # Диапазон смещений (внутри ±0.5 шага — нормальная зона)
    shifts = np.linspace(-STEP * 0.49, STEP * 0.49, 201)
    snr_range = list(range(0, 41, 2))  # 0..40 дБ шагом 2

    print("  Вычисление bias (чистый сигнал)...")
    bias_results = compute_bias(shifts)

    print("  Монте-Карло (может занять ~30 сек)...")
    mc_results = run_montecarlo(snr_range, n_trials=500, n_shifts=15)

    print("  Сохранение графиков...")
    plot_bias_vs_x0(shifts, bias_results)
    plot_abs_error_vs_x0(shifts, bias_results)
    plot_error_vs_snr(snr_range, mc_results)
    plot_gain_vs_snr(snr_range, mc_results)

    print("Готово. Файлы в:", OUT_PLOTS)


if __name__ == "__main__":
    main()
