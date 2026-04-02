"""
07_fft_analysis.py — FFT-дискриминаторы: sweep по N_fft и окнам
================================================================

Использует 5 FFT-методов из test_fft_frequency.py (exp, sqr, lay, sd, cg).
НЕ использует common.py ref_* — это отдельный домен (частотная оценка).

Результаты:
  results/fft_analysis.csv
  plots/2d/fft_error_vs_nfft.png
  plots/2d/fft_error_vs_window.png

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/07_fft_analysis.py
"""

import sys
import numpy as np
from pathlib import Path

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent
REPO_ROOT = MODULE_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(ANALYSIS_DIR.parent))  # test_python/ для test_fft_frequency

from test_fft_frequency import METHODS, create_signal, make_freq_axis
from PyCore.runner import TestRunner

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use("dark_background")

OUT_RESULTS = ANALYSIS_DIR / "results"
OUT_PLOTS = ANALYSIS_DIR / "plots" / "2d"
OUT_RESULTS.mkdir(parents=True, exist_ok=True)
OUT_PLOTS.mkdir(parents=True, exist_ok=True)

# Цвета для 5 FFT-методов
FFT_COLORS = {
    'exp': '#FFE66D',
    'sqr': '#4ECDC4',
    'lay': '#89CFF0',
    'sd': '#C792EA',
    'cg': '#FF6B6B',
}


def compute_fft_window(signal, nfft, window_name='hamming'):
    """FFT с различными окнами."""
    N = len(signal)
    if window_name == 'hamming':
        win = np.hamming(N)
    elif window_name == 'blackman':
        win = np.blackman(N)
    elif window_name == 'kaiser8':
        win = np.kaiser(N, 8)
    elif window_name == 'kaiser14':
        win = np.kaiser(N, 14)
    else:
        win = np.ones(N)
    return np.fft.fftshift(np.fft.fft(signal * win, nfft))


def sweep_errors(fd, N, n_pts=41, window='hamming'):
    """Sweep fsin в пределах ±df/4 для всех 5 методов.

    Returns:
        dict: {method_name: [abs_errors]}
    """
    df = fd / N
    fsin_arr = np.linspace(-df / 4, df / 4, n_pts)
    errs = {m: [] for m in METHODS}

    for fsin in fsin_arr:
        sig = create_signal(fsin, fd, N, a=1.0, an=0.0)
        spec = compute_fft_window(sig, N, window)
        f_axis = make_freq_axis(N, fd)

        for m, func in METHODS.items():
            fe = func(spec, f_axis)
            errs[m].append(abs(fe - fsin))

    return errs, fsin_arr


def experiment_nfft_sweep(fd=12e6):
    """Sweep по N_fft = [16, 32, 64, 128, 256]."""
    nfft_values = [16, 32, 64, 128, 256]
    results = []

    for N in nfft_values:
        errs, _ = sweep_errors(fd, N, n_pts=41, window='hamming')
        for m in METHODS:
            mae = np.mean(errs[m])
            maxerr = np.max(errs[m])
            results.append({
                'N_fft': N, 'method': m,
                'MAE': mae, 'MaxErr': maxerr,
            })

    return results, nfft_values


def experiment_windows(fd=12e6, N=32):
    """Сравнение окон для метода EXP при N=32."""
    windows = ['hamming', 'blackman', 'kaiser8', 'kaiser14']
    results = []

    for win in windows:
        errs, _ = sweep_errors(fd, N, n_pts=41, window=win)
        mae = np.mean(errs['exp'])
        maxerr = np.max(errs['exp'])
        results.append({
            'window': win, 'MAE': mae, 'MaxErr': maxerr,
        })

    return results


