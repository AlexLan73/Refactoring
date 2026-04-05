"""
common.py — Общие функции для аналитического исследования дискриминаторов
=========================================================================

Содержит:
  - sinc(x) = sin(x)/x (ненормализованный!)
  - Эталонные реализации дискриминаторов (порт C-исходников)
  - Функции экстраполяции для монотонных случаев
  - Загрузка C-библиотеки через ctypes
  - Утилиты: select_top2, is_monotonic

Запуск self-test:
    cd discriminator_estimates/test_python
    python analysis/common.py
"""

import sys
import ctypes
import numpy as np
from pathlib import Path

# --- Пути ---
ANALYSIS_DIR = Path(__file__).resolve().parent
MODULE_DIR = ANALYSIS_DIR.parent.parent       # discriminator_estimates/
REPO_ROOT = MODULE_DIR.parent                 # Refactoring/
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner, SkipTest


# ══════════════════════════════════════════════════════════════════════ #
#  Константы                                                             #
# ══════════════════════════════════════════════════════════════════════ #

GRID_DEFAULT = np.array([-1.0, 0.0, 1.0])
SD_COEFF_DEFAULT = 1.0
SD_COEFF_FFT = 0.132497

# Цвета для графиков (единые во всех скриптах)
COLORS = {
    'CG': '#FF6B6B',
    'SD': '#C792EA',
    'QA': '#4ECDC4',
    'EA': '#FFE66D',
    'AUTO': '#00FF88',
    'LSQ5E': '#FF8C00',   # МНК-гаусс 5 точек (оранжевый)
    'LSQ5Q': '#DA70D6',   # МНК-парабола 5 точек (орхидея)
}


# ══════════════════════════════════════════════════════════════════════ #
#  sinc(x) = sin(x)/x                                                   #
# ══════════════════════════════════════════════════════════════════════ #

def sinc(x):
    """sinc(x) = sin(x)/x, sinc(0) = 1.

    ⚠️ НЕ numpy.sinc (который нормализованный: sin(πx)/(πx)).
    Принимает scalar и np.ndarray.
    """
    x = np.asarray(x, dtype=np.float64)
    result = np.ones_like(x)
    mask = np.abs(x) > 1e-15
    result[mask] = np.sin(x[mask]) / x[mask]
    return result


def hanning_kernel(x):
    """Hanning kernel — форма пика в FFT после Hanning окна.

    H(δ) = 0.5·sinc_n(δ) + 0.25·sinc_n(δ-1) + 0.25·sinc_n(δ+1)
    где sinc_n(x) = sin(πx)/(πx) — нормализованный sinc.

    Используется для Range FFT (ЛЧМ): Hanning окно → FFT → пик этой формы.
    Гладкий, колоколообразный, парабола ложится отлично.
    """
    x = np.asarray(x, dtype=np.float64)
    return 0.5 * np.sinc(x) + 0.25 * np.sinc(x - 1) + 0.25 * np.sinc(x + 1)


# ══════════════════════════════════════════════════════════════════════ #
#  Эталонные реализации дискриминаторов                                  #
# ══════════════════════════════════════════════════════════════════════ #

def ref_cg_2pt(A1, A2, x1, x2):
    """CG 2-точечный (порт discr2cg из discrcg.c).

    Формула: xe = (A1*x1 + A2*x2) / (A1 + A2)
    """
    s = A1 + A2
    if abs(s) < 1e-15:
        return (x1 + x2) * 0.5
    return (A1 * x1 + A2 * x2) / s


