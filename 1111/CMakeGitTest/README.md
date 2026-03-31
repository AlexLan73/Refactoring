# CMakeGitTest

Учебный проект: демонстрация **Подхода 5** — гибридное управление зависимостями через `FetchContent` + `FIND_PACKAGE_ARGS` с локальными git-репозиториями.

---

## Структура проекта

```
CMakeGitTest/
├── lib-network/          ← библиотека: ping / connect / disconnect
│   ├── CMakeLists.txt
│   ├── cmake/
│   │   └── networkConfig.cmake.in
│   ├── include/network/network.hpp
│   └── src/network.cpp
│
├── lib-protocol/         ← библиотека: encode / decode / validate
│   ├── CMakeLists.txt
│   ├── cmake/
│   │   └── protocolConfig.cmake.in
│   ├── include/protocol/protocol.hpp
│   └── src/protocol.cpp
│
└── my-project/           ← основное приложение
    ├── CMakeLists.txt
    ├── CMakePresets.json
    └── src/main.cpp
```

Каждая библиотека — **независимый git-репозиторий** с тремя тегами версий.

---

## История версий библиотек

### lib-network

| Тег | Добавлено | API |
|-----|-----------|-----|
| `v1.0.0` | базовая версия | `ping(host)` |
| `v1.1.0` | новая функция | `ping` + `connect(host, port)` |
| `v2.0.0` | новая функция | `ping` + `connect` + `disconnect(host)` |

### lib-protocol

| Тег | Добавлено | API |
|-----|-----------|-----|
| `v1.0.0` | базовая версия | `encode(message)` |
| `v1.1.0` | новая функция | `encode` + `decode(frame)` |
| `v2.0.0` | новая функция | `encode` + `decode` + `validate(frame)` |

Посмотреть историю:

```bash
cd lib-network && git log --oneline --decorate
cd lib-protocol && git log --oneline --decorate
```

---

## Концепция: зачем гибридный подход

Классическая проблема: в `CMakeLists.txt` нельзя одновременно удовлетворить всех:

| Сценарий | Что нужно |
|----------|-----------|
| Разработчик правит lib и app одновременно | Видеть несохранённые изменения в lib без коммита |
| Тестирование конкретной версии | Точно знать, какой код используется (по тегу) |
| Система пакетов (vcpkg, conan) | Использовать заранее собранные бинарники |

**Решение:** `CMakeLists.txt` описывает только *что* нужно. *Как* получить — управляется **снаружи**, через пресеты.

### Приоритет FetchContent_MakeAvailable

```
Задан FETCHCONTENT_SOURCE_DIR_LIBNETWORK?
  ДА  → берём папку напрямую (add_subdirectory), git не вызывается
  НЕТ → find_package(network CONFIG) найден?
          ДА  → используем установленную версию
          НЕТ → git clone по GIT_REPOSITORY + GIT_TAG
```

---

## Пресеты

### `dev-local` — рабочая копия

```bash
cmake --preset dev-local
cmake --build my-project/build
```

**Как работает:**
Пресет устанавливает переменные:
```
FETCHCONTENT_SOURCE_DIR_LIBNETWORK  = ../lib-network
FETCHCONTENT_SOURCE_DIR_LIBPROTOCOL = ../lib-protocol
```

CMake видит эти переменные и **полностью обходит git**. Вместо клонирования он делает `add_subdirectory` прямо на указанные папки. Это означает:

- Uncommitted изменения в `lib-network` **сразу видны** в сборке — не нужно делать `git commit` перед каждой перекомпиляцией.
- Конфигурация происходит мгновенно — нет сетевых или дисковых операций клонирования.
- Папка-источник может быть вообще не git-репозиторием.

**Когда использовать:** при одновременной работе над библиотекой и приложением — правишь `lib-network/src/network.cpp`, сразу пересобираешь `my-project`.

---

### `dev-tag` — пинированный тег из локального git

```bash
cmake --preset dev-tag
cmake --build my-project/build-tag
```

**Как работает:**
Пресет не задаёт `FETCHCONTENT_SOURCE_DIR_*`. CMake смотрит в `CMakeLists.txt`:

