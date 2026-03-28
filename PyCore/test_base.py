"""
test_base.py -- TestBase для C-библиотек (Template Method)
===========================================================

Template Method (GoF):
  TestBase.run() определяет неизменный скелет теста.
  Подклассы переопределяют hooks: get_params, generate_data, compute, validate.

Адаптирован для проекта Refactoring: работа с C-библиотеками через ctypes.
Нет зависимостей от GPU.

Usage:
    class TestDiscrCG(TestBase):
        def get_params(self):
            return {"points": 2, "type": "cg"}

        def generate_data(self, params):
            return np.random.randn(2, 2)

        def compute(self, data, params):
            lib = ctypes.CDLL('./libdiscr.so')
            # ... вызов C-функции ...
            return result

        def validate(self, result, params):
            v = DataValidator(tolerance=0.001, metric="max_rel")
            vr = v.validate(result, numpy_reference, name="az_cg")
            tr = TestResult("test_cg")
            return tr.add(vr)

    test = TestDiscrCG()
    result = test.run()
    print(result.summary())
"""

from abc import ABC, abstractmethod
import numpy as np

from .result import TestResult


class TestBase(ABC):
    """Абстрактный базовый класс для тестирования C-библиотек.

    Template Method (GoF) -- run() задаёт скелет, подклассы реализуют hooks.

    Hooks (переопределяются в подклассах):
        get_params()         -> конфигурация теста
        generate_data()      -> тестовые данные (numpy array)
        compute()            -> вызов C-функции -> результат
        validate()           -> сравнение с эталоном -> TestResult

    Optional hooks:
        setup()              -> дополнительная инициализация
        teardown()           -> очистка ресурсов
    """

    name: str = ""

    def __init__(self, name: str = ""):
        if name:
            self.name = name
        if not self.name:
            self.name = self.__class__.__name__

    def run(self) -> TestResult:
        """Неизменный скелет теста (Template Method).

        Шаги:
          1. setup()          -- инициализация
          2. get_params()     -- конфигурация
          3. generate_data()  -- входные данные
          4. compute()        -- вызов C-функции
          5. validate()       -- проверка результатов
          6. teardown()       -- очистка
        """
        result = TestResult(test_name=self.name)
        try:
            self.setup()
            params = self.get_params()
            data = self.generate_data(params)
            output = self.compute(data, params)
            result = self.validate(output, params)
            result.test_name = self.name
        except Exception as e:
            result.error = e
        finally:
            self.teardown()
        return result

    def setup(self) -> None:
        """Хук инициализации (загрузка библиотеки и т.д.)."""
        pass

    def teardown(self) -> None:
        """Хук очистки."""
        pass

    @abstractmethod
    def get_params(self):
        """Вернуть конфигурацию теста."""
        ...

    @abstractmethod
    def generate_data(self, params) -> np.ndarray:
        """Сгенерировать входные данные теста."""
        ...

    @abstractmethod
    def compute(self, data: np.ndarray, params):
        """Вызвать C-функцию и вернуть результат."""
        ...

    @abstractmethod
    def validate(self, result, params) -> TestResult:
        """Сравнить результат C-функции с эталоном."""
        ...
