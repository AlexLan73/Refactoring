"""
test_fft_frequency_plot.py -- Графики FFT-дискриминаторов (Primer.m)
====================================================================

Воспроизводит MatLab-пример Primer.m:
  1. Дискриминационная характеристика (3×3 фигура)
  2. Ошибка метода EXP vs. смещение (sweep)
  3. Ошибка EXP vs. размер FFT (N)

Запуск:
    python test_python/test_fft_frequency_plot.py
"""
import sys
import numpy as np
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("dark_background")
except ImportError:
    print("[SKIP] matplotlib не установлен")
    sys.exit(0)

# Используем реализации из test_fft_frequency.py
sys.path.insert(0, str(Path(__file__).parent))
from test_fft_frequency import (
    create_signal, compute_fft, make_freq_axis,
    METHODS, fft_discr_exp,
)

OUT_DIR = Path(__file__).resolve().parent.parent / "Doc" / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────── #
#  Plot 4: Дискриминационная характеристика (3×3, как Primer.m)       #
# ─────────────────────────────────────────────────────────────────── #

def plot4_primer_m():
    """Полное воспроизведение Primer.m: sweep 65 точек, 5 методов."""
    N, fd = 32, 12e6
    nfft = N
    df = fd / N
    n_pts = 65

    f_axis = make_freq_axis(nfft, fd)
    fsin = np.linspace(-df/2, df/2, n_pts)

    f_est = {m: np.zeros(n_pts) for m in METHODS}
    a_est = {m: np.zeros(n_pts) for m in METHODS}
    ffts_all = np.zeros((n_pts, nfft), dtype=complex)

    for i, fs in enumerate(fsin):
        sig = create_signal(fs, fd, N, an=1e-9)
        spec = compute_fft(sig, nfft)
        ffts_all[i] = spec
        for m, func in METHODS.items():
            fe = func(spec, f_axis)
            f_est[m][i] = fe
            a_est[m][i] = np.abs(spec[np.argmax(np.abs(spec))])

    STYLE = {"lay": "ro-", "exp": "ms-", "sqr": "kd-", "sd": "g^-", "cg": "cv-"}

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle("Дискриминационная характеристика FFT-дискриминаторов (Primer.m)", fontsize=13)

    # Верх: 3 спектра
    for pos, (idx, title) in enumerate([(0, "Первая"), (32, "Средняя"), (64, "Последняя")]):
        ax = fig.add_subplot(3, 3, pos + 1)
        ax.plot(f_axis, 20*np.log10(np.abs(ffts_all[idx])+1e-60), "c.-", lw=0.8)
        fm = f_est["exp"][idx]
        am = a_est["exp"][idx]
        ax.plot(fm, 20*np.log10(am+1e-60), "r*", ms=12, label=f"exp={fm/1e3:.1f}k")
        ax.set_title(f"{title} точка"); ax.set_xlabel("Гц"); ax.set_ylabel("дБ")
        ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    # Середина: оценки
    ax4 = fig.add_subplot(3, 3, (4, 6))
    ax4.plot(np.arange(1, n_pts+1), fsin, "b.-", lw=1.2, label="true")
    for m, sty in STYLE.items():
        ax4.plot(np.arange(1, n_pts+1), f_est[m], sty, lw=0.8, ms=3, label=f"f{m}")
    ax4.set_xlabel("Номер точки"); ax4.set_ylabel("Частота, Гц")
    ax4.set_ylim(-df*1.05, df*1.05); ax4.legend(fontsize=7, ncol=3); ax4.grid(True, alpha=0.3)

    # Низ: ошибки
    ax5 = fig.add_subplot(3, 3, (7, 9))
    for m, sty in STYLE.items():
        err = np.clip(fsin - f_est[m], -df*1.1, df*1.1)
        ax5.plot(fsin, err, sty, lw=0.8, ms=3, label=f"err{m}")
    ax5.set_xlabel(f"Частота, Гц   fd/N={df:.0f}"); ax5.set_ylabel("Ошибка, Гц")
    ax5.set_ylim(-df*1.1, df*1.1); ax5.legend(fontsize=7, ncol=3); ax5.grid(True, alpha=0.3)

    fig.tight_layout()
    path = OUT_DIR / "fft_primer_m.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Plot 4] {path}")


# ─────────────────────────────────────────────────────────────────── #
#  Plot 5: Ошибка EXP vs. смещение + сравнение окон                   #
# ─────────────────────────────────────────────────────────────────── #

def plot5_exp_error_and_windows():
    """Ошибка EXP: sweep + сравнение окон Hamming/Blackman/Kaiser."""
    N, fd = 32, 12e6
    df = fd / N
    n_pts = 41
    fsin_arr = np.linspace(-df/4, df/4, n_pts)
    windows = {"hamming": "c", "hann": "g", "blackman": "r"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Метод EXP: ошибка и влияние окна", fontsize=12)

    # Левый: ошибка всех 5 методов (окно Hamming)
    for m, func in METHODS.items():
        errs = []
        for fs in fsin_arr:
            sig = create_signal(fs, fd, N, an=0)
            spec = compute_fft(sig, N, "hamming")
            f_axis = make_freq_axis(N, fd)
            errs.append(abs(fs - func(spec, f_axis)))
        ax1.plot(fsin_arr/1e3, [e/1e3 for e in errs], lw=1.2,
                 label=f"{m} (mean={np.mean(errs)/1e3:.1f}k)")
    ax1.set_xlabel("fsin, кГц"); ax1.set_ylabel("|error|, кГц")
    ax1.set_title("Все методы (Hamming)"); ax1.legend(fontsize=7); ax1.grid(True, alpha=0.3)

    # Правый: EXP с разными окнами
    for wname, color in windows.items():
        errs = []
        for fs in fsin_arr:
            sig = create_signal(fs, fd, N, an=0)
            spec = compute_fft(sig, N, wname)
            f_axis = make_freq_axis(N, fd)
            errs.append(abs(fs - fft_discr_exp(spec, f_axis)))
        ax2.plot(fsin_arr/1e3, [e/1e3 for e in errs], color+"-", lw=1.5,
                 label=f"{wname} ({np.mean(errs)/1e3:.1f}k)")
    ax2.set_xlabel("fsin, кГц"); ax2.set_ylabel("|error|, кГц")
    ax2.set_title("Метод EXP: разные окна"); ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    path = OUT_DIR / "fft_exp_error_windows.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Plot 5] {path}")


# ─────────────────────────────────────────────────────────────────── #

if __name__ == "__main__":
    print("=== FFT Discriminator Plots (Primer.m) ===")
    plot4_primer_m()
    plot5_exp_error_and_windows()
    print(f"\nГрафики: {OUT_DIR}")