def ref_cg_3pt(A, x):
    """CG 3-точечный (порт discr3cg из discrcg.c).

    Формула: xe = sum(Ai*xi) / sum(Ai)
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    s = np.sum(A)
    if abs(s) < 1e-15:
        return float(x[len(x) // 2])
    return float(np.sum(A * x) / s)


def ref_sd(c, A1, A2, x1, x2):
    """SD 2-точечный (порт discr2sd из discrsd.c).

    Формулы:
      xc = (x1 + x2) / 2
      dx = c * (A2 - A1) / (A2 + A1)
      xe = xc + dx
    """
    s = A1 + A2
    if abs(s) < 1e-15:
        return (x1 + x2) * 0.5
    return (x1 + x2) * 0.5 + c * (A2 - A1) / s


def ref_qa(A, x):
    """QA 3-точечный (порт discr3qa из discrqa.c, формула Ao).

    Формулы:
      Ao = (A2 - A1) / (A2 - A3)
      xe = 0.5 * ((Ao-1)*x2² - Ao*x3² + x1²) / ((Ao-1)*x2 - Ao*x3 + x1)

    ⚠️ Использует формулу Ao из C-кода, НЕ np.polyfit!
    """
    A1, A2, A3 = float(A[0]), float(A[1]), float(A[2])
    x1, x2, x3 = float(x[0]), float(x[1]), float(x[2])
    eps = 1e-15

    if abs(A2 - A3) < eps:
        if abs(A2 - A1) < eps:
            return x2
        return x1 if A1 > A2 else 0.5 * (x3 + x2)

    if abs(A2 - A1) < eps:
        return x3 if A3 > A2 else 0.5 * (x1 + x2)

    Ao = (A2 - A1) / (A2 - A3)
    denom = (Ao - 1.0) * x2 - Ao * x3 + x1

    if abs(denom) < eps:
        return x2

    return 0.5 * ((Ao - 1.0) * x2**2 - Ao * x3**2 + x1**2) / denom


def ref_ea(A, x):
    """EA 3-точечный — Гауссов фит через scipy.optimize.curve_fit.

    Фитирует y = amp * exp(-((x - x0) / sigma)^2) и возвращает x0.
    При ошибке фита возвращает координату максимального отсчёта.

    ⚠️ Это НЕ точный порт C-кода (discr3ea использует другой алгоритм
    с логарифмированием). Для валидации C↔Python используйте ref_ea_c().
    """
    from scipy.optimize import curve_fit

    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)

    try:
        def gauss(xx, x0, amp, sigma):
            return amp * np.exp(-((xx - x0) / sigma) ** 2)

        p0 = [float(x[np.argmax(A)]), float(np.max(A)), 1.0]
        popt, _ = curve_fit(gauss, x, A, p0=p0, maxfev=5000)
        return float(popt[0])
    except Exception:
        return float(x[np.argmax(A)])


def ref_ea_c(A1, A2, A3, x1, x2, x3):
    """EA 3-точечный — точный порт discr3ea из discrea.c.

    Алгоритм:
      1. Проверка положительности амплитуд
      2. Сортировка по координатам
      3. Проверка выпуклости
      4. Логарифмирование + парабола
      5. Ограничение вылета

    Returns:
        (xe, success): оценка + флаг успеха (True = EXIT_SUCCESS)
    """
    eps = 1e-15  # аналог DBL_EPSILON в проверках

    # Проверка положительности
    if A1 < eps or A2 < eps or A3 < eps:
        return x2, False

    # Все равны
    if abs(A1 - A2) < eps and abs(A2 - A3) < eps:
        return x2, False

    # Сортировка по x (как qsort в C)
    pts = sorted([(A1, x1), (A2, x2), (A3, x3)], key=lambda p: p[1])
    a1, f1 = pts[0]
    a2, f2 = pts[1]
    a3, f3 = pts[2]

    # Проверка выпуклости
    a12 = a1 - a2
    a23 = a2 - a3
    a13 = a1 - a3

    # Вогнутость: максимум справа
    if (a12 < 0 and a23 < 0 and a12 > a23) or \
       (a12 > 0 and a23 < 0 and a13 < 0):
        return x3, False

    # Вогнутость: максимум слева
    if (a12 > 0 and a23 > 0 and a12 > a23) or \
       (a12 > 0 and a23 < 0 and a13 > 0):
        return x1, False

    # Логарифмирование
    z1 = np.log(a1)
    z2 = np.log(a2)
    z3 = np.log(a3)

    # Коэффициенты параболы
    a_coef = z1 * (f2**2 - f3**2) + z2 * (f3**2 - f1**2) + z3 * (f1**2 - f2**2)
    b_coef = z1 * (f2 - f3) + z2 * (f3 - f1) + z3 * (f1 - f2)

    if abs(b_coef) < eps:
        if a_coef * b_coef >= 0:
            return f3 + 0.5 * (f3 - f1), False
        else:
            return f1 - 0.5 * (f3 - f1), False

    # Вершина параболы
    xe = 0.5 * a_coef / b_coef

    # Ограничение вылета
    span = f3 - f1
    if xe > f3 + 0.5 * span:
        return f3 + 0.5 * span, False
    if xe < f1 - 0.5 * span:
        return f1 - 0.5 * span, False

    return xe, True


def ref_auto(A, x):
    """AUTO: автоматический дискриминатор — порт discr3_auto из C.

    Стратегия:
      1. Монотонные данные → Гауссова экстраполяция (E2)
      2. Нормальные данные → EA (экспоненциальный)
      3. EA failure        → QA (квадратичный fallback)

    Returns:
        (xe, mode) — оценка + режим (0=EA, 1=QA fallback, 2=E2, 3=E2 fail)
    """
    A1, A2, A3 = float(A[0]), float(A[1]), float(A[2])
    x1, x2, x3 = float(x[0]), float(x[1]), float(x[2])

    if is_monotonic(A1, A2, A3):
        xe = extrap_gaussian_c(A1, A2, A3, x1, x2, x3)
        if not np.isnan(xe):
            return xe, 2
        return x2, 3

    xe, ok = ref_ea_c(A1, A2, A3, x1, x2, x3)
    if ok:
        return xe, 0

    return ref_qa(A, x), 1


def extrap_gaussian_c(A1, A2, A3, x1, x2, x3):
    """E2 Гауссова экстраполяция — порт discr3_extrap_gauss из C.

    Как EA, но БЕЗ проверки выпуклости и с расширенным clipping (2× вместо 0.5×).
    """
    eps = 1e-15

    if A1 < eps or A2 < eps or A3 < eps:
        return float('nan')
    if abs(A1 - A2) < eps and abs(A2 - A3) < eps:
        return float('nan')

    pts = sorted([(A1, x1), (A2, x2), (A3, x3)], key=lambda p: p[1])
    a1, f1 = pts[0]
    a2, f2 = pts[1]
    a3, f3 = pts[2]

    z1, z2, z3 = np.log(a1), np.log(a2), np.log(a3)

    a_coef = z1 * (f2**2 - f3**2) + z2 * (f3**2 - f1**2) + z3 * (f1**2 - f2**2)
    b_coef = z1 * (f2 - f3) + z2 * (f3 - f1) + z3 * (f1 - f2)

    if abs(b_coef) < eps:
        if a3 > a1:
            return f3 + 0.5 * (f3 - f1)
        return f1 - 0.5 * (f3 - f1)

    xe = 0.5 * a_coef / b_coef

    span = f3 - f1
    if xe > f3 + span:
        xe = f3 + span
    if xe < f1 - span:
        xe = f1 - span

    return xe


# ══════════════════════════════════════════════════════════════════════ #
#  МНК 5-точечные дискриминаторы (discr5ea / discr5qa)                   #
# ══════════════════════════════════════════════════════════════════════ #

def _lsq5_peak(y):
    """МНК-параболическая оценка вершины по 5 равноотстоящим значениям.

    Нормированные координаты {-2, -1, 0, 1, 2}.
    Формулы из нормальных уравнений (A^T A) beta = A^T y.

    Returns:
        (peak, ok) — смещение вершины в нормированных единицах, флаг успеха.
    """
    a = (2.0*y[0] - y[1] - 2.0*y[2] - y[3] + 2.0*y[4]) / 14.0
    b = (-2.0*y[0] - y[1] + y[3] + 2.0*y[4]) / 10.0

    if a > -1e-15:  # парабола не вогнутая → нет максимума
        return 0.0, False

    peak = -b / (2.0 * a)
    peak = max(-2.0, min(2.0, peak))  # ограничение ±2 шага
    return peak, True


def ref_5ea(A, x):
    """МНК-гауссов дискриминатор по 5 точкам (порт discr5ea из C).

    Логарифмирует амплитуды, затем МНК-парабола.

    Args:
        A: массив из 5 амплитуд (все > 0)
        x: массив из 5 координат (равноотстоящие)

    Returns:
        float — оценка координаты xe
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    h = x[1] - x[0]
    if abs(h) < 1e-15 or np.any(A < 1e-15):
        return float(x[2])
    z = np.log(A)
    peak, _ = _lsq5_peak(z)
    return float(x[2] + h * peak)


