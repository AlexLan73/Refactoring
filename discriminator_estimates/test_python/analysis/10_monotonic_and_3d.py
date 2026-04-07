"""
10_monotonic_and_3d.py — Монотонный режим QA-3pt vs МНК-5 + 3D поверхность 5EA
===============================================================================

Монотонный случай — когда пик сигнала находится ВНЕ окна из 3 отсчётов.
3-точечные методы (QA, EA) при этом вынуждены экстраполировать — ненадёжно.
5-точечный МНК (5EA) использует более широкое окно — пик виден дольше.

Графики:
  1. 2_no_noise/monotonic_example.png     — пример: нормальный vs монотонный сигнал
  2. 2_no_noise/monotonic_bias.png        — ошибка без шума, полный диапазон x0
  3. 3_noise/monotonic_error_vs_snr.png   — MC в монотонной зоне: ошибка vs SNR
  4. 4_3d/surface_5ea_x0_snr.png          — 3D: 5EA ошибка f(x0, SNR)
  5. 4_3d/heatmap_5ea_x0_snr.png          — тепловая карта той же поверхности

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/10_monotonic_and_3d.py
"""

import sys
import numpy as np
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR   = ANALYSIS_DIR.parent.parent
REPO_ROOT    = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
plt.style.use("dark_background")

OUT_CLEAN = MODULE_DIR / "Doc" / "plots" / "2_no_noise"
OUT_NOISE = MODULE_DIR / "Doc" / "plots" / "3_noise"
OUT_3D    = MODULE_DIR / "Doc" / "plots" / "4_3d"
for p in (OUT_CLEAN, OUT_NOISE, OUT_3D):
    p.mkdir(parents=True, exist_ok=True)

# ─── Параметры сетки ──────────────────────────────────────────────────────────

STEP = 0.5          # шаг между отсчётами (в единицах бинов/шагов)
GRID_3PT = np.array([-1, 0, 1], dtype=float) * STEP      # 3-точечная сетка
GRID_5PT = np.array([-2, -1, 0, 1, 2], dtype=float) * STEP  # 5-точечная сетка

# Граница монотонного режима:
# - 3pt монотонен при |x0| > MONO_3PT (пик выходит из 3-точечного окна)
# - 5pt монотонен при |x0| > MONO_5PT
MONO_3PT = 0.5 * STEP   # ≈ 0.25 для STEP=0.5
MONO_5PT = 2.0 * STEP   # ≈ 1.0  для STEP=0.5

# ─── Сигнал: Hanning kernel ───────────────────────────────────────────────────

def _sinc_n(x):
    """Нормализованный sinc: sin(πx) / (πx)."""
    x = np.asarray(x, dtype=np.float64)
    r = np.ones_like(x)
    m = np.abs(x) > 1e-15
    r[m] = np.sin(np.pi * x[m]) / (np.pi * x[m])
    return r


def hanning_kernel(delta):
    """Форма спектрального пика после Hanning-окна.
    H(δ) = 0.5·sinc_n(δ) + 0.25·sinc_n(δ−1) + 0.25·sinc_n(δ+1)
    δ = (x - x0) / step  — смещение в нормированных единицах.
    """
    d = np.asarray(delta, dtype=np.float64)
    return np.abs(0.5 * _sinc_n(d) + 0.25 * _sinc_n(d - 1) + 0.25 * _sinc_n(d + 1))


def sample(x0, grid):
    """Отсчёты сигнала на сетке grid при истинном пике x0."""
    return hanning_kernel((grid - x0) / STEP)


# ─── Дискриминаторы ───────────────────────────────────────────────────────────

def qa_3pt(A, x):
    """QA: квадратичная аппроксимация по 3 точкам (формула Ao из C-кода)."""
    A1, A2, A3 = float(A[0]), float(A[1]), float(A[2])
    x1, x2, x3 = float(x[0]), float(x[1]), float(x[2])
    eps = 1e-15
    if abs(A2 - A3) < eps:
        return x2 if abs(A2 - A1) < eps else (x1 if A1 > A2 else 0.5*(x3+x2))
    if abs(A2 - A1) < eps:
        return x3 if A3 > A2 else 0.5*(x1+x2)
    Ao = (A2 - A1) / (A2 - A3)
    denom = (Ao - 1.0)*x2 - Ao*x3 + x1
    if abs(denom) < eps:
        return x2
    return 0.5 * ((Ao-1.0)*x2**2 - Ao*x3**2 + x1**2) / denom


def lsq5_peak(y):
    """МНК-парабола по 5 равноотстоящим значениям. Нормированные координаты {-2..2}."""
    a = (2*y[0] - y[1] - 2*y[2] - y[3] + 2*y[4]) / 14.0
    b = (-2*y[0] - y[1] + y[3] + 2*y[4]) / 10.0
    if a >= -1e-15:
        return 0.0, False
    peak = -b / (2.0 * a)
    return max(-2.0, min(2.0, peak)), True


