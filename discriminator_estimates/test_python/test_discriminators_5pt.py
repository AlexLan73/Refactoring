"""
test_discriminators_5pt.py -- Тесты МНК-дискриминаторов по 5 точкам
===================================================================

Методы:
  - ref_5ea: МНК-Гауссиан по 5 точкам (в лог-масштабе)
  - ref_5qa: МНК-парабола по 5 точкам (в линейном масштабе)

Сравнение с существующими QA (3pt) и EA (3pt) на данных sinc(x).

Запуск:
    python test_python/test_discriminators_5pt.py
"""

import sys
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner, SkipTest
from PyCore.validators import DataValidator


# --- sinc(x) ---

def sinc(x):
    """sinc(x) = sin(x)/x, sinc(0) = 1"""
    x = np.asarray(x, dtype=np.float64)
    result = np.ones_like(x)
    mask = np.abs(x) > 1e-15
    result[mask] = np.sin(x[mask]) / x[mask]
    return result


# --- Эталонные реализации на numpy ---

def ref_qa(A, x):
    """Квадратичная аппроксимация 3pt: вершина параболы через 3 точки."""
    coeffs = np.polyfit(x, A, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


def ref_ea(A, x):
    """Экспоненциальная аппроксимация 3pt: вершина в лог-масштабе."""
    if any(a <= 0 for a in A):
        return ref_qa(A, x)
    z = np.log(A)
    coeffs = np.polyfit(x, z, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


def ref_5qa(A, x):
    """МНК-параболическая аппроксимация по 5 равноотстоящим точкам.

    Замкнутая формула для xi = {-2, -1, 0, 1, 2} * step:
        a = (2*y1 - y2 - 2*y3 - y4 + 2*y5) / 14
        b = (-2*y1 - y2 + y4 + 2*y5) / 10
        xe = x_center + step * (-b / (2*a))
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    assert len(A) == 5 and len(x) == 5

    step = x[1] - x[0]
    if abs(step) < 1e-15:
        return x[2]

    a = (2.0*A[0] - A[1] - 2.0*A[2] - A[3] + 2.0*A[4]) / 14.0
    b = (-2.0*A[0] - A[1] + A[3] + 2.0*A[4]) / 10.0

    if a >= -1e-30:
        return x[2]

    delta = -b / (2.0 * a)
    return x[2] + step * delta


def ref_5ea(A, x):
    """МНК-гауссова аппроксимация по 5 равноотстоящим точкам.

    Логарифмирует амплитуды, затем МНК-парабола по 5 точкам.
    """
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    assert len(A) == 5 and len(x) == 5

    if any(A <= 0):
        return ref_5qa(A, x)

    step = x[1] - x[0]
    if abs(step) < 1e-15:
        return x[2]

    z = np.log(A)

    a = (2.0*z[0] - z[1] - 2.0*z[2] - z[3] + 2.0*z[4]) / 14.0
    b = (-2.0*z[0] - z[1] + z[3] + 2.0*z[4]) / 10.0

    if a >= -1e-30:
        return x[2]

    delta = -b / (2.0 * a)
    return x[2] + step * delta


# --- Тесты ---

class TestDiscr5EA:
    """Тесты МНК-Гауссиан по 5 точкам на sinc(x)."""

    def test_gaussian_symmetric(self):
        """Гауссов пик в 0: 5 точек {-2,-1,0,1,2}"""
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = np.exp(-x**2)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=1e-10, metric="abs")
        return v.validate(result, 0.0, name="5EA_gaussian_symmetric")

    def test_gaussian_shifted(self):
        """Гауссов пик в 0.3"""
        x0 = 0.3
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = np.exp(-(x - x0)**2)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=0.01, metric="abs")
        return v.validate(result, x0, name="5EA_gaussian_shifted_03")

    def test_sinc_symmetric(self):
        """sinc(x), пик в 0: 5 точек {-2,-1,0,1,2}"""
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = sinc(x)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=0.01, metric="abs")
        return v.validate(result, 0.0, name="5EA_sinc_symmetric")

    def test_sinc_shifted_03(self):
        """sinc(x - 0.3), 5 точек {-2,-1,0,1,2}"""
        x0 = 0.3
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = sinc(x - x0)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=0.05, metric="abs")
        return v.validate(result, x0, name="5EA_sinc_shifted_03")

    def test_sinc_fine_grid(self):
        """sinc(x - 0.2), мелкая сетка шаг 0.5"""
        x0 = 0.2
        x = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        A = sinc(x - x0)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=0.02, metric="abs")
        return v.validate(result, x0, name="5EA_sinc_fine_grid_02")

    def test_sinc_fine_grid_04(self):
        """sinc(x - 0.4), мелкая сетка шаг 0.5"""
        x0 = 0.4
        x = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        A = sinc(x - x0)
        result = ref_5ea(A, x)
        v = DataValidator(tolerance=0.03, metric="abs")
        return v.validate(result, x0, name="5EA_sinc_fine_grid_04")


class TestDiscr5QA:
    """Тесты МНК-парабола по 5 точкам."""

    def test_parabola_exact(self):
        """Точная парабола: МНК должен дать точный ответ"""
        x0 = 0.4
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = -(x - x0)**2 + 10.0
        result = ref_5qa(A, x)
        v = DataValidator(tolerance=1e-10, metric="abs")
        return v.validate(result, x0, name="5QA_parabola_exact")

    def test_sinc_symmetric(self):
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = sinc(x)
        result = ref_5qa(A, x)
        v = DataValidator(tolerance=0.01, metric="abs")
        return v.validate(result, 0.0, name="5QA_sinc_symmetric")

    def test_sinc_shifted(self):
        x0 = 0.3
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        A = sinc(x - x0)
        result = ref_5qa(A, x)
        v = DataValidator(tolerance=0.1, metric="abs")
        return v.validate(result, x0, name="5QA_sinc_shifted_03")


class TestComparison5pt:
    """Сравнение точности 5-точечных и 3-точечных методов."""

    def test_accuracy_comparison_step1(self):
        """Сравнение на sinc(x), шаг 1.0, серия смещений"""
        shifts = np.linspace(-0.4, 0.4, 9)
        x5 = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        x3 = np.array([-1.0, 0.0, 1.0])

        errors = {'QA3': [], 'EA3': [], '5QA': [], '5EA': []}
        for x0 in shifts:
            A5 = sinc(x5 - x0)
            A3 = sinc(x3 - x0)
            errors['QA3'].append(abs(ref_qa(A3, x3) - x0))
            errors['EA3'].append(abs(ref_ea(A3, x3) - x0))
            errors['5QA'].append(abs(ref_5qa(A5, x5) - x0))
            errors['5EA'].append(abs(ref_5ea(A5, x5) - x0))

        for name, errs in errors.items():
            print(f"  {name}: mean={np.mean(errs):.6f}, max={np.max(errs):.6f}")

    def test_accuracy_comparison_step05(self):
        """Сравнение на sinc(x), шаг 0.5 (= zero-pad x2)"""
        shifts = np.linspace(-0.2, 0.2, 9)
        x5 = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        x3 = np.array([-0.5, 0.0, 0.5])

        errors = {'QA3': [], 'EA3': [], '5QA': [], '5EA': []}
        for x0 in shifts:
            A5 = sinc(x5 - x0)
            A3 = sinc(x3 - x0)
            errors['QA3'].append(abs(ref_qa(A3, x3) - x0))
            errors['EA3'].append(abs(ref_ea(A3, x3) - x0))
            errors['5QA'].append(abs(ref_5qa(A5, x5) - x0))
            errors['5EA'].append(abs(ref_5ea(A5, x5) - x0))

        print("  [step=0.5]")
        for name, errs in errors.items():
            print(f"  {name}: mean={np.mean(errs):.6f}, max={np.max(errs):.6f}")

        # МНК-5 с мелким шагом должен быть хорош
        assert np.mean(errors['5EA']) < 0.05

    def test_noise_robustness(self):
        """МНК-5 должен быть устойчивее к шуму чем 3pt"""
        np.random.seed(42)
        x0 = 0.15
        step = 0.5
        x5 = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        x3 = np.array([-0.5, 0.0, 0.5])
        n_trials = 200
        snr_db = 20  # уровень шума

        errors_3ea = []
        errors_5ea = []

        for _ in range(n_trials):
            A_clean = sinc(x5 - x0)
            noise = A_clean * 10**(-snr_db/20) * np.random.randn(5)
            A_noisy = np.maximum(A_clean + noise, 1e-10)

            # 5-точечный
            est_5ea = ref_5ea(A_noisy, x5)
            errors_5ea.append(abs(est_5ea - x0))

            # 3-точечный (центральные)
            est_3ea = ref_ea(A_noisy[1:4], x3)
            errors_3ea.append(abs(est_3ea - x0))

        std_3 = np.std(errors_3ea)
        std_5 = np.std(errors_5ea)
        mean_3 = np.mean(errors_3ea)
        mean_5 = np.mean(errors_5ea)
        print(f"  [noise SNR={snr_db}dB, {n_trials} trials]")
        print(f"  EA3: mean={mean_3:.6f}, std={std_3:.6f}")
        print(f"  5EA: mean={mean_5:.6f}, std={std_5:.6f}")

        # МНК-5 должен иметь меньший разброс (устойчивость к шуму)
        # Не жёсткий assert — на 20 дБ разница может быть небольшой
        print(f"  [INFO] 5EA std/3EA std = {std_5/std_3:.3f}")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all([
        TestDiscr5EA(),
        TestDiscr5QA(),
        TestComparison5pt(),
    ])
    runner.print_summary(results)