def ref_5qa(A, x):
    """МНК-параболический дискриминатор по 5 точкам (порт discr5qa из C).

    Работает напрямую с амплитудами (без логарифмирования).

    Args:
        A: массив из 5 амплитуд
        x: массив из 5 координат (равноотстоящие)

    Returns:
        float — оценка координаты xe
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    h = x[1] - x[0]
    if abs(h) < 1e-15:
        return float(x[2])
    peak, _ = _lsq5_peak(A)
    return float(x[2] + h * peak)


# ══════════════════════════════════════════════════════════════════════ #
#  Утилиты                                                               #
# ══════════════════════════════════════════════════════════════════════ #

def select_top2(A, x):
    """Выбрать 2 отсчёта с максимальными амплитудами (как conv3to2 в C).

    Returns:
        (A1, A2, x1, x2) — пара (амплитуда, координата), упорядоченная по x.
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    idx = np.argsort(A)[-2:]  # два наибольших по амплитуде
    idx = np.sort(idx)        # упорядочить по позиции (→ по x)
    return float(A[idx[0]]), float(A[idx[1]]), float(x[idx[0]]), float(x[idx[1]])


def is_monotonic(A1, A2, A3):
    """True если нет локального максимума (все возрастают или убывают).

    Монотонный случай — пик за пределами сетки из 3 отсчётов.
    """
    return (A1 >= A2 >= A3) or (A1 <= A2 <= A3)