def qa_5pt(A, x):
    """5QA: МНК-парабола по 5 точкам."""
    h = x[1] - x[0]
    peak, _ = lsq5_peak(np.asarray(A, float))
    return float(x[2] + h * peak)


def ea_5pt(A, x):
    """5EA: МНК-Гауссиан по 5 точкам (log + 5QA)."""
    A = np.asarray(A, dtype=float)
    x = np.asarray(x, dtype=float)
    h = x[1] - x[0]
    if np.any(A <= 1e-15):
        return qa_5pt(A, x)
    z = np.log(A)
    peak, _ = lsq5_peak(z)
    return float(x[2] + h * peak)


# ─── График 1: Пример сигнала — нормальный и монотонный ──────────────────────

def plot_example():
    """Три ситуации: нормальная, граничная, монотонная."""
    cases = [
        (0.0,     "x0 = 0   (нормальный)\nПик в центре окна"),
        (0.35,    f"x0 = {0.35:.2f}  (переходный)\nПик у края 3-точечного окна"),
        (0.7,     f"x0 = {0.7:.2f}  (монотонный для 3pt)\nПик вне 3-точечного окна"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Монотонный режим: что происходит когда пик выходит за пределы 3 отсчётов",
        fontsize=13, y=1.02
    )

    x_cont = np.linspace(-1.5, 2.5, 500)

    for ax, (x0, title) in zip(axes, cases):
        # Непрерывный сигнал
        y_cont = hanning_kernel((x_cont - x0) / STEP)
        ax.plot(x_cont, y_cont, color='#888888', lw=1.2, label='Сигнал H(x)')

        # 3-точечные отсчёты
        A3 = sample(x0, GRID_3PT)
        ax.scatter(GRID_3PT, A3, color='#4ECDC4', s=80, zorder=5,
                   marker='o', label='3pt отсчёты')

        # 5-точечные отсчёты
        A5 = sample(x0, GRID_5PT)
        ax.scatter(GRID_5PT, A5, color='#FFE66D', s=50, zorder=4,
                   marker='^', alpha=0.8, label='5pt отсчёты')

        # Оценки
        xe_qa  = qa_3pt(A3, GRID_3PT)
        xe_5ea = ea_5pt(A5, GRID_5PT)

        ax.axvline(x0,     color='white',   lw=1.5, ls='--', label=f'Истинный x0={x0:.2f}')
        ax.axvline(xe_qa,  color='#FF6B6B', lw=1.5, ls='-',  label=f'QA(3pt) = {xe_qa:.2f}')
        ax.axvline(xe_5ea, color='#98FB98', lw=1.5, ls='-.',  label=f'5EA = {xe_5ea:.2f}')

        # Зоны сетки
        ax.axvspan(GRID_3PT[0], GRID_3PT[-1], alpha=0.08, color='cyan',
                   label='3pt окно')
        ax.axvspan(GRID_5PT[0], GRID_5PT[-1], alpha=0.05, color='yellow',
                   label='5pt окно')

        ax.set_title(title, fontsize=10)
        ax.set_xlabel('Координата x')
        ax.set_ylabel('Амплитуда')
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(True, alpha=0.2)
        ax.set_xlim(-1.5, 2.5)

    plt.tight_layout()
    path = OUT_CLEAN / "monotonic_example.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 2_no_noise/{path.name}")


# ─── График 2: Ошибка без шума, полный диапазон x0 ───────────────────────────

