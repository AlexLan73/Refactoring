"""
test_discriminators_plot.py -- Визуализация дискриминаторов на sinc(x)
=====================================================================

Графики:
  1. sinc(x) + отсчёты + оценки дискриминаторов
  2. Ошибка оценки vs смещение пика
  3. Сравнение точности CG / QA / EA на серии смещений

Запуск:
    python test_python/test_discriminators_plot.py
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

from scipy.optimize import curve_fit


# --- sinc(x) ---

def sinc(x):
    x = np.asarray(x, dtype=np.float64)
    result = np.ones_like(x)
    mask = np.abs(x) > 1e-15
    result[mask] = np.sin(x[mask]) / x[mask]
    return result


# --- Эталонные реализации ---

def ref_cg(A, x):
    s = np.sum(A)
    if abs(s) < 1e-15:
        return np.mean(x)
    return np.sum(A * x) / s


def ref_sd(c, A1, A2, x1, x2):
    s = A1 + A2
    if abs(s) < 1e-15:
        return (x1 + x2) * 0.5
    return (x1 + x2) * 0.5 + c * (A2 - A1) / s


def ref_qa(A, x):
    coeffs = np.polyfit(x, A, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


def ref_ea(A, x):
    """Экспоненциальная: fit y = a*exp(-b*(x-x0)^2)"""
    try:
        def gauss(xx, x0, amp, sigma):
            return amp * np.exp(-((xx - x0) / sigma) ** 2)
        p0 = [x[np.argmax(A)], max(A), 1.0]
        popt, _ = curve_fit(gauss, x, A, p0=p0, maxfev=5000)
        return popt[0]
    except Exception:
        return x[np.argmax(A)]


# --- Графики ---

OUT_DIR = Path(__file__).resolve().parent.parent / "Doc" / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def plot1_sinc_with_estimates():
    """График 1: sinc(x) + точки + оценки дискриминаторов."""
    x_fine = np.linspace(-3, 3, 500)
    y_fine = sinc(x_fine)

    x0 = 0.25  # истинное смещение пика
    y_shifted = sinc(x_fine - x0)

    # Отсчёты на сетке
    x_grid = np.array([-1.0, 0.0, 1.0])
    A_grid = sinc(x_grid - x0)

    # Оценки
    est_cg = ref_cg(A_grid, x_grid)
    est_qa = ref_qa(A_grid, x_grid)
    est_ea = ref_ea(A_grid, x_grid)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(x_fine, y_shifted, 'c-', linewidth=2, label=f'sinc(x - {x0})')
    ax.plot(x_fine, y_fine, 'w--', linewidth=0.8, alpha=0.3, label='sinc(x) reference')

    # Отсчёты
    ax.plot(x_grid, A_grid, 'yo', markersize=12, zorder=5, label='Отсчёты ДН (3 точки)')

    # Оценки дискриминаторов (вертикальные линии)
    ax.axvline(x0, color='lime', linestyle=':', linewidth=2, label=f'Истинный пик x0={x0}')
    ax.axvline(est_cg, color='#FF6B6B', linestyle='--', linewidth=1.5, label=f'CG = {est_cg:.4f}')
    ax.axvline(est_qa, color='#4ECDC4', linestyle='--', linewidth=1.5, label=f'QA = {est_qa:.4f}')
    ax.axvline(est_ea, color='#FFE66D', linestyle='--', linewidth=1.5, label=f'EA = {est_ea:.4f}')

    ax.set_xlabel('x (угловая координата)', fontsize=12)
    ax.set_ylabel('Амплитуда sinc(x)', fontsize=12)
    ax.set_title('Дискриминаторные оценки на sinc(x) = sin(x)/x', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-3, 3)

    path = OUT_DIR / "sinc_discriminator_estimates.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 1] Saved: {path}")


def plot2_error_vs_shift():
    """График 2: Ошибка оценки vs смещение пика (все 4 метода)."""
    shifts = np.linspace(-0.45, 0.45, 91)
    x_grid = np.array([-1.0, 0.0, 1.0])

    errors = {'CG': [], 'SD': [], 'QA': [], 'EA': []}

    for x0 in shifts:
        A = sinc(x_grid - x0)
        errors['CG'].append(abs(ref_cg(A, x_grid) - x0))
        errors['SD'].append(abs(ref_sd(0.8, A[0], A[2], x_grid[0], x_grid[2]) - x0))
        errors['QA'].append(abs(ref_qa(A, x_grid) - x0))
        errors['EA'].append(abs(ref_ea(A, x_grid) - x0))

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(shifts, errors['CG'], '#FF6B6B', linewidth=2, label='CG (центр масс)')
    ax.plot(shifts, errors['SD'], '#C792EA', linewidth=2, label='SD (суммарно-разн.)')
    ax.plot(shifts, errors['QA'], '#4ECDC4', linewidth=2, label='QA (квадратичная)')
    ax.plot(shifts, errors['EA'], '#FFE66D', linewidth=2, label='EA (экспоненциальная)')

    ax.set_xlabel('Истинное смещение пика x0', fontsize=12)
    ax.set_ylabel('Абсолютная ошибка |xe - x0|', fontsize=12)
    ax.set_title('Ошибка дискриминаторных оценок на sinc(x), сетка шаг=1', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    path = OUT_DIR / "error_vs_shift.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 2] Saved: {path}")


def plot3_error_vs_grid_step():
    """График 3: Ошибка vs шаг сетки для фиксированного смещения."""
    x0 = 0.2
    steps = np.linspace(0.3, 2.0, 50)

    errors = {'CG': [], 'QA': [], 'EA': []}

    for step in steps:
        x_grid = np.array([-step, 0.0, step])
        A = sinc(x_grid - x0)
        errors['CG'].append(abs(ref_cg(A, x_grid) - x0))
        errors['QA'].append(abs(ref_qa(A, x_grid) - x0))
        errors['EA'].append(abs(ref_ea(A, x_grid) - x0))

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(steps, errors['CG'], '#FF6B6B', linewidth=2, label='CG')
    ax.plot(steps, errors['QA'], '#4ECDC4', linewidth=2, label='QA')
    ax.plot(steps, errors['EA'], '#FFE66D', linewidth=2, label='EA')

    ax.set_xlabel('Шаг сетки (расстояние между отсчётами)', fontsize=12)
    ax.set_ylabel('Абсолютная ошибка |xe - x0|', fontsize=12)
    ax.set_title(f'Ошибка vs шаг сетки, sinc(x-{x0})', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    path = OUT_DIR / "error_vs_grid_step.png"
    fig.savefig(path, dpi=120, bbox_inches='tight')
    plt.close(fig)
    print(f"[Plot 3] Saved: {path}")


if __name__ == "__main__":
    print("=== Discriminator Plots (sinc data) ===")
    plot1_sinc_with_estimates()
    plot2_error_vs_shift()
    plot3_error_vs_grid_step()
    print(f"\nГрафики сохранены в: {OUT_DIR}")