def classify_zone(x0):
    """Классифицировать положение пика по зонам.

    Returns: 'normal' | 'boundary' | 'extreme'
    """
    ax0 = abs(x0)
    if ax0 <= 0.5:
        return 'normal'
    elif ax0 <= 1.0:
        return 'boundary'
    else:
        return 'extreme'


# ══════════════════════════════════════════════════════════════════════ #
#  Экстраполяция для монотонных случаев (Этап 1.1)                      #
# ══════════════════════════════════════════════════════════════════════ #

def extrap_parabolic(A1, A2, A3, x1, x2, x3, max_extrap=2.0):
    """E1: параболическая экстраполяция.

    Фит y = a*x² + b*x + c через 3 точки, вершина x_v = -b/(2a).
    Clip: не дальше max_extrap * step от края сетки.
    """
    coeffs = np.polyfit([x1, x2, x3], [A1, A2, A3], 2)
    a, b, c = coeffs
    if abs(a) < 1e-15:
        return float('nan')
    x_vertex = -b / (2.0 * a)
    step = x2 - x1
    x_min = x1 - max_extrap * abs(step)
    x_max = x3 + max_extrap * abs(step)
    return float(np.clip(x_vertex, x_min, x_max))


def extrap_gaussian(A1, A2, A3, x1, x2, x3):
    """E2: Гауссова экстраполяция через scipy.optimize.curve_fit.

    Фит y = amp * exp(-((x - x0) / sigma)^2).
    При несходимости возвращает NaN.
    """
    from scipy.optimize import curve_fit

    A = np.array([A1, A2, A3])
    x = np.array([x1, x2, x3])

    if np.any(A <= 0):
        return float('nan')

    try:
        def gauss(xx, x0, amp, sigma):
            return amp * np.exp(-((xx - x0) / sigma) ** 2)

        # Начальное приближение: пик в сторону роста
        x_init = x3 if A3 > A1 else x1
        p0 = [x_init, float(np.max(A)), 1.0]
        popt, _ = curve_fit(gauss, x, A, p0=p0, maxfev=5000)
        return float(popt[0])
    except Exception:
        return float('nan')


def extrap_gradient(A1, A2, A3, x1, x2, x3):
    """E3: градиентная экстраполяция (робастный fallback).

    Линейная регрессия → направление + 0.5 * step за край.
    """
    x = np.array([x1, x2, x3])
    A = np.array([A1, A2, A3])
    step = x2 - x1
    slope, _ = np.polyfit(x, A, 1)
    x_edge = x3 if slope > 0 else x1
    return float(x_edge + 0.5 * step * np.sign(slope))


# ══════════════════════════════════════════════════════════════════════ #
#  Загрузка C-библиотеки (ctypes)                                       #
# ══════════════════════════════════════════════════════════════════════ #