def plot_bias_full():
    """Bias QA(3pt) vs 5QA vs 5EA по всему диапазону x0."""
    shifts = np.linspace(0.0, MONO_5PT * 1.3, 300)

    errors_qa3  = []
    errors_5qa  = []
    errors_5ea  = []

    for x0 in shifts:
        A3 = sample(x0, GRID_3PT)
        A5 = sample(x0, GRID_5PT)
        errors_qa3.append(qa_3pt(A3, GRID_3PT) - x0)
        errors_5qa.append(qa_5pt(A5, GRID_5PT) - x0)
        errors_5ea.append(ea_5pt(A5, GRID_5PT) - x0)

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(shifts / STEP, errors_qa3, color='#FF6B6B', lw=2.0, ls='-',  label='QA (3 точки)')
    ax.plot(shifts / STEP, errors_5qa, color='#4ECDC4', lw=1.8, ls='--', label='5QA (МНК-5, парабола)')
    ax.plot(shifts / STEP, errors_5ea, color='#98FB98', lw=2.0, ls='-',  label='5EA (МНК-5, гауссиан)')

    ax.axhline(0, color='white', lw=0.5, alpha=0.4)

    # Границы режимов
    ax.axvline(MONO_3PT / STEP, color='#FF6B6B', lw=1.0, ls=':', alpha=0.7)
    ax.axvline(MONO_5PT / STEP, color='#98FB98', lw=1.0, ls=':', alpha=0.7)

    # Закрашенные зоны
    ax.axvspan(0, MONO_3PT / STEP, alpha=0.07, color='white',
               label=f'Нормальная зона QA (|x0|<{MONO_3PT:.2f})')
    ax.axvspan(MONO_3PT / STEP, MONO_5PT / STEP, alpha=0.10, color='#FF6B6B',
               label=f'Монотонно для 3pt, норм. для 5pt')
    ax.axvspan(MONO_5PT / STEP, shifts[-1] / STEP, alpha=0.10, color='gray',
               label=f'Монотонно для обоих')

    ax.set_xlabel('Смещение пика  x0 / step  (в единицах шага сетки)', fontsize=12)
    ax.set_ylabel('Систематическая ошибка  xe − x0', fontsize=12)
    ax.set_title('QA(3pt) vs МНК-5: ошибка в нормальной и монотонной зоне (без шума)',
                 fontsize=13)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, alpha=0.25)

    path = OUT_CLEAN / "monotonic_bias.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 2_no_noise/{path.name}")


# ─── График 3: MC в монотонной зоне — ошибка vs SNR ──────────────────────────

def plot_monotonic_noise():
    """Монте-Карло в монотонной зоне (x0 ∈ [MONO_3PT, MONO_5PT])."""
    np.random.seed(42)

    snr_db_range = list(range(0, 41, 2))
    # x0 — только в монотонной для 3pt зоне
    x0_range = np.linspace(MONO_3PT * 1.1, MONO_5PT * 0.85, 12)
    n_trials = 500

    med_qa3 = []
    med_5qa = []
    med_5ea = []

    for snr_db in snr_db_range:
        snr_lin = 10 ** (snr_db / 20.0)
        err_qa3, err_5qa, err_5ea = [], [], []

        for x0 in x0_range:
            for _ in range(n_trials):
                A3_c = sample(x0, GRID_3PT)
                A5_c = sample(x0, GRID_5PT)

                # Добавляем гауссов шум (σ = max(A) / SNR)
                sigma = float(np.max(A5_c)) / snr_lin
                A3 = np.abs(A3_c + np.random.randn(3) * sigma)
                A5 = np.abs(A5_c + np.random.randn(5) * sigma)

                err_qa3.append(abs(qa_3pt(A3, GRID_3PT) - x0))
                err_5qa.append(abs(qa_5pt(A5, GRID_5PT) - x0))
                err_5ea.append(abs(ea_5pt(A5, GRID_5PT) - x0))

        med_qa3.append(np.median(err_qa3))
        med_5qa.append(np.median(err_5qa))
        med_5ea.append(np.median(err_5ea))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(snr_db_range, med_qa3, color='#FF6B6B', lw=2.0, ls='-',  label='QA (3 точки)')
    ax.semilogy(snr_db_range, med_5qa, color='#4ECDC4', lw=1.8, ls='--', label='5QA (МНК-5, парабола)')
    ax.semilogy(snr_db_range, med_5ea, color='#98FB98', lw=2.0, ls='-',  label='5EA (МНК-5, гауссиан)')

    ax.set_xlabel('ОСШ (SNR, дБ)', fontsize=12)
    ax.set_ylabel('Медиана |xe − x0|  (лог. шкала)', fontsize=12)
    ax.set_title(
        f'Монотонный режим: QA(3pt) vs МНК-5 при шуме\n'
        f'(x0 ∈ [{MONO_3PT:.2f}, {MONO_5PT*0.85:.2f}] — пик ВНЕ 3-точечного окна)',
        fontsize=12
    )
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.25, which='both')

    path = OUT_NOISE / "monotonic_error_vs_snr.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 3_noise/{path.name}")


# ─── Графики 4+5: 3D поверхность 5EA: f(x0, SNR) ────────────────────────────

def compute_3d_surface(x0_range, snr_range, n_trials=400):
    """Монте-Карло: медиана |ошибки| 5EA как функция (x0, SNR)."""
    np.random.seed(42)
    Z = np.zeros((len(snr_range), len(x0_range)))

    for j, x0 in enumerate(x0_range):
        A5_clean = sample(x0, GRID_5PT)
        sig_max = float(np.max(A5_clean))

        for i, snr_db in enumerate(snr_range):
            snr_lin = 10 ** (snr_db / 20.0)
            sigma = sig_max / snr_lin
            errs = []
            for _ in range(n_trials):
                A5 = np.abs(A5_clean + np.random.randn(5) * sigma)
                errs.append(abs(ea_5pt(A5, GRID_5PT) - x0))
            Z[i, j] = np.median(errs)

    return Z


