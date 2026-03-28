#!/usr/bin/env python3
"""
Refactoring: запуск всех Python тестов
========================================

Usage:
  python scripts/run_tests.py                  # все модули
  python scripts/run_tests.py discriminator_estimates  # один модуль

Ищет test_python/test_*.py в каждом модуле и запускает через PyCore.TestRunner.
"""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Добавить корень проекта в PYTHONPATH для импорта PyCore
sys.path.insert(0, str(REPO_ROOT))

# Модули для тестирования (папки с test_python/)
MODULES = [
    d.name for d in REPO_ROOT.iterdir()
    if d.is_dir() and (d / "test_python").exists()
]


def run_module_tests(module_name: str) -> int:
    """Запустить все тесты модуля. Возвращает количество ошибок."""
    test_dir = REPO_ROOT / module_name / "test_python"
    if not test_dir.exists():
        print(f"[SKIP] {module_name}: test_python/ не найден")
        return 0

    test_files = sorted(test_dir.glob("test_*.py"))
    if not test_files:
        print(f"[SKIP] {module_name}: нет файлов test_*.py")
        return 0

    errors = 0
    for test_file in test_files:
        print(f"\n--- {module_name}/{test_file.name} ---")
        exit_code = os.system(f'{sys.executable} "{test_file}"')
        if exit_code != 0:
            errors += 1

    return errors


def main():
    if len(sys.argv) > 1:
        modules = [sys.argv[1]]
    else:
        modules = MODULES

    if not modules:
        print("Нет модулей с test_python/ для тестирования")
        return

    print(f"=== Refactoring: Python Tests ===")
    print(f"Модули: {', '.join(modules)}")

    total_errors = 0
    for module in modules:
        total_errors += run_module_tests(module)

    print(f"\n{'=' * 40}")
    if total_errors == 0:
        print(f"Все тесты пройдены!")
    else:
        print(f"ОШИБКИ: {total_errors} модулей с ошибками")
        sys.exit(1)


if __name__ == "__main__":
    main()
