"""
test_discriminators_5pt_plot.py -- Визуализация МНК-дискриминаторов по 5 точкам
===============================================================================

Сигнал: Hanning kernel — форма пика после FFT с Hanning окном.

Графики:
  1. Hanning kernel + 5 отсчётов + оценки дискриминаторов
  2. Ошибка vs смещение (шаг 0.5 бин = zp×2)
  3. Ошибка vs смещение (шаг 0.25 бин = zp×4)
  4. Шумоустойчивость: медиана ошибки vs SNR

Запуск:
    python test_python/test_discriminators_5pt_plot.py
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
except ImportError:
    print("[SKIP] matplotlib не установлен. pip install matplotlib")
    sys.exit(0)


# --- Hanning kernel ---

def hanning_kernel(delta):
    """Форма пика в FFT после Hanning окна.
    H(d) = 0.5*sinc(d) + 0.25*sinc(d-1) + 0.25*sinc(d+1)
    """
    delta = np.asarray(delta, dtype=np.float64)
    def safe_sinc(x):
        x = np.asarray(x, dtype=np.float64)
        r = np.ones_like(x)
        m = np.abs(x) > 1e-15
        r[m] = np.sin(np.pi * x[m]) / (np.pi * x[m])
        return r
    return np.abs(0.5*safe_sinc(delta) + 0.25*safe_sinc(delta-1) + 0.25*safe_sinc(delta+1))


# --- Эталонные реализации ---

def ref_qa(A, x):
    coeffs = np.polyfit(x, A, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


def ref_ea(A, x):
    if any(a <= 0 for a in A):
        return ref_qa(A, x)
    z = np.log(A)
    coeffs = np.polyfit(x, z, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


def ref_5qa(A, x):
    step = x[1] - x[0]
    a = (2.0*A[0] - A[1] - 2.0*A[2] - A[3] + 2.0*A[4]) / 14.0
    b = (-2.0*A[0] - A[1] + A[3] + 2.0*A[4]) / 10.0
    if a >= -1e-30:
        return x[2]
    return x[2] + step * (-b / (2.0 * a))


def ref_5ea(A, x):
    if any(A <= 0):
        return ref_5qa(A, x)
    step = x[1] - x[0]
    z = np.log(A)
    a = (2.0*z[0] - z[1] - 2.0*z[2] - z[3] + 2.0*z[4]) / 14.0
    b = (-2.0*z[0] - z[1] + z[3] + 2.0*z[4]) / 10.0
    if a >= -1e-30:
        return x[2]
    return x[2] + step * (-b / (2.0 * a))


# --- Цвета ---

COLORS = {
    'QA3': '#4ECDC4',
    'EA3': '#FFE66D',
    '5QA': '#C792EA',
    '5EA': '#45B7D1',
}

OUT_DIR = Path(__file__).resolve().parent.parent / "Doc" / "plots" / "2_no_noise"
OUT_DIR_NOISE = Path(__file__).resolve().parent.parent / "Doc" / "plots" / "3_noise"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR_NOISE.mkdir(parents=True, exist_ok=True)


# --- Графики ---

def plot1_hanning_5pt_estimates():
    """График 1: Hanning kernel + 5 точек + оценки дискриминаторов."""
    d_fine = np.linspace(-3, 3, 500)
    d0 = 0.2  # истинное смещение пика

    y_fine = hanning_kernel(d_fine - d0)

    step = 0.5  # zp×2
    x5 = np.array([-2, -1, 0, 1, 2]) * step
    A5 = hanning_kernel(x5 - d0)
    x3 = x5[1:4]
    A3 = A5[1:4]

    est_qa3 = ref_qa(A3, x3)
    est_ea3 = ref_ea(A3, x3)
    est_5qa = ref_5qa(A5, x5)
    est_5ea = ref_5ea(A5, x5)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(d_fine, y_fine, 'c-', linewidth=2, alpha=0.6,
            label=f'Hanning kernel (пик в {d0})')
    ax.plot(x5, A5, 'wo', markersize=12, zorder=5, label='5 отсчётов (zp×2)')
    ax.plot(x3, A3, 'yo', markersize=8, zorder=6, label='3 центральных')

    ax.axvline(d0, color='lime', linestyle=':', linewidth=2.5,
               label=f'Истинный пик = {d0}')
    ax.axvline(est_qa3, color=COLORS['QA3'], linestyle='--', linewidth=1.2,
               label=f'QA3 = {est_qa3:.5f} (err={abs(est_qa3-d0):.5f})')
    ax.axvline(est_ea3, color=COLORS['EA3'], linestyle='--', linewidth=1.2,
               label=f'EA3 = {est_ea3:.5f} (err={abs(est_ea3-d0):.5f})')
    ax.axvline(est_5qa, color=COLORS['5QA'], linestyle='-.', linewidth=2,
               label=f'5QA = {est_5qa:.5f} (err={abs(est_5qa-d0):.5f})')
    ax.axvline(est_5ea, color=COLORS['5EA'], linestyle='-.', linewidth=2,
               label=f'5EA = {est_5ea:.5f} (err={abs(est_5ea-d0):.5f})')

    ax.set_xlabel('Смещение (бины)', fontsize=12)
    ax.set_ylabel('Амплитуда', fontsize=12)
    ax.set_title('Дискриминаторы на Hanning kernel (FFT + Hanning окно)', fontsize=14)
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-3, 3)

    path = OUT_DIR / "hanning_5pt_estimates.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 1] Saved: {path}")


def plot2_error_vs_shift_step05():
    """График 2: Ошибка vs смещение, шаг = 0.5 (zero-pad ×2)."""
    step = 0.5
    shifts = np.linspace(-step * 0.45, step * 0.45, 91)
    x5 = np.array([-2, -1, 0, 1, 2]) * step
    x3 = x5[1:4]

    errors = {k: [] for k in COLORS}
    for d0 in shifts:
        A5 = hanning_kernel(x5 - d0)
        A3 = A5[1:4]
        errors['QA3'].append(abs(ref_qa(A3, x3) - d0))
        errors['EA3'].append(abs(ref_ea(A3, x3) - d0))
        errors['5QA'].append(abs(ref_5qa(A5, x5) - d0))
        errors['5EA'].append(abs(ref_5ea(A5, x5) - d0))

    fig, ax = plt.subplots(figsize=(14, 7))
    for name, errs in errors.items():
        lw = 2.5 if '5' in name else 1.5
        ls = '-' if '5' in name else '--'
        ax.plot(shifts, errs, color=COLORS[name], linewidth=lw, linestyle=ls,
                label=f'{name} (mean={np.mean(errs):.6f})')

    ax.set_xlabel('Смещение пика (бины)', fontsize=12)
    ax.set_ylabel('Абсолютная ошибка', fontsize=12)
    ax.set_title('Ошибка дискриминаторов на Hanning kernel, шаг = 0.5 бин (zp×2)',
                 fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    path = OUT_DIR / "hanning_error_vs_shift_step05.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 2] Saved: {path}")


def plot3_error_vs_shift_step025():
    """График 3: Ошибка vs смещение, шаг = 0.25 (zero-pad ×4)."""
    step = 0.25
    shifts = np.linspace(-step * 0.45, step * 0.45, 91)
    x5 = np.array([-2, -1, 0, 1, 2]) * step
    x3 = x5[1:4]

    errors = {k: [] for k in COLORS}
    for d0 in shifts:
        A5 = hanning_kernel(x5 - d0)
        A3 = A5[1:4]
        errors['QA3'].append(abs(ref_qa(A3, x3) - d0))
        errors['EA3'].append(abs(ref_ea(A3, x3) - d0))
        errors['5QA'].append(abs(ref_5qa(A5, x5) - d0))
        errors['5EA'].append(abs(ref_5ea(A5, x5) - d0))

    fig, ax = plt.subplots(figsize=(14, 7))
    for name, errs in errors.items():
        lw = 2.5 if '5' in name else 1.5
        ls = '-' if '5' in name else '--'
        ax.plot(shifts, errs, color=COLORS[name], linewidth=lw, linestyle=ls,
                label=f'{name} (mean={np.mean(errs):.7f})')

    ax.set_xlabel('Смещение пика (бины)', fontsize=12)
    ax.set_ylabel('Абсолютная ошибка', fontsize=12)
    ax.set_title('Ошибка дискриминаторов на Hanning kernel, шаг = 0.25 бин (zp×4)',
                 fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')

    path = OUT_DIR / "hanning_error_vs_shift_step025.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 3] Saved: {path}")


def plot4_noise_robustness():
    """График 4: Шумоустойчивость — медиана ошибки vs SNR."""
    np.random.seed(42)
    step = 0.5
    x5 = np.array([-2, -1, 0, 1, 2]) * step
    x3 = x5[1:4]
    n_trials = 1000
    shifts = np.linspace(-step * 0.45, step * 0.45, 11)

    snr_range = np.arange(5, 45, 2)

    results = {k: {'median': [], 'q25': [], 'q75': []} for k in COLORS}

    for snr_db in snr_range:
        trial_errors = {k: [] for k in COLORS}

        for d0 in shifts:
            A_clean = hanning_kernel(x5 - d0)
            for _ in range(n_trials):
                noise_level = np.max(A_clean) * 10**(-snr_db / 20)
                A_noisy = np.maximum(A_clean + noise_level * np.random.randn(5), 1e-10)
                A3_noisy = A_noisy[1:4]

                trial_errors['QA3'].append(abs(ref_qa(A3_noisy, x3) - d0))
                trial_errors['EA3'].append(abs(ref_ea(A3_noisy, x3) - d0))
                trial_errors['5QA'].append(abs(ref_5qa(A_noisy, x5) - d0))
                trial_errors['5EA'].append(abs(ref_5ea(A_noisy, x5) - d0))

        for k in COLORS:
            arr = np.array(trial_errors[k])
            results[k]['median'].append(np.median(arr))
            results[k]['q25'].append(np.percentile(arr, 25))
            results[k]['q75'].append(np.percentile(arr, 75))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Медиана
    for name, data in results.items():
        lw = 2.5 if '5' in name else 1.5
        ls = '-' if '5' in name else '--'
        ax1.plot(snr_range, data['median'], color=COLORS[name],
                 linewidth=lw, linestyle=ls, label=name, marker='o', markersize=3)

    ax1.set_xlabel('SNR (дБ)', fontsize=12)
    ax1.set_ylabel('Медиана ошибки (бины)', fontsize=12)
    ax1.set_title('Медиана ошибки vs SNR', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Интерквартильный размах (IQR = Q75 - Q25) = мера стабильности
    for name, data in results.items():
        lw = 2.5 if '5' in name else 1.5
        ls = '-' if '5' in name else '--'
        iqr = [q75 - q25 for q25, q75 in zip(data['q25'], data['q75'])]
        ax2.plot(snr_range, iqr, color=COLORS[name],
                 linewidth=lw, linestyle=ls, label=name, marker='o', markersize=3)

    ax2.set_xlabel('SNR (дБ)', fontsize=12)
    ax2.set_ylabel('IQR ошибки (Q75-Q25)', fontsize=12)
    ax2.set_title('Разброс ошибки vs SNR (стабильность)', fontsize=14)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    fig.suptitle('Hanning kernel: 5pt МНК vs 3pt, шаг=0.5 бин (zp×2)',
                 fontsize=15, y=1.02)
    fig.tight_layout()

    path = OUT_DIR_NOISE / "hanning_noise_robustness.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 4] Saved: {path}")


if __name__ == "__main__":
    print("=== Hanning Kernel: 5-Point LSQ Discriminator Plots ===")
    plot1_hanning_5pt_estimates()
    plot2_error_vs_shift_step05()
    plot3_error_vs_shift_step025()
    plot4_noise_robustness()
    print(f"\nГрафики сохранены в: {OUT_DIR}")