def plot_surface_3d(X0, SNR, Z):
    """График 4: 3D-поверхность."""
    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(111, projection='3d')

    XX, YY = np.meshgrid(X0 / STEP, SNR)
    surf = ax.plot_surface(XX, YY, Z, cmap='plasma', edgecolor='none', alpha=0.9)
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Медиана |xe − x0|')

    # Граница монотонной зоны для 3pt
    mono_idx = np.searchsorted(X0, MONO_3PT)
    if mono_idx < len(X0):
        ax.plot([MONO_3PT / STEP] * len(SNR), SNR,
                Z[:, mono_idx], color='cyan', lw=1.5, alpha=0.7,
                label=f'Граница 3pt (x0={MONO_3PT:.2f})')

    ax.set_xlabel('x0 / step', fontsize=10, labelpad=8)
    ax.set_ylabel('SNR (дБ)', fontsize=10, labelpad=8)
    ax.set_zlabel('Медиана |ошибки|', fontsize=10, labelpad=8)
    ax.set_title('5EA: точность как функция смещения x0 и ОСШ\n'
                 '(включая монотонную зону — правая часть графика)', fontsize=12)
    ax.legend(fontsize=8)

    path = OUT_3D / "surface_5ea_x0_snr.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 4_3d/{path.name}")


def plot_heatmap(X0, SNR, Z):
    """График 5: Тепловая карта (вид сверху)."""
    fig, ax = plt.subplots(figsize=(11, 6))

    extent = [X0[0] / STEP, X0[-1] / STEP, SNR[0], SNR[-1]]
    im = ax.imshow(Z, aspect='auto', origin='lower', extent=extent,
                   cmap='plasma', interpolation='bilinear')
    fig.colorbar(im, ax=ax, label='Медиана |xe − x0|')

    # Граница монотонного режима
    ax.axvline(MONO_3PT / STEP, color='cyan', lw=1.5, ls='--',
               label=f'3pt монотонен при x0 > {MONO_3PT:.2f}')
    ax.axvline(MONO_5PT / STEP, color='#98FB98', lw=1.5, ls='--',
               label=f'5pt монотонен при x0 > {MONO_5PT:.2f}')

    ax.set_xlabel('x0 / step  (смещение пика в единицах шага)', fontsize=12)
    ax.set_ylabel('ОСШ (SNR, дБ)', fontsize=12)
    ax.set_title('5EA: тепловая карта ошибки f(x0, SNR)\n'
                 'Тёмно = малая ошибка (хорошо). Правая зона = монотонный режим.',
                 fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(False)

    path = OUT_3D / "heatmap_5ea_x0_snr.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  [OK] 4_3d/{path.name}")


# ─── main ──────────────────────────────────────────────────────────────────────

def main():
    print("10_monotonic_and_3d.py: монотонный режим + 3D поверхность 5EA")
    print(f"  Сетка: step={STEP}, 3pt=[{GRID_3PT[0]:.1f},{GRID_3PT[-1]:.1f}], "
          f"5pt=[{GRID_5PT[0]:.1f},{GRID_5PT[-1]:.1f}]")
    print(f"  Монотонность: 3pt при |x0|>{MONO_3PT:.2f}, 5pt при |x0|>{MONO_5PT:.2f}")

    print("\n[1/5] Пример сигналов...")
    plot_example()

    print("[2/5] Bias без шума (полный диапазон)...")
    plot_bias_full()

    print("[3/5] Монте-Карло в монотонной зоне (≈30 сек)...")
    plot_monotonic_noise()

    print("[4/5] Вычисление 3D поверхности 5EA (≈60 сек)...")
    x0_range = np.linspace(0, MONO_5PT * 1.2, 40)
    snr_range = np.arange(2, 42, 2)
    Z = compute_3d_surface(x0_range, snr_range, n_trials=300)

    print("[5/5] Рисуем 3D + тепловую карту...")
    plot_surface_3d(x0_range, snr_range, Z)
    plot_heatmap(x0_range, snr_range, Z)

    print(f"\nГотово! Файлы:")
    print(f"  {OUT_CLEAN}/monotonic_example.png")
    print(f"  {OUT_CLEAN}/monotonic_bias.png")
    print(f"  {OUT_NOISE}/monotonic_error_vs_snr.png")
    print(f"  {OUT_3D}/surface_5ea_x0_snr.png")
    print(f"  {OUT_3D}/heatmap_5ea_x0_snr.png")


if __name__ == "__main__":
    main()