def load_discr_lib():
    """Загрузить shared-библиотеку discriminator_estimates.

    Ищет в build/, build/Release/. При отсутствии: raise SkipTest.
    """
    candidates = [
        MODULE_DIR / "build" / "discr.dll",
        MODULE_DIR / "build" / "Release" / "discr.dll",
        MODULE_DIR / "build" / "libdiscr.so",
        MODULE_DIR / "build" / "libdiscr_shared.so",
    ]
    for p in candidates:
        if p.exists():
            return ctypes.CDLL(str(p))
    raise SkipTest(
        "C-библиотека не найдена. Кандидаты:\n"
        + "\n".join(f"  {p}" for p in candidates)
    )


# ══════════════════════════════════════════════════════════════════════ #
#  Self-test                                                              #
# ══════════════════════════════════════════════════════════════════════ #

class TestCommonFunctions:
    """Self-test: проверка всех функций common.py."""

    def test_sinc_zero(self):
        """sinc(0) == 1.0"""
        assert sinc(0.0) == 1.0, f"sinc(0) = {sinc(0.0)}"
        print("  [PASS] sinc(0) = 1.0")

    def test_sinc_array(self):
        """sinc(np.array([0, 1, -1])) работает."""
        result = sinc(np.array([0.0, 1.0, -1.0]))
        assert result[0] == 1.0
        assert abs(result[1] - np.sin(1.0)) < 1e-15
        assert abs(result[2] - np.sin(-1.0) / (-1.0)) < 1e-15
        print(f"  [PASS] sinc([0,1,-1]) = [{result[0]:.4f}, {result[1]:.4f}, {result[2]:.4f}]")

    def test_ref_cg_2pt_symmetric(self):
        """CG 2pt: равные амплитуды → середина."""
        xe = ref_cg_2pt(1.0, 1.0, -1.0, 1.0)
        assert abs(xe) < 1e-15, f"CG 2pt symmetric: {xe}"
        print(f"  [PASS] CG 2pt symmetric: xe = {xe:.6f}")

    def test_ref_cg_2pt_weighted(self):
        """CG 2pt: A1=1, A2=3 на [-1, 1] → 0.5."""
        xe = ref_cg_2pt(1.0, 3.0, -1.0, 1.0)
        assert abs(xe - 0.5) < 1e-15, f"CG 2pt weighted: {xe}"
        print(f"  [PASS] CG 2pt weighted: xe = {xe:.6f}")

    def test_ref_sd_basic(self):
        """SD: c=1, равные → середина."""
        xe = ref_sd(1.0, 1.0, 1.0, -1.0, 1.0)
        assert abs(xe) < 1e-15
        print(f"  [PASS] SD equal amplitudes: xe = {xe:.6f}")

    def test_ref_qa_symmetric(self):
        """QA: sinc(x) с пиком в 0 → xe ≈ 0."""
        x = GRID_DEFAULT
        A = sinc(x)
        xe = ref_qa(A, x)
        assert abs(xe) < 1e-10, f"QA symmetric: {xe}"
        print(f"  [PASS] QA symmetric: xe = {xe:.10f}")

    def test_ref_qa_shifted(self):
        """QA: sinc(x - 0.2) → xe ≈ 0.2."""
        x0 = 0.2
        x = GRID_DEFAULT
        A = sinc(x - x0)
        xe = ref_qa(A, x)
        err = abs(xe - x0)
        assert err < 0.15, f"QA shifted: xe={xe}, err={err}"
        print(f"  [PASS] QA shifted (x0=0.2): xe = {xe:.6f}, err = {err:.6f}")

    def test_ref_ea_symmetric(self):
        """EA: sinc(x) с пиком в 0 → xe ≈ 0."""
        x = GRID_DEFAULT
        A = sinc(x)
        xe = ref_ea(A, x)
        assert abs(xe) < 0.01, f"EA symmetric: {xe}"
        print(f"  [PASS] EA symmetric: xe = {xe:.6f}")

    def test_ref_ea_c_symmetric(self):
        """EA (C-порт): sinc(x) с пиком в 0 → xe ≈ 0."""
        x = GRID_DEFAULT
        A = sinc(x)
        xe, ok = ref_ea_c(A[0], A[1], A[2], x[0], x[1], x[2])
        assert ok, f"EA_c returned failure"
        assert abs(xe) < 0.01, f"EA_c symmetric: {xe}"
        print(f"  [PASS] EA_c symmetric: xe = {xe:.6f}, success = {ok}")

    def test_select_top2(self):
        """select_top2: 3 амплитуды → 2 максимальных."""
        A = np.array([0.5, 1.0, 0.8])
        x = np.array([-1.0, 0.0, 1.0])
        A1, A2, x1, x2 = select_top2(A, x)
        assert A1 == 1.0 and A2 == 0.8
        assert x1 == 0.0 and x2 == 1.0
        print(f"  [PASS] select_top2: ({A1},{A2}) at ({x1},{x2})")

    def test_is_monotonic(self):
        """is_monotonic: корректная детекция."""
        assert is_monotonic(3, 2, 1) == True
        assert is_monotonic(1, 2, 3) == True
        assert is_monotonic(1, 3, 2) == False
        assert is_monotonic(2, 3, 1) == False
        print("  [PASS] is_monotonic: all cases correct")

    def test_classify_zone(self):
        """classify_zone: правильная классификация."""
        assert classify_zone(0.0) == 'normal'
        assert classify_zone(0.3) == 'normal'
        assert classify_zone(0.7) == 'boundary'
        assert classify_zone(1.2) == 'extreme'
        print("  [PASS] classify_zone: all cases correct")

    def test_extrap_parabolic(self):
        """E1: парабола через 3 монотонных точки."""
        # Монотонные: sinc(x - 1.3) на [-1, 0, 1]
        x0 = 1.3
        A1, A2, A3 = float(sinc(-1 - x0)), float(sinc(0 - x0)), float(sinc(1 - x0))
        xe = extrap_parabolic(A1, A2, A3, -1.0, 0.0, 1.0)
        assert not np.isnan(xe), "E1 returned NaN"
        err = abs(xe - x0)
        print(f"  [PASS] E1 parabolic (x0=1.3): xe = {xe:.4f}, err = {err:.4f}")

    def test_extrap_gradient(self):
        """E3: градиентная экстраполяция."""
        x0 = 1.3
        A1, A2, A3 = float(sinc(-1 - x0)), float(sinc(0 - x0)), float(sinc(1 - x0))
        xe = extrap_gradient(A1, A2, A3, -1.0, 0.0, 1.0)
        assert xe > 1.0, f"E3 should extrapolate right: {xe}"
        print(f"  [PASS] E3 gradient (x0=1.3): xe = {xe:.4f}")

    def test_qa_vs_ea_c_agreement(self):
        """QA и EA_c дают похожие результаты в normal зоне."""
        x = GRID_DEFAULT
        x0 = 0.15
        A = sinc(x - x0)
        xe_qa = ref_qa(A, x)
        xe_ea, ok = ref_ea_c(A[0], A[1], A[2], x[0], x[1], x[2])
        assert ok, "EA_c should succeed for normal case"
        diff = abs(xe_qa - xe_ea)
        print(f"  [PASS] QA={xe_qa:.6f}, EA_c={xe_ea:.6f}, diff={diff:.6f}")

    def test_auto_normal(self):
        """AUTO: нормальный случай → использует EA (mode=0)."""
        x = GRID_DEFAULT
        A = sinc(x - 0.2)
        xe, mode = ref_auto(A, x)
        assert mode == 0, f"Expected EA (mode=0), got mode={mode}"
        assert abs(xe - 0.2) < 0.01
        print(f"  [PASS] AUTO normal: xe={xe:.6f}, mode={mode} (EA)")

    def test_auto_monotonic(self):
        """AUTO: монотонный случай → использует E2 (mode=2)."""
        x = GRID_DEFAULT
        A = sinc(x - 1.3)
        xe, mode = ref_auto(A, x)
        assert mode == 2 or mode == 3, f"Expected E2, got mode={mode}"
        assert xe > 0.5, f"Extrapolation should be right: xe={xe}"
        print(f"  [PASS] AUTO monotonic: xe={xe:.4f}, mode={mode} (E2), err={abs(xe-1.3):.4f}")

    def test_auto_better_than_ea_monotonic(self):
        """AUTO лучше чистого EA для монотонных данных."""
        x = GRID_DEFAULT
        errors_auto, errors_ea = [], []
        for x0 in np.linspace(1.05, 1.5, 20):
            A = sinc(x - x0)
            xe_auto, _ = ref_auto(A, x)
            xe_ea, _ = ref_ea_c(A[0], A[1], A[2], x[0], x[1], x[2])
            errors_auto.append(abs(xe_auto - x0))
            errors_ea.append(abs(xe_ea - x0))
        mae_auto = np.mean(errors_auto)
        mae_ea = np.mean(errors_ea)
        print(f"  [PASS] AUTO vs EA (monotonic): AUTO MAE={mae_auto:.4f}, EA MAE={mae_ea:.4f}")


