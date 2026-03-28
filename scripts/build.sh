#!/bin/bash
# build.sh -- Сборка проекта Refactoring
# Использование: ./scripts/build.sh [module_name]
# Без аргументов -- собирает все модули

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"

echo "=== Refactoring: Build ==="
echo "Repo root: ${REPO_ROOT}"

# Создать build директорию
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# CMake configure
cmake "${REPO_ROOT}" -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release

echo "=== Build complete ==="