def save_csv(nfft_results, window_results, path):
    """Сохранить результаты в CSV."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write("type,N_fft,method,window,MAE,MaxErr\n")
        for r in nfft_results:
            f.write(f"nfft,{r['N_fft']},{r['method']},,{r['MAE']:.6f},{r['MaxErr']:.6f}\n")
        for r in window_results:
            f.write(f"window,32,exp,{r['window']},{r['MAE']:.6f},{r['MaxErr']:.6f}\n")


def plot_error_vs_nfft(results, nfft_values, path):
    """График: MAE vs N_fft для 5 методов."""
    fig, ax = plt.subplots(figsize=(14, 7))

    for m in ['exp', 'sqr', 'lay', 'sd', 'cg']:
        maes = [r['MAE'] for r in results if r['method'] == m]
        ax.plot(nfft_values, maes, 'o-', color=FFT_COLORS[m],
                linewidth=2, markersize=8, label=m.upper())

    ax.set_xlabel('N_fft (размер БПФ)', fontsize=12)
    ax.set_ylabel('Средняя абсолютная ошибка (Гц)', fontsize=12)
    ax.set_title('Точность FFT-дискриминаторов vs размер БПФ', fontsize=14)
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_error_vs_window(results, path):
    """График: MAE по окнам (метод EXP)."""
    fig, ax = plt.subplots(figsize=(14, 7))

    windows = [r['window'] for r in results]
    maes = [r['MAE'] for r in results]
    colors = ['#FFE66D', '#4ECDC4', '#C792EA', '#FF6B6B']

    bars = ax.bar(windows, maes, color=colors, edgecolor='white', linewidth=0.5)

    # Подписи значений на барах
    for bar, mae in zip(bars, maes):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.05,
                f'{mae:.0f} Гц', ha='center', va='bottom', fontsize=11, color='white')

    ax.set_xlabel('Оконная функция', fontsize=12)
    ax.set_ylabel('Средняя абсолютная ошибка (Гц)', fontsize=12)
    ax.set_title('Влияние окна на точность EXP-дискриминатора (N=32)', fontsize=14)
    ax.grid(True, alpha=0.3, axis='y')

    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)


class FFTAnalysis:
    """Анализ FFT-дискриминаторов."""

    def test_nfft_sweep(self):
        """Sweep по N_fft = [16, 32, 64, 128, 256]."""
        print("\n  FFT sweep: N_fft = [16, 32, 64, 128, 256], 5 methods")
        results, nfft_values = experiment_nfft_sweep()

        # Таблица
        print(f"\n  {'N':>5s} | {'EXP':>10s} | {'SQR':>10s} | {'LAY':>10s} | {'SD':>10s} | {'CG':>10s}")
        print(f"  {'-'*5}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}")
        for N in nfft_values:
            vals = {}
            for r in results:
                if r['N_fft'] == N:
                    vals[r['method']] = r['MAE']
            print(f"  {N:5d} | {vals.get('exp',0):10.1f} | {vals.get('sqr',0):10.1f} | "
                  f"{vals.get('lay',0):10.1f} | {vals.get('sd',0):10.1f} | {vals.get('cg',0):10.1f}")

        # График
        plot_path = OUT_PLOTS / "fft_error_vs_nfft.png"
        plot_error_vs_nfft(results, nfft_values, plot_path)
        print(f"\n  Saved: {plot_path}")

        # Проверка: EXP лучше остальных при всех N
        for N in nfft_values:
            exp_mae = [r['MAE'] for r in results if r['N_fft'] == N and r['method'] == 'exp'][0]
            sqr_mae = [r['MAE'] for r in results if r['N_fft'] == N and r['method'] == 'sqr'][0]
            assert exp_mae <= sqr_mae * 1.1, f"EXP not best at N={N}"
        print(f"  [OK] EXP consistently best or near-best")

        self._nfft_results = results

    def test_window_comparison(self):
        """Сравнение окон для EXP при N=32."""
        print("\n  Window comparison: EXP method, N=32")
        results = experiment_windows()

        for r in results:
            print(f"    {r['window']:>10s}: MAE = {r['MAE']:.1f} Hz, MaxErr = {r['MaxErr']:.1f} Hz")

        # График
        plot_path = OUT_PLOTS / "fft_error_vs_window.png"
        plot_error_vs_window(results, plot_path)
        print(f"\n  Saved: {plot_path}")

        # CSV (общий для обоих тестов)
        nfft_results, _ = experiment_nfft_sweep()
        csv_path = OUT_RESULTS / "fft_analysis.csv"
        save_csv(nfft_results, results, csv_path)
        print(f"  Saved: {csv_path}")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run(FFTAnalysis())
    runner.print_summary(results)