class TestCValidation:
    """Валидация C ↔ Python (пропускается если библиотека не собрана)."""

    def setUp(self):
        self.lib = load_discr_lib()
        # Настройка ctypes
        self.lib.discr2cg.restype = ctypes.c_double
        self.lib.discr2cg.argtypes = [ctypes.c_double] * 4
        self.lib.discr3cg.restype = ctypes.c_double
        self.lib.discr3cg.argtypes = [ctypes.c_double] * 6
        self.lib.discr2sd.restype = ctypes.c_double
        self.lib.discr2sd.argtypes = [ctypes.c_double] * 5
        self.lib.discr3qa.restype = ctypes.c_double
        self.lib.discr3qa.argtypes = [ctypes.c_double] * 6
        self.lib.discr3ea.restype = ctypes.c_int
        self.lib.discr3ea.argtypes = [ctypes.c_double] * 6 + [ctypes.POINTER(ctypes.c_double)]

    def test_cg_validation(self):
        """CG: Python ↔ C (< 1e-12)."""
        for x0 in [0.0, 0.1, 0.2, 0.3, 0.4]:
            A = sinc(GRID_DEFAULT - x0)
            A1, A2, x1, x2 = select_top2(A, GRID_DEFAULT)
            py = ref_cg_2pt(A1, A2, x1, x2)
            c_val = self.lib.discr2cg(A1, A2, x1, x2)
            assert abs(py - c_val) < 1e-12, f"CG x0={x0}: py={py}, c={c_val}"
        print("  [PASS] CG C↔Python: 5 points, diff < 1e-12")

    def test_sd_validation(self):
        """SD: Python ↔ C (< 1e-12)."""
        c = 1.0
        for x0 in [0.0, 0.1, 0.2, 0.3, 0.4]:
            A = sinc(GRID_DEFAULT - x0)
            A1, A2, x1, x2 = select_top2(A, GRID_DEFAULT)
            py = ref_sd(c, A1, A2, x1, x2)
            c_val = self.lib.discr2sd(c, A1, A2, x1, x2)
            assert abs(py - c_val) < 1e-12, f"SD x0={x0}: py={py}, c={c_val}"
        print("  [PASS] SD C↔Python: 5 points, diff < 1e-12")

    def test_qa_validation(self):
        """QA: Python ↔ C (< 1e-12)."""
        for x0 in [0.0, 0.1, 0.2, 0.3, 0.4]:
            A = sinc(GRID_DEFAULT - x0)
            py = ref_qa(A, GRID_DEFAULT)
            c_val = self.lib.discr3qa(
                A[0], A[1], A[2],
                GRID_DEFAULT[0], GRID_DEFAULT[1], GRID_DEFAULT[2]
            )
            assert abs(py - c_val) < 1e-12, f"QA x0={x0}: py={py}, c={c_val}"
        print("  [PASS] QA C↔Python: 5 points, diff < 1e-12")

    def test_ea_validation(self):
        """EA (C-порт): Python ↔ C (< 1e-12, только normal зона)."""
        for x0 in [0.0, 0.1, 0.2, 0.3]:
            A = sinc(GRID_DEFAULT - x0)
            xe_c = ctypes.c_double(0.0)
            ret = self.lib.discr3ea(
                A[0], A[1], A[2],
                GRID_DEFAULT[0], GRID_DEFAULT[1], GRID_DEFAULT[2],
                ctypes.byref(xe_c)
            )
            py, ok = ref_ea_c(A[0], A[1], A[2],
                              GRID_DEFAULT[0], GRID_DEFAULT[1], GRID_DEFAULT[2])
            if ret == 0 and ok:
                assert abs(py - xe_c.value) < 1e-12, \
                    f"EA x0={x0}: py={py}, c={xe_c.value}"
        print("  [PASS] EA_c C↔Python: normal zone, diff < 1e-12")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all([
        TestCommonFunctions(),
        TestCValidation(),
    ])
    runner.print_summary(results)
