
---

## Подход 5: Гибридный — FetchContent + find_package (best practice)

Начиная с CMake 3.24, FetchContent может сначала попытаться найти пакет через `find_package`, и только при неудаче — скачать и собрать из исходников:

```cmake
# my-project/CMakeLists.txt
cmake_minimum_required(VERSION 3.24)
project(my-project LANGUAGES CXX)

include(FetchContent)

FetchContent_Declare(
  lib-network
  GIT_REPOSITORY https://github.com/yourorg/lib-network.git
  GIT_TAG        v2.3.1
  FIND_PACKAGE_ARGS NAMES network  # ← сначала попробовать find_package!
)

FetchContent_Declare(
  lib-protocol
  GIT_REPOSITORY https://github.com/yourorg/lib-protocol.git
  GIT_TAG        v1.0.0
  FIND_PACKAGE_ARGS NAMES protocol
)

FetchContent_MakeAvailable(lib-network lib-protocol)

add_executable(myapp src/main.cpp)
target_link_libraries(myapp PRIVATE network::network protocol::protocol)
```

Порядок приоритетов при вызове `FetchContent_MakeAvailable`:

1. Если задан `FETCHCONTENT_SOURCE_DIR_LIB-NETWORK` → берёт локальный путь
2. Если `FIND_PACKAGE_ARGS` задан и `find_package(network)` успешен → использует системную/vcpkg версию
3. Иначе → клонирует из Git и делает `add_subdirectory`

---

## Сравнительная таблица## Что я рекомендую для вас

Раз вы ориентируетесь на CMake 3.24+, лучшая стратегия — **подход 5 (гибридный FetchContent + FIND_PACKAGE_ARGS)** в связке с **CMakePresets.json**:

**В CMakeLists.txt** — пишете чистый, переносимый код с `FetchContent_Declare(..., FIND_PACKAGE_ARGS ...)`. Никаких хардкодов путей.

**В CMakePresets.json** — для каждого сценария свой пресет: `dev-local` с `FETCHCONTENT_SOURCE_DIR_*` на соседние каталоги, `ci` без переопределений (тянет из Git), `prod` с vcpkg toolchain (бинарники).

Таким образом каждый разработчик работает со своими локальными ветками соседних проектов, CI всё тянет из репозиториев с фиксированными тегами, а production-сборка использует предкомпилированные бинарники из vcpkg — и всё это без единого изменения в `CMakeLists.txt`.

Хотите, могу собрать готовый шаблон проекта с этой структурой?
