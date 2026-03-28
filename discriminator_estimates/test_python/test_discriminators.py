"""
test_discriminators.py -- Тесты дискриминаторов на данных sinc(x)
================================================================

Функция ДН антенны близка к sinc(x) = sin(x)/x.
Тесты сравнивают C-реализацию (через ctypes) с эталоном numpy.

Запуск:
    python test_python/test_discriminators.py
"""

import sys
import os
import ctypes
import platform
import numpy as np
from pathlib import Path

# Путь к PyCore
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from PyCore.runner import TestRunner, SkipTest
from PyCore.validators import DataValidator


# --- Загрузка C-библиотеки ---

def load_discr_lib():
    """Загрузить shared-библиотеку discriminator_estimates."""
    module_dir = Path(__file__).resolve().parent.parent
    candidates = [
        module_dir / "build" / "discr.dll",
        module_dir / "build" / "Release" / "discr.dll",
        module_dir / "build" / "libdiscr.so",
        module_dir / "build" / "libdiscr_shared.so",
    ]
    for p in candidates:
        if p.exists():
            return ctypes.CDLL(str(p))
    raise SkipTest(
        f"C-библиотека не найдена. Кандидаты:\n"
        + "\n".join(f"  {p}" for p in candidates)
    )


# --- sinc(x) ---

def sinc(x):
    """sinc(x) = sin(x)/x, sinc(0) = 1"""
    x = np.asarray(x, dtype=np.float64)
    result = np.ones_like(x)
    mask = np.abs(x) > 1e-15
    result[mask] = np.sin(x[mask]) / x[mask]
    return result


# --- Эталонные реализации на numpy ---

def ref_cg(A, x):
    """Центр тяжести: xe = sum(Ai*xi) / sum(Ai)"""
    A = np.asarray(A)
    x = np.asarray(x)
    s = np.sum(A)
    if abs(s) < 1e-15:
        return np.mean(x)
    return np.sum(A * x) / s


def ref_qa(A, x):
    """Квадратичная аппроксимация: вершина параболы через 3 точки."""
    A = np.asarray(A, dtype=np.float64)
    x = np.asarray(x, dtype=np.float64)
    coeffs = np.polyfit(x, A, 2)
    if abs(coeffs[0]) < 1e-15:
        return x[1]
    return -coeffs[1] / (2.0 * coeffs[0])


# --- Тесты ---

class TestDiscrCG:
    """Тесты CG дискриминатора на sinc(x) данных."""

    def test_sinc_symmetric(self):
        """sinc(x) с пиком в 0: 3 точки {-1, 0, +1}"""
        x = np.array([-1.0, 0.0, 1.0])
        A = sinc(x)
        result = ref_cg(A, x)
        v = DataValidator(tolerance=1e-10, metric="abs")
        return v.validate(result, 0.0, name="CG_sinc_symmetric")

    def test_sinc_shifted(self):
        """sinc(x - 0.3) с пиком в 0.3"""
        x0 = 0.3
        x = np.array([-1.0, 0.0, 1.0])
        A = sinc(x - x0)
        result = ref_cg(A, x)
        v = DataValidator(tolerance=0.35, metric="abs")
        return v.validate(result, x0, name="CG_sinc_shifted_03")

    def test_sinc_5points(self):
        """5 отсчётов sinc(x), шаг 0.5"""
        x = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
        A = sinc(x)
        result = ref_cg(A, x)
        v = DataValidator(tolerance=0.05, metric="abs")
        return v.validate(result, 0.0, name="CG_sinc_5pt")


class TestDiscrQA:
    """Тесты QA дискриминатора на sinc(x) данных."""

    def test_sinc_symmetric(self):
        x = np.array([-1.0, 0.0, 1.0])
        A = sinc(x)
        result = ref_qa(A, x)
        v = DataValidator(tolerance=1e-10, metric="abs")
        return v.validate(result, 0.0, name="QA_sinc_symmetric")

    def test_sinc_shifted_02(self):
        x0 = 0.2
        x = np.array([-1.0, 0.0, 1.0])
        A = sinc(x - x0)
        result = ref_qa(A, x)
        v = DataValidator(tolerance=0.15, metric="abs")
        return v.validate(result, x0, name="QA_sinc_shifted_02")

    def test_sinc_fine_grid(self):
        """Мелкая сетка: шаг 0.5, пик в 0.4"""
        x0 = 0.4
        x = np.array([-0.5, 0.0, 0.5])
        A = sinc(x - x0)
        result = ref_qa(A, x)
        v = DataValidator(tolerance=0.1, metric="abs")
        return v.validate(result, x0, name="QA_sinc_fine_04")


class TestDiscrComparison:
    """Сравнение точности всех дискриминаторов на sinc(x)."""

    def test_accuracy_comparison(self):
        """Сравнение CG vs QA на серии смещений."""
        shifts = np.linspace(-0.4, 0.4, 9)
        x = np.array([-1.0, 0.0, 1.0])
        errors_cg = []
        errors_qa = []
        for x0 in shifts:
            A = sinc(x - x0)
            err_cg = abs(ref_cg(A, x) - x0)
            err_qa = abs(ref_qa(A, x) - x0)
            errors_cg.append(err_cg)
            errors_qa.append(err_qa)
        # QA должен быть точнее CG в среднем
        mean_cg = np.mean(errors_cg)
        mean_qa = np.mean(errors_qa)
        print(f"  Mean error CG: {mean_cg:.6f}")
        print(f"  Mean error QA: {mean_qa:.6f}")
        assert mean_qa < mean_cg, "QA should be more accurate than CG"
        print(f"  [OK] QA ({mean_qa:.4f}) < CG ({mean_cg:.4f})")


if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all([
        TestDiscrCG(),
        TestDiscrQA(),
        TestDiscrComparison(),
    ])
    runner.print_summary(results)
