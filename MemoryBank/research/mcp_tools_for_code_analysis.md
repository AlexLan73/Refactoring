# MCP-серверы для глубокого анализа кода
*Дата: 2026-04-05*

---

## Текущий статус (Debian, Claude Code global) — обновлено 2026-04-06

| Сервер | Статус | Назначение |
|--------|--------|-----------|
| **sequential-thinking** | ✅ Connected | Пошаговые рассуждения, сложные задачи |
| **context7** | ✅ Connected | Документация библиотек (OpenCL, ROCm, HIP, pybind11) |
| **memory** | ✅ Connected | Граф знаний (entities, relations) |
| **repomix** | ✅ Connected | Упаковка кодовой базы для AI-анализа |
| **filesystem** | ✅ Connected | Прямой доступ к `/home/alex/C++` |
| **fetch** | ✅ Connected | Fetch URL (`uvx mcp-server-fetch`) |
| **git** | ✅ Connected | История git, blame (`uvx mcp-server-git`) |
| **github** | ⏳ Без токена | Нужен PAT — пока не настроен |

---

## Рекомендованный стек для анализа кода

### Для проектов GPUWorkLib + Refactoring

```
sequential-thinking   → Сложная архитектура, выбор решений, математика
context7              → Документация библиотек (OpenCL, ROCm, CMake, pybind11)
github                → Референсный код, примеры, best practices
filesystem            → Прямое чтение файлов проекта
git                   → История изменений, blame, поиск регрессий
repomix               → Упаковка всего модуля в один файл для AI-анализа
```

### Что добавить — repomix (TOP-1 для анализа архитектуры)

**Зачем:** Упаковывает весь репозиторий (или модуль) в один XML/текстовый файл.
AI видит весь контекст сразу — все зависимости, структуру, связи между файлами.

**Идеальное применение:**
- "Проанализируй архитектуру модуля capon целиком"
- "Найди все нарушения паттерна BufferSet<N>"
- "Сравни реализацию heterodyne и statistics"

**Установка:**
```bash
npm install -g repomix
# MCP сервер:
claude mcp add repomix --scope user -- npx -y repomix-mcp
```

**Использование вручную:**
```bash
# Упаковать один модуль
repomix --include "modules/capon/**" --output /tmp/capon_analysis.xml

# Упаковать весь проект (исключить бинарники)
repomix --ignore "build/**,*.exe,*.dll,*.so" --output /tmp/full_project.xml
```

---

## Инструкция настройки на рабочем компьютере (Debian)

### 1. Установить Node.js 20+ (LTS)

```bash
# Через nvm (рекомендуется)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
node --version   # должно быть v20+
npm --version
```

### 2. Установить Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

### 3. Войти в аккаунт

```bash
claude
# или
claude auth login
```

### 4. Добавить MCP серверы глобально (user scope)

```bash
# GitHub MCP (нужен Personal Access Token)
claude mcp add github --scope user \
  -e GITHUB_PERSONAL_ACCESS_TOKEN=<твой_токен> \
  -- npx -y @modelcontextprotocol/server-github

# Sequential Thinking
claude mcp add sequential-thinking --scope user \
  -- npx -y @modelcontextprotocol/server-sequential-thinking

# Context7 (документация библиотек)
claude mcp add context7 --scope user \
  -- npx -y @upstash/context7-mcp@latest

# Memory (граф знаний)
claude mcp add memory --scope user \
  -- npx -y @modelcontextprotocol/server-memory

# Filesystem (путь к проекту на Debian)
claude mcp add filesystem --scope user \
  -- npx -y @modelcontextprotocol/server-filesystem /home/alex/C++/GPUWorkLib

# Git (история изменений)
claude mcp add git --scope user \
  -- npx -y @modelcontextprotocol/server-git --repository /home/alex/C++/GPUWorkLib

# Fetch (загрузка URL)
claude mcp add fetch --scope user \
  -- npx -y @modelcontextprotocol/server-fetch

# Repomix (упаковка кодовой базы)
claude mcp add repomix --scope user \
  -- npx -y repomix-mcp
```

### 5. Проверить что всё работает

```bash
claude mcp list
# Все серверы должны показывать ✓ Connected
```

### 6. Добавить проекты

```bash
# Скопировать CLAUDE.md из GPUWorkLib в Refactoring (если нужно)
cp /home/alex/C++/GPUWorkLib/CLAUDE.md /home/alex/C++/Refactoring/CLAUDE.md
# Отредактировать под специфику проекта
```

### 7. Настройка ~/.claude/settings.json (опционально)

```json
{
  "effortLevel": "high",
  "model": "sonnet",
  "permissions": {
    "additionalDirectories": [
      "/home/alex/C++/GPUWorkLib",
      "/home/alex/C++/Refactoring"
    ]
  }
}
```

---

## Паттерн работы: sequential-thinking + repomix

Самая мощная комбинация для архитектурного анализа:

```
1. repomix → упаковать модуль в один файл
2. sequential-thinking → разобрать архитектуру по шагам:
   - Шаг 1: Что делает модуль?
   - Шаг 2: Какие паттерны использует?
   - Шаг 3: Где нарушения архитектуры?
   - Шаг 4: Что оптимизировать?
3. context7 → проверить best practices для конкретных API
4. github → найти референсные реализации
```

---

## Что НЕ стоит добавлять (лишнее)

| Инструмент | Почему не нужен |
|-----------|----------------|
| **ast-grep MCP** | Можно использовать напрямую через Bash; MCP overhead не оправдан |
| **testsprite** | Только для Web/JS тестов |
| **dap-debug** | Debug-адаптер для IDE, не для CLI Claude Code |
| **sqlite** | Нет активной работы с БД в наших проектах |

---

*Обновлено: 2026-04-05*
*Источник: обсуждение с Кодо в Claude Code*
