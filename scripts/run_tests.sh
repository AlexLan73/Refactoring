#!/bin/bash
# run_tests.sh -- Запуск всех тестов (C++ и Python)
# Использование: ./scripts/run_tests.sh [module_name]

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Refactoring: Run Tests ==="

# 1. C++ тесты (если скомпилированы)
BUILD_DIR="${REPO_ROOT}/build"
if [ -f "${BUILD_DIR}/test_main" ]; then
    echo "--- C++ Tests ---"
    "${BUILD_DIR}/test_main"
elif [ -f "${BUILD_DIR}/Release/test_main.exe" ]; then
    echo "--- C++ Tests ---"
    "${BUILD_DIR}/Release/test_main.exe"
else
    echo "[SKIP] C++ тесты: test_main не найден (запустите build.sh)"
fi

# 2. Python тесты
echo ""
echo "--- Python Tests ---"
python "${REPO_ROOT}/scripts/run_tests.py" "$@"

echo ""
echo "=== All tests complete ==="
