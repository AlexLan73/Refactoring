"""
validators.py -- DataValidator (Strategy GoF)
=============================================

Один универсальный класс для сравнения результатов C-функций с эталоном numpy.

Classes:
    IValidator    -- абстрактный интерфейс (Strategy GoF)
    DataValidator -- универсальный валидатор, метрика задаётся при создании
"""

from abc import ABC, abstractmethod
import numpy as np

from .result import ValidationResult


class IValidator(ABC):
    """Абстрактный валидатор -- Strategy interface."""

    @abstractmethod
    def validate(self, actual: np.ndarray,
                 reference: np.ndarray) -> ValidationResult:
        """Сравнить actual с reference, вернуть ValidationResult.

        Args:
            actual:    результат C-функции
            reference: эталонный результат (numpy/scipy)

        Returns:
            ValidationResult с passed=True если проверка пройдена
        """
        ...


class DataValidator(IValidator):
    """Универсальный валидатор: скаляр / вектор / матрица.

    Strategy (GoF) -- метрика выбирается при создании.

    Метрики:
        "max_rel" -> max(|actual - ref|) / max(|ref|) < tolerance
                    Для сигналов, координат, статистики.
                    При ref ~ 0 переключается на абсолютный допуск 1e-10.

        "abs"     -> max(|actual - ref|) < tolerance
                    Для углов, индексов, дискретных значений.

        "rmse"    -> rms(|actual - ref|) / rms(|ref|) < tolerance
                    Для шумных данных где нужна среднеквадратичная метрика.

    Usage:
        v = DataValidator(tolerance=0.001, metric="max_rel")
        r = v.validate(c_result, numpy_ref, name="azimuth_cg")
        print(r)   # [PASS] azimuth_cg: 0.0003 (threshold=0.001)
    """

    METRICS = ("max_rel", "abs", "rmse")

    def __init__(self, tolerance: float,
                 metric: str = "max_rel",
                 name: str = ""):
        if metric not in self.METRICS:
            raise ValueError(
                f"metric должен быть одним из {self.METRICS}, получено: {metric!r}"
            )
        self.tolerance = tolerance
        self.metric = metric
        self._default_name = name

    def validate(self, actual, reference,
                 name: str = "") -> ValidationResult:
        """Сравнить actual с reference.

        Args:
            actual:    результат C-функции (скаляр, list, np.ndarray)
            reference: эталон (скаляр, list, np.ndarray)
            name:      имя метрики для ValidationResult

        Returns:
            ValidationResult
        """
        metric_name = name or self._default_name or self.metric
        a = np.atleast_1d(np.asarray(actual)).ravel().astype(np.float64)
        r = np.atleast_1d(np.asarray(reference)).ravel().astype(np.float64)

        if self.metric == "max_rel":
            return self._max_rel(a, r, metric_name)
        elif self.metric == "abs":
            return self._abs(a, r, metric_name)
        else:
            return self._rmse(a, r, metric_name)

    def _max_rel(self, a, r, name) -> ValidationResult:
        diff = np.abs(a - r)
        ref_norm = np.max(np.abs(r))
        if ref_norm < 1e-15:
            err = float(np.max(diff))
            return ValidationResult(
                passed=err < 1e-10,
                metric_name=name,
                actual_value=err,
                threshold=1e-10,
                message="(near-zero reference, using absolute tolerance)"
            )
        err = float(np.max(diff) / ref_norm)
        return ValidationResult(
            passed=err < self.tolerance,
            metric_name=name,
            actual_value=err,
            threshold=self.tolerance,
        )

    def _abs(self, a, r, name) -> ValidationResult:
        err = float(np.max(np.abs(a - r)))
        return ValidationResult(
            passed=err < self.tolerance,
            metric_name=name,
            actual_value=err,
            threshold=self.tolerance,
        )

    def _rmse(self, a, r, name) -> ValidationResult:
        diff = a - r
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        ref_rms = float(np.sqrt(np.mean(r ** 2)))
        if ref_rms < 1e-15:
            return ValidationResult(
                passed=rmse < 1e-10,
                metric_name=name,
                actual_value=rmse,
                threshold=1e-10,
                message="(near-zero reference)"
            )
        err = rmse / ref_rms
        return ValidationResult(
            passed=err < self.tolerance,
            metric_name=name,
            actual_value=err,
            threshold=self.tolerance,
        )