```cmake
FetchContent_Declare(
  libnetwork
  GIT_REPOSITORY /home/alex/C++/CMakeGitTest/lib-network
  GIT_TAG        v2.0.0
  ...
)
```

и выполняет:
```
git clone /home/alex/C++/CMakeGitTest/lib-network  --branch v2.0.0
```

Клон помещается в `my-project/build-tag/_deps/libnetwork-src/`. Используется **только то, что закоммичено под тегом `v2.0.0`** — никакие незакоммиченные изменения в рабочей копии `lib-network` не видны.

**Зачем это нужно — ключевое объяснение:**

Представь ситуацию: ты вносишь экспериментальные изменения в `lib-network`, но ещё не уверен в них. Тебе нужно проверить, как работает основной проект с **последней стабильной версией** `v2.0.0`, а не с экспериментом.

С `dev-tag` ты можешь:
1. Держать незакоммиченные изменения в `lib-network`.
2. Собрать `my-project` с `dev-tag` — он возьмёт строго `v2.0.0` из git.
3. Сравнить результат с `dev-local` (где будут твои эксперименты).

Также `dev-tag` моделирует поведение **CI-сервера**: CI не знает о твоей рабочей папке, он всегда берёт код из git по конкретному тегу.

> **Важно:** при смене `GIT_TAG` в `CMakeLists.txt` нужно удалить `build-tag/_deps/`
> или запустить `cmake --preset dev-tag` заново — CMake сделает новый клон.

**Когда использовать:**
- Для проверки совместимости с конкретной версией библиотеки.
- Для воспроизведения поведения CI-сборки локально.
- Когда важна воспроизводимость: точно знаешь, какой именно код собирается.

---

## Сравнение пресетов

| | `dev-local` | `dev-tag` |
|---|---|---|
| **Источник кода** | Рабочая папка напрямую | git clone по тегу |
| **Git задействован?** | Нет | Да |
| **Видит uncommitted изменения?** | **Да** | **Нет** |
| **Скорость configure** | Мгновенно | Медленнее (клонирование при первом запуске) |
| **Билд-папка** | `build/` | `build-tag/` |
| **Сценарий** | Активная разработка | Тестирование версии / воспроизведение CI |

---

## Быстрый старт

```bash
# Клонировать / перейти в папку проекта
cd my-project

# Вариант 1: рабочая копия (uncommitted изменения видны)
cmake --preset dev-local
cmake --build build
./build/myapp

# Вариант 2: строгий тег из git
cmake --preset dev-tag
cmake --build build-tag
./build-tag/myapp
```

Ожидаемый вывод:
```
ping:     pong from localhost
connect:  1
frame:    [PROTO] pong from localhost
decoded:  pong from localhost
valid:    1
```

---

## Сменить версию библиотеки

Чтобы взять, например, `v1.0.0` вместо `v2.0.0`:

1. В [my-project/CMakeLists.txt](my-project/CMakeLists.txt) изменить `GIT_TAG v2.0.0` → `GIT_TAG v1.0.0`.
2. Удалить `build-tag/_deps/` (старый клон).
3. `cmake --preset dev-tag && cmake --build build-tag`.

С `v1.0.0` доступна только функция `ping()` — `connect()` и `disconnect()` ещё не существуют.

---

## Как работает ALIAS и зачем он нужен

В каждой библиотеке:
```cmake
add_library(network src/network.cpp)          # реальная цель: network
add_library(network::network ALIAS network)   # псевдоним:     network::network
```

Потребитель пишет:
```cmake
target_link_libraries(myapp PRIVATE network::network)
```

Это имя работает **в обоих сценариях**:

- `find_package(network CONFIG)` → CMake создаёт IMPORTED-цель `network::network` (из `install(EXPORT ... NAMESPACE network::)`)
- `FetchContent` / `add_subdirectory` → создаётся только `network`, но ALIAS делает `network::network` доступным

Без ALIAS FetchContent-сценарий падал бы с ошибкой: `target network::network not found`.

---

## Требования

- CMake >= 3.24 (требуется для `FIND_PACKAGE_ARGS` в `FetchContent_Declare`)
- GCC / Clang с поддержкой C++17
- Git
