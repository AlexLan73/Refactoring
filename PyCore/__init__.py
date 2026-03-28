"""
PyCore -- общая инфраструктура тестирования проекта Refactoring
================================================================

Источник: адаптировано из GPUWorkLib/Python_test/common (без GPU-специфики).

Пакеты:
    result      -- TestResult, ValidationResult (value objects)
    validators  -- IValidator + DataValidator (Strategy GoF)
    runner      -- TestRunner + SkipTest
    reporters   -- IReporter + ConsoleReporter / JSONReporter
    test_base   -- TestBase (Template Method для C-библиотек)
    plotting    -- IPlotter ABC + PlotConfig
"""

from .result import TestResult, ValidationResult
from .validators import IValidator, DataValidator
from .runner import TestRunner, SkipTest

__all__ = [
    "TestResult", "ValidationResult",
    "IValidator", "DataValidator",
    "TestRunner", "SkipTest",
]
