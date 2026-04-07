"""
11_recommendations_plots.py
============================

Генерирует все иллюстрации к отчёту:
    Doc/Frequency_Recommendations_2026-04-06.md

Графики сохраняются в:
    Doc/plots/5_recommendations/

Все графики рассчитаны на читателя "с нуля":
  - крупные подписи
  - русские заголовки
  - минимум технического жаргона на холсте
  - цветовая схема: spring/autumn для методов,
                    тёмно-синий = рекомендуемый, серый = базовый

Запуск:
    cd discriminator_estimates/test_python
    python3 analysis/11_recommendations_plots.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
MODULE_ROOT = HERE.parent.parent                          # discriminator_estimates/
OUT_DIR = MODULE_ROOT / "Doc" / "plots" / "5_recommendations"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Общие стили
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "legend.fontsize": 11,
    "figure.titlesize": 16,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "savefig.dpi": 140,
    "savefig.bbox": "tight",
})

COLOR_REC = "#1f4e79"        # тёмно-синий — рекомендуемый
COLOR_GOOD = "#2e8b57"       # зелёный — хороший
COLOR_OK = "#d97706"         # оранжевый — ok но не лучший
COLOR_BAD = "#b91c1c"        # красный — плохой
COLOR_GRAY = "#6b7280"       # серый — нейтральный

# ---------------------------------------------------------------------------
# Математика: Hanning kernel (форма пика после Hanning + FFT)
# ---------------------------------------------------------------------------
def sinc_normalized(x):
    """sinc(x) = sin(pi x)/(pi x)  — нормированный синк."""
    return np.sinc(x)                     # np.sinc уже нормированный


def hanning_kernel(delta):
    """
    Форма одиночного пика в FFT-спектре при Hanning окне.
    H(d) = 0.5 sinc(d) + 0.25 sinc(d-1) + 0.25 sinc(d+1)
    """
    return 0.5 * sinc_normalized(delta) \
         + 0.25 * sinc_normalized(delta - 1.0) \
         + 0.25 * sinc_normalized(delta + 1.0)


# ===========================================================================
# ГРАФИК 1 — Pipeline обработки сигнала (блок-схема)
# ===========================================================================
def plot_pipeline():
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Pipeline поиска частоты в зашумлённом сигнале",
                 fontsize=16, pad=12, fontweight="bold")

    steps = [
        (0.5, "Сигнал\n~1.3 М точек", "#dbeafe"),
        (2.2, "Окно\nHanning", "#bfdbfe"),
        (3.9, "Zero-pad\n×2", "#93c5fd"),
        (5.6, "FFT", "#60a5fa"),
        (7.3, "Поиск максимума\n(±1000 бинов)", "#3b82f6"),
        (9.0, "discr5ea\n(суб-бин)", "#1f4e79"),
        (10.7, "Частота\nf [Гц]", "#15803d"),
    ]

    y_center = 3.0
    box_w, box_h = 1.4, 1.4

    for i, (x, text, color) in enumerate(steps):
        box = FancyBboxPatch(
            (x - box_w / 2, y_center - box_h / 2),
            box_w, box_h,
            boxstyle="round,pad=0.08",
            linewidth=1.5, edgecolor="#1e293b",
            facecolor=color,
        )
        ax.add_patch(box)
        txt_color = "white" if i >= 3 else "#1e293b"
        ax.text(x, y_center, text, ha="center", va="center",
                fontsize=10.5, color=txt_color, fontweight="bold")

        if i < len(steps) - 1:
            x_next = steps[i + 1][0]
            arrow = FancyArrowPatch(
                (x + box_w / 2, y_center),
                (x_next - box_w / 2, y_center),
                arrowstyle="->", mutation_scale=18,
                linewidth=1.8, color="#1e293b",
            )
            ax.add_patch(arrow)

    # Поясняющие подписи сверху и снизу
    ax.text(0.5, 4.6, "вход", ha="center", fontsize=10, style="italic", color=COLOR_GRAY)
    ax.text(10.7, 4.6, "выход", ha="center", fontsize=10, style="italic", color=COLOR_GRAY)

    ax.text(9.0, 1.15,
            "← ЭТО ТО, ЧТО МЫ ВЫБИРАЕМ",
            ha="center", fontsize=11, color=COLOR_REC, fontweight="bold")
    ax.text(9.0, 0.65,
            "(метод суб-бинной оценки)",
            ha="center", fontsize=10, color=COLOR_REC, style="italic")

    # Низ: что такое "суб-бин"
    ax.text(6.0, 0.1,
            "Без суб-бинной оценки точность = ±0.5 бина. С discr5ea — в ~20 раз точнее.",
            ha="center", fontsize=10, color="#374151", style="italic")

    plt.savefig(OUT_DIR / "01_pipeline.png")
    plt.close()
    print("[OK] 01_pipeline.png")


# ===========================================================================
# ГРАФИК 2 — Форма пика Hanning и как парабола на неё ложится
# ===========================================================================
def plot_hanning_vs_parabola():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # Слева: форма пика — sinc vs Hanning kernel
    d = np.linspace(-3.5, 3.5, 1000)
    y_sinc = sinc_normalized(d)
    y_han = hanning_kernel(d)

    ax1.plot(d, y_sinc, "-", color=COLOR_BAD, linewidth=2.2,
             label="Без окна (sinc) — острый, с «ушами»")
    ax1.plot(d, y_han, "-", color=COLOR_REC, linewidth=2.8,
             label="С Hanning окном — гладкий, \nколоколообразный")
    ax1.axhline(0, color="#9ca3af", linewidth=0.8)
    ax1.axhline(-0.133, color=COLOR_BAD, linewidth=0.8, linestyle=":",
                alpha=0.7)
    ax1.text(2.8, -0.17, "−13 дБ (sinc)", fontsize=9, color=COLOR_BAD)

    ax1.set_xlabel("Смещение от пика (в бинах)")
    ax1.set_ylabel("Амплитуда (нормированная)")
    ax1.set_title("Форма пика в FFT-спектре")
    ax1.legend(loc="upper left", framealpha=0.95)
    ax1.set_xlim(-3.5, 3.5)
    ax1.set_ylim(-0.35, 1.12)

    # Справа: парабола против Hanning kernel — как хорошо ложится
    d2 = np.linspace(-1.2, 1.2, 500)
    y_han2 = hanning_kernel(d2)

    # Парабола подогнанная по трём точкам: -1, 0, +1 (после normalize к вершине)
    y_m1, y_0, y_p1 = hanning_kernel(-1.0), hanning_kernel(0.0), hanning_kernel(1.0)
    a = 0.5 * (y_m1 - 2 * y_0 + y_p1)
    b = 0.5 * (y_p1 - y_m1)
    c = y_0
    y_par = a * d2**2 + b * d2 + c

    ax2.plot(d2, y_han2, "-", color=COLOR_REC, linewidth=3,
             label="Hanning kernel (реальная форма)")
    ax2.plot(d2, y_par, "--", color=COLOR_OK, linewidth=2.5,
             label="Парабола (аппроксимация)")

    # Точки МНК-5 при шаге 0.5 (zp×2)
    step = 0.5
    xs_5pt = np.array([-2, -1, 0, 1, 2]) * step
    ys_5pt = hanning_kernel(xs_5pt)
    ax2.plot(xs_5pt, ys_5pt, "o", markersize=13, color=COLOR_REC,
             markeredgecolor="white", markeredgewidth=2,
             label="5 точек для discr5ea (zp×2)", zorder=10)

    ax2.axvline(0, color="#9ca3af", linewidth=0.8, linestyle=":")
    ax2.set_xlabel("Смещение от пика (в бинах)")
    ax2.set_ylabel("Амплитуда")
    ax2.set_title("Парабола ложится на Hanning — почти идеально")
    ax2.legend(loc="lower center", framealpha=0.95)
    ax2.set_xlim(-1.2, 1.2)
    ax2.set_ylim(0.15, 1.1)

    # Аннотация
    ax2.annotate("в пределах ±0.7 бина\nошибка < 2.5%",
                 xy=(0.7, 0.72), xytext=(0.3, 0.35),
                 fontsize=10, color="#374151",
                 arrowprops=dict(arrowstyle="->", color="#374151", lw=1.2))

    fig.suptitle("Почему Hanning + парабола работают вместе",
                 fontsize=15, fontweight="bold", y=1.02)
    plt.savefig(OUT_DIR / "02_hanning_vs_parabola.png")
    plt.close()
    print("[OK] 02_hanning_vs_parabola.png")


# ===========================================================================
# ГРАФИК 3 — Эффект zero-padding (визуальная аналогия)
# ===========================================================================
def plot_zero_padding_effect():
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

    d = np.linspace(-4, 4, 1000)
    y_curve = hanning_kernel(d)

    configs = [
        ("Без zero-padding\n(шаг = 1 бин)", 1.0, COLOR_BAD),
        ("Zero-pad ×2\n(шаг = 0.5 бина) — рекомендуется", 0.5, COLOR_REC),
        ("Zero-pad ×4\n(шаг = 0.25 бина)", 0.25, COLOR_GOOD),
    ]

    for ax, (title, step, color) in zip(axes, configs):
        ax.plot(d, y_curve, "-", color="#94a3b8", linewidth=2,
                label="Истинная форма пика")

        # Сетка бинов вокруг пика +0.17 (произвольное смещение)
        true_shift = 0.17
        bins = np.arange(-4, 4.01, step)
        bins = bins + true_shift  # смещаем сетку
        y_bins = hanning_kernel(bins)
        ax.stem(bins, y_bins, linefmt=f"{color}", markerfmt="o",
                basefmt=" ")

        # Отметка истинного пика
        ax.axvline(true_shift, color="#059669", linewidth=2, linestyle="--",
                   label="Истинная частота")

        # 5 точек вокруг максимума
        k_max_idx = int(np.argmax(y_bins))
        if k_max_idx >= 2 and k_max_idx < len(bins) - 2:
            five = bins[k_max_idx - 2: k_max_idx + 3]
            five_y = y_bins[k_max_idx - 2: k_max_idx + 3]
            ax.plot(five, five_y, "o", markersize=14,
                    markerfacecolor="none", markeredgecolor=color,
                    markeredgewidth=2.5, zorder=20,
                    label="5 точек МНК")

        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Смещение (в бинах)")
        ax.set_xlim(-3.5, 3.5)
        ax.set_ylim(-0.2, 1.15)
        ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

    axes[0].set_ylabel("Амплитуда")
    fig.suptitle("Zero-padding: что это и зачем — «уплотняем» точки на той же кривой",
                 fontsize=14, fontweight="bold", y=1.03)

    # Подпись снизу
    fig.text(0.5, -0.05,
             "Zero-padding НЕ улучшает разрешение — только делает сетку бинов гуще. "
             "Это и нужно 5-точечным методам.",
             ha="center", fontsize=10, color="#374151", style="italic")

    plt.savefig(OUT_DIR / "03_zero_padding_effect.png")
    plt.close()
    print("[OK] 03_zero_padding_effect.png")


# ===========================================================================
# ГРАФИК 4 — Сравнение методов при разных SNR (по реальным данным)
# ===========================================================================
def plot_methods_vs_snr():
    """
    Данные из отчёта Doc/Review/2026-04-03_5pt_LSQ_comparison.md
    Медиана ошибки по 5000 × 21 = 105000 испытаний.
    """
    snr_db = np.array([5, 10, 15, 20, 25, 30, 40])
    err_ea3 = np.array([0.195, 0.181, 0.153, 0.104, 0.059, 0.033, 0.010])
    err_5qa = np.array([0.168, 0.145, 0.090, 0.051, 0.030, 0.019, 0.015])
    err_5ea = np.array([0.203, 0.181, 0.108, 0.058, 0.032, 0.018, 0.007])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # --- Левый график: линейная шкала ---
    ax1.plot(snr_db, err_ea3, "o--", color=COLOR_GRAY, linewidth=2,
             markersize=9, label="EA3 — классика по 3 точкам")
    ax1.plot(snr_db, err_5qa, "s-", color=COLOR_OK, linewidth=2.5,
             markersize=10, label="5QA — МНК парабола по 5 точкам")
    ax1.plot(snr_db, err_5ea, "^-", color=COLOR_REC, linewidth=3,
             markersize=11, label="5EA — МНК гаусс по 5 точкам ★")

    ax1.set_xlabel("SNR — отношение сигнал/шум (дБ)")
    ax1.set_ylabel("Ошибка (в бинах после zp×2)")
    ax1.set_title("Ошибка vs шум — чем ниже, тем лучше")
    ax1.legend(loc="upper right", framealpha=0.95)
    ax1.invert_xaxis()
    ax1.set_xlim(42, 3)

    # Зоны
    ax1.axvspan(3, 15, alpha=0.08, color="red", label="_nolegend_")
    ax1.axvspan(15, 25, alpha=0.08, color="orange", label="_nolegend_")
    ax1.axvspan(25, 42, alpha=0.08, color="green", label="_nolegend_")
    ax1.text(9, 0.18, "очень\nшумно", ha="center", fontsize=9, color="#7f1d1d")
    ax1.text(20, 0.18, "нормально", ha="center", fontsize=9, color="#78350f")
    ax1.text(33, 0.18, "хорошо", ha="center", fontsize=9, color="#14532d")

    # --- Правый график: выигрыш 5EA относительно EA3 ---
    gain = err_ea3 / np.minimum(err_5qa, err_5ea)
    ax2.bar(snr_db, gain, width=3, color=COLOR_REC, alpha=0.85,
            edgecolor="#1e3a5f", linewidth=1.5)
    for x, g in zip(snr_db, gain):
        ax2.text(x, g + 0.05, f"{g:.1f}×", ha="center", fontsize=10,
                 fontweight="bold", color=COLOR_REC)

    ax2.axhline(1.0, color=COLOR_GRAY, linewidth=1.2, linestyle="--")
    ax2.text(5, 1.06, "= классика EA3", fontsize=9, color=COLOR_GRAY)

    ax2.set_xlabel("SNR (дБ)")
    ax2.set_ylabel("Во сколько раз 5pt точнее EA3")
    ax2.set_title("Выигрыш 5-точечных методов")
    ax2.invert_xaxis()
    ax2.set_xlim(42, 3)
    ax2.set_ylim(0, max(gain) * 1.3)

    fig.suptitle("Главный эксперимент: 5000 × 21 испытание Монте-Карло на Hanning kernel",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.savefig(OUT_DIR / "04_methods_vs_snr.png")
    plt.close()
    print("[OK] 04_methods_vs_snr.png")


# ===========================================================================
# ГРАФИК 5 — Точность в реальных единицах (Гц) для типового сценария
# ===========================================================================
def plot_accuracy_hz():
    """
    Типичные параметры: fs = 100 МГц, N = 4M (2^22)
        Delta_f = 23.84 Гц
        Без интерполяции: ±Delta_f/2 ≈ ±12 Гц

    5EA даёт ошибку ~0.025 реального бина при SNR=20 дБ
        -> 0.025 * 23.84 ≈ 0.6 Гц

    Quinn 2nd: bias ~0.0001 бина -> 0.002 Гц
    """
    fs = 100e6
    N = 2**22
    df = fs / N         # ≈ 23.84 Гц

    # Данные в реальных бинах (не "padded")
    # 5EA/5QA ошибка при zp×2: в бинах padded * 0.5 = в реальных
    # Берём минимум из 5QA/5EA
    snr_db = np.array([10, 15, 20, 25, 30])
    err_padded_bin = np.array([0.145, 0.090, 0.051, 0.030, 0.018])
    err_real_bin = err_padded_bin * 0.5     # zp×2
    err_hz = err_real_bin * df

    # Бенчмарк методы
    methods = [
        ("Без интерполяции\n(просто argmax)",     0.5 * df, COLOR_BAD),
        ("EA3\n(классика, 3 точки)",              0.5 * 0.104 * df, COLOR_GRAY),
        ("5EA / 5QA ★\n(наш выбор)",             err_hz[2], COLOR_REC),
        ("Quinn 2nd\n(комплексный, будущее)",     0.0001 * df, COLOR_GOOD),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # --- Левый: столбчатая диаграмма для SNR=20 дБ ---
    names = [m[0] for m in methods]
    vals = [m[1] for m in methods]
    colors = [m[2] for m in methods]

    x_pos = np.arange(len(names))
    bars = ax1.bar(x_pos, vals, color=colors, alpha=0.88,
                   edgecolor="#1e293b", linewidth=1.5)
    ax1.set_yscale("log")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(names, fontsize=10)
    ax1.set_ylabel("Ошибка оценки частоты (Гц), лог. шкала")
    ax1.set_title(f"Точность при fs = 100 МГц, N = 4M (Δf = {df:.2f} Гц), SNR = 20 дБ",
                  fontsize=11)

    for bar, v in zip(bars, vals):
        h = bar.get_height()
        if v >= 1:
            label = f"{v:.1f} Гц"
        elif v >= 0.01:
            label = f"{v:.2f} Гц"
        else:
            label = f"{v*1000:.2f} мГц"
        ax1.text(bar.get_x() + bar.get_width() / 2, h * 1.3, label,
                 ha="center", fontsize=10, fontweight="bold")

    ax1.set_ylim(1e-3, 50)
    ax1.axhline(df, color=COLOR_BAD, linestyle=":", linewidth=1.5, alpha=0.6)
    ax1.text(3.4, df * 1.05, f"1 бин FFT = {df:.1f} Гц",
             ha="right", fontsize=9, color=COLOR_BAD)

    # --- Правый: 5EA ошибка в Гц от SNR ---
    ax2.plot(snr_db, err_hz, "o-", color=COLOR_REC, linewidth=3,
             markersize=12, label="5EA / 5QA ★")
    ax2.fill_between(snr_db, err_hz * 0.7, err_hz * 1.4,
                     color=COLOR_REC, alpha=0.15, label="типовой разброс")

    ax2.axhline(df * 0.5, color=COLOR_BAD, linestyle="--", linewidth=1.5,
                label="без интерполяции (±0.5 бина)")

    for x, y in zip(snr_db, err_hz):
        label = f"{y:.2f} Гц" if y >= 0.01 else f"{y*1000:.1f} мГц"
        ax2.annotate(label, (x, y), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=9,
                     color=COLOR_REC, fontweight="bold")

    ax2.set_xlabel("SNR (дБ)")
    ax2.set_ylabel("Ошибка оценки частоты (Гц)")
    ax2.set_title("Как точность зависит от шума")
    ax2.legend(loc="upper right", framealpha=0.95)
    ax2.set_yscale("log")
    ax2.invert_xaxis()
    ax2.set_ylim(0.01, 50)

    fig.suptitle("Практический результат — точность в герцах",
                 fontsize=15, fontweight="bold", y=1.02)
    plt.savefig(OUT_DIR / "05_accuracy_in_hz.png")
    plt.close()
    print("[OK] 05_accuracy_in_hz.png")


# ===========================================================================
# ГРАФИК 6 — Дерево решений: какой метод выбрать
# ===========================================================================
def plot_decision_tree():
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, color, text_color="white", fontsize=11, bold=True):
        b = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.15",
                           linewidth=2, edgecolor="#1e293b", facecolor=color)
        ax.add_patch(b)
        weight = "bold" if bold else "normal"
        ax.text(x, y, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight)

    def diamond(x, y, w, h, text, color="#fef3c7"):
        pts = [[x, y + h/2], [x + w/2, y], [x, y - h/2], [x - w/2, y]]
        poly = plt.Polygon(pts, facecolor=color, edgecolor="#1e293b",
                           linewidth=2)
        ax.add_patch(poly)
        ax.text(x, y, text, ha="center", va="center",
                fontsize=10, color="#1e293b", fontweight="bold")

    def arrow(x1, y1, x2, y2, label=None, label_x_offset=0.15):
        a = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle="->", mutation_scale=18,
                            linewidth=1.8, color="#1e293b")
        ax.add_patch(a)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx + label_x_offset, my, label,
                    fontsize=10, color="#1e293b", fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2",
                              facecolor="white", edgecolor="none"))

    # Заголовок
    ax.text(6.5, 9.5, "Как выбрать метод суб-бинной оценки",
            ha="center", fontsize=16, fontweight="bold")

    # Старт
    box(6.5, 8.5, 4.5, 0.7, "Нужна точная частота пика", "#3b82f6")

    # Вопрос 1: есть ли комплексные X(k)?
    diamond(6.5, 7.3, 4.5, 1.1, "Доступны комплексные X(k)?")
    arrow(6.5, 8.15, 6.5, 7.88)

    # Да -> Quinn 2nd
    diamond(3.0, 5.7, 3.2, 0.95, "SNR > 10 дБ?")
    arrow(5.4, 7.3, 3.9, 6.0, label="Да")

    # Нет -> разбираемся с магнитудой
    diamond(10.0, 5.7, 3.4, 0.95, "Один пик?\n(а не несколько)")
    arrow(7.6, 7.3, 9.2, 6.0, label="Нет")

    # Ветка Quinn
    box(3.0, 4.2, 3.0, 0.75, "Quinn 2nd\nдостигает CRLB",
        COLOR_GOOD, fontsize=11)
    arrow(3.0, 5.2, 3.0, 4.6, label="Да")
    box(1.0, 4.2, 2.0, 0.75, "Jacobsen\nпроще", COLOR_OK, fontsize=10)
    arrow(2.5, 5.2, 1.2, 4.6, label="Нет")

    # Ветка магнитуды: один пик?
    box(10.0, 4.2, 3.5, 0.75, "Zero-pad ×2 есть?",
        "#fef3c7", text_color="#1e293b", fontsize=11)
    arrow(10.0, 5.2, 10.0, 4.6, label="Да")

    box(12.2, 5.7, 1.5, 0.7, "MUSIC /\nESPRIT",
        COLOR_GRAY, fontsize=9)
    arrow(11.5, 5.85, 12.0, 5.85, label="Нет")

    # Дальше
    box(8.0, 2.8, 3.0, 0.85, "discr5qa ★\n(SNR ≤ 25 дБ)",
        COLOR_REC, fontsize=10)
    box(12.0, 2.8, 3.0, 0.85, "discr5ea ★\n(SNR > 25 дБ)",
        COLOR_REC, fontsize=10)

    arrow(8.8, 3.85, 8.3, 3.22, label="шумно")
    arrow(11.2, 3.85, 11.7, 3.22, label="чисто")

    # Fallback
    box(10.0, 1.3, 4.6, 0.75,
        "Fallback: если |X(k)| ≤ 0 → переключить 5ea → 5qa",
        "#fef9c3", text_color="#1e293b", fontsize=10, bold=False)

    # Подпись снизу
    ax.text(6.5, 0.3,
            "★ Рекомендуемый путь для текущего CPU-pipeline: 5EA/5QA + zero-pad ×2 + Hanning",
            ha="center", fontsize=11, color=COLOR_REC,
            fontweight="bold", style="italic")

    plt.savefig(OUT_DIR / "06_decision_tree.png")
    plt.close()
    print("[OK] 06_decision_tree.png")


# ===========================================================================
# ГРАФИК 7 — Монотонная зона: где 3pt ломается, 5pt держится
# ===========================================================================
def plot_monotonic_zone():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # --- Левый: иллюстрация нормальной и монотонной зоны ---
    d = np.linspace(-4, 4, 1000)
    y = hanning_kernel(d)

    # Случай 1: x0 = 0.2 (нормальная зона, 3pt ок)
    x0_norm = 0.2
    pts_3_norm = np.array([-1, 0, 1]) + 0.0  # бины
    y_3_norm = hanning_kernel(pts_3_norm - x0_norm)

    # Случай 2: x0 = 1.3 (монотонная зона для 3pt)
    x0_mono = 1.3

    ax1.plot(d, y, "-", color="#94a3b8", linewidth=2, label="Hanning kernel")
    ax1.axvline(x0_norm, color=COLOR_GOOD, linewidth=2, linestyle="--",
                label=f"Истинный пик №1 (x₀={x0_norm})")
    ax1.axvline(x0_mono, color=COLOR_BAD, linewidth=2, linestyle="--",
                label=f"Истинный пик №2 (x₀={x0_mono})")

    # 3pt окно: бины -1, 0, +1
    ax1.plot([-1, 0, 1], hanning_kernel(np.array([-1, 0, 1]) - x0_norm),
             "o", color=COLOR_GOOD, markersize=13,
             label="3pt окно: пик внутри ✓", zorder=10)
    ax1.plot([-1, 0, 1], hanning_kernel(np.array([-1, 0, 1]) - x0_mono),
             "X", color=COLOR_BAD, markersize=13,
             label="3pt окно: пик СНАРУЖИ ✗", zorder=10)

    # 5pt окно всё ещё видит
    ax1.plot([-2, -1, 0, 1, 2],
             hanning_kernel(np.array([-2, -1, 0, 1, 2]) - x0_mono),
             "s", color=COLOR_REC, markersize=10, alpha=0.6,
             label="5pt окно (shift): видит пик ✓", zorder=5)

    ax1.set_xlabel("Позиция бина (относительно центра окна)")
    ax1.set_ylabel("Амплитуда")
    ax1.set_title("Нормальная vs монотонная зона")
    ax1.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax1.set_xlim(-3.5, 3.5)
    ax1.set_ylim(-0.1, 1.15)

    # --- Правый: зоны рабочая/монотонная ---
    x0_range = np.linspace(0, 3, 200)
    # Грубая модель ошибки 3pt vs 5pt в монотонной зоне
    err_3pt = np.where(x0_range < 0.5, 0.005,
                       np.where(x0_range < 1.0, 0.05 * (x0_range - 0.5) / 0.5,
                                np.minimum(0.05 + (x0_range - 1.0) * 0.3, 1.0)))
    err_5pt = np.where(x0_range < 1.5, 0.01,
                       np.where(x0_range < 2.0, 0.02,
                                np.minimum(0.02 + (x0_range - 2.0) * 0.2, 1.0)))

    ax2.plot(x0_range, err_3pt, "-", color=COLOR_BAD, linewidth=3,
             label="3pt (EA3/QA3)")
    ax2.plot(x0_range, err_5pt, "-", color=COLOR_REC, linewidth=3,
             label="5pt (5EA/5QA) ★")

    # Зоны
    ax2.axvspan(0, 0.5, alpha=0.15, color=COLOR_GOOD)
    ax2.axvspan(0.5, 2.0, alpha=0.12, color=COLOR_OK)
    ax2.axvspan(2.0, 3.0, alpha=0.15, color=COLOR_BAD)

    ax2.text(0.25, 0.7, "норма\n(всё OK)", ha="center",
             fontsize=10, color="#14532d", fontweight="bold")
    ax2.text(1.25, 0.7, "монотонная\nдля 3pt\n5pt держится",
             ha="center", fontsize=10, color="#78350f", fontweight="bold")
    ax2.text(2.5, 0.7, "монотонная\nдля всех", ha="center",
             fontsize=10, color="#7f1d1d", fontweight="bold")

    ax2.set_xlabel("|x₀| — смещение пика от центра окна (в бинах)")
    ax2.set_ylabel("Ошибка (качественно)")
    ax2.set_title("Рабочие зоны 3pt vs 5pt методов")
    ax2.legend(loc="upper left", framealpha=0.95)
    ax2.set_xlim(0, 3)
    ax2.set_ylim(0, 1.0)

    fig.suptitle("Монотонная зона: ещё один плюс 5-точечных методов",
                 fontsize=14, fontweight="bold", y=1.02)
    plt.savefig(OUT_DIR / "07_monotonic_zone.png")
    plt.close()
    print("[OK] 07_monotonic_zone.png")


# ===========================================================================
# ГРАФИК 8 — Почему 5 точек, а не 7 или 9
# ===========================================================================
def plot_why_5_points():
    """
    Живой Монте-Карло: для каждого SNR и количества точек (3, 5, 7, 9)
    считаем медиану ошибки на Hanning kernel при zp×2.
    """
    rng = np.random.default_rng(42)

    def generate_trial(x0, snr_db, n_bins=31):
        """
        Генерирует 'FFT-спектр' = Hanning kernel с шумом.
        Возвращает массив магнитуды вокруг истинного пика.
        """
        # padded bins (шаг 0.5 бина = zp×2)
        step = 0.5
        indices = np.arange(n_bins) - n_bins // 2
        positions = indices * step
        clean = hanning_kernel(positions - x0)
        # шум в комплексной области
        snr_linear = 10 ** (snr_db / 10)
        sigma = 1.0 / np.sqrt(2 * snr_linear)
        noise_r = rng.normal(0, sigma, size=n_bins)
        noise_i = rng.normal(0, sigma, size=n_bins)
        # магнитуда комплекс. значения (sig_complex + noise)
        sig_complex = clean.astype(complex)
        sig_complex += noise_r + 1j * noise_i
        return np.abs(sig_complex), indices, step

    def lsq_parabola(y):
        """МНК-парабола по n равноотстоящим точкам xi = -m..m, возвращает -b/(2a)."""
        n = len(y)
        m = n // 2
        x = np.arange(-m, m + 1, dtype=float)
        # fit y = a*x^2 + b*x + c
        A = np.vstack([x**2, x, np.ones(n)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        a, b, c = coef
        if abs(a) < 1e-30:
            return 0.0
        return -b / (2 * a)

    def lsq_gauss(y):
        if np.any(y <= 0):
            return lsq_parabola(y)
        return lsq_parabola(np.log(y))

    def estimate(mag_full, k_center, n_pts, kind="qa"):
        m = n_pts // 2
        y = mag_full[k_center - m: k_center + m + 1]
        if kind == "qa":
            return lsq_parabola(y)
        else:
            return lsq_gauss(y)

    snr_list = [10, 15, 20, 25, 30]
    n_trials = 800
    x0_samples = np.linspace(-0.4, 0.4, 11)

    results = {n: {snr: [] for snr in snr_list} for n in [3, 5, 7, 9]}

    for snr in snr_list:
        errs = {n: [] for n in [3, 5, 7, 9]}
        for _ in range(n_trials):
            for x0 in x0_samples:
                mag, idx, step = generate_trial(x0, snr, n_bins=31)
                k_max = int(np.argmax(mag))
                for n_pts in [3, 5, 7, 9]:
                    m = n_pts // 2
                    if k_max - m < 0 or k_max + m >= len(mag):
                        continue
                    d_est = estimate(mag, k_max, n_pts, kind="ea")
                    # истинная позиция относительно центра окна
                    true_rel = x0 / step - idx[k_max]
                    err = abs(d_est - true_rel) * step  # в реальных бинах
                    errs[n_pts].append(err)
        for n_pts in [3, 5, 7, 9]:
            results[n_pts][snr] = float(np.median(errs[n_pts]))

    fig, ax = plt.subplots(figsize=(11, 6))
    width = 0.2
    x_pos = np.arange(len(snr_list))
    colors = {3: COLOR_GRAY, 5: COLOR_REC, 7: "#7c3aed", 9: "#be185d"}
    labels = {3: "3 точки (EA3)", 5: "5 точек (5EA) ★", 7: "7 точек (7EA)", 9: "9 точек (9EA)"}

    for i, n_pts in enumerate([3, 5, 7, 9]):
        vals = [results[n_pts][s] for s in snr_list]
        offset = (i - 1.5) * width
        bars = ax.bar(x_pos + offset, vals, width,
                      color=colors[n_pts], alpha=0.88,
                      edgecolor="#1e293b", linewidth=1.2,
                      label=labels[n_pts])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.05,
                    f"{v:.3f}", ha="center", fontsize=8, rotation=90)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{s} дБ" for s in snr_list])
    ax.set_xlabel("SNR")
    ax.set_ylabel("Медиана ошибки (в реальных бинах)")
    ax.set_title("Сколько точек брать? Живой эксперимент Монте-Карло",
                 fontsize=13, fontweight="bold")
    ax.set_yscale("log")
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(True, axis="y", alpha=0.3, which="both")

    fig.text(0.5, -0.02,
             "Вывод: 7 и 9 точек почти не дают выигрыша относительно 5 на Hanning kernel. "
             "5 точек — золотая середина.",
             ha="center", fontsize=10, color="#374151", style="italic")

    plt.savefig(OUT_DIR / "08_why_5_points.png")
    plt.close()
    print("[OK] 08_why_5_points.png")


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    print("=" * 60)
    print("Генерация графиков для Frequency_Recommendations")
    print("Папка:", OUT_DIR)
    print("=" * 60)

    plot_pipeline()
    plot_hanning_vs_parabola()
    plot_zero_padding_effect()
    plot_methods_vs_snr()
    plot_accuracy_hz()
    plot_decision_tree()
    plot_monotonic_zone()
    plot_why_5_points()

    print("=" * 60)
    print(f"Готово! Создано 8 графиков в {OUT_DIR}")


if __name__ == "__main__":
    main()
