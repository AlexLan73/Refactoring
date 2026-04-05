# Инструкция: Настройка MCP на рабочем компьютере (Debian/Linux)
*Автор: Кодо | Дата: 2026-04-05*

> ⚠️ **ВАЖНО**: `.mcp.json` в `.gitignore` — через git не передаётся!
> Этот файл нужно создавать руками на каждой машине отдельно.

---

## Шаг 1 — Проверить/установить Node.js 20+

```bash
node --version   # нужно v20+

# Если нет или старая версия — установить через nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc   # или source ~/.zshrc
nvm install 20
nvm use 20
nvm alias default 20   # сделать дефолтной
node --version   # должно быть v20.x.x
npm --version    # должно быть 10+
```

---

## Шаг 2 — Установить uv + uvx (нужен для git и fetch MCP)

```bash
# uvx — запускает Python MCP-серверы (git, fetch)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc   # или source ~/.zshrc
uvx --version      # должно быть 0.8+
```

---

## Шаг 3 — Проверить/установить Claude Code

```bash
claude --version

# Если нет:
npm install -g @anthropic-ai/claude-code

# Войти в аккаунт:
claude auth login
```

---

## Шаг 3 — Создать .mcp.json для GPUWorkLib

```bash
# Открыть проект
cd ~/C++/GPUWorkLib

# Создать файл (ВРУЧНУЮ — в git не коммитить!)
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "env": {}
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/alex/C++/GPUWorkLib"],
      "env": {}
    },
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    },
    "git": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/home/alex/C++/GPUWorkLib"],
      "env": {}
    },
    "fetch": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    },
    "repomix": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "repomix-mcp"],
      "env": {}
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ВАШ_GITHUB_TOKEN_ЗДЕСЬ"
      }
    }
  }
}
EOF
```

> ⚠️ Замени `ВАШ_GITHUB_TOKEN_ЗДЕСЬ` на реальный токен (см. ниже как получить).

---

## Шаг 4 — Создать .mcp.json для Refactoring

```bash
cd ~/C++/Refactoring

cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "sequential-thinking": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "env": {}
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "env": {}
    },
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/alex/C++/Refactoring"],
      "env": {}
    },
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    },
    "git": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "/home/alex/C++/Refactoring"],
      "env": {}
    },
    "fetch": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {}
    },
    "repomix": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "repomix-mcp"],
      "env": {}
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ВАШ_GITHUB_TOKEN_ЗДЕСЬ"
      }
    }
  }
}
EOF
```

---

## Шаг 5 — Получить GitHub Personal Access Token

1. Открыть: https://github.com/settings/tokens
2. Нажать **"Generate new token (classic)"**
3. Название: `claude-code-linux`
4. Срок: 90 дней или без срока
5. Разрешения:
   - ✅ `repo` (полный доступ к репозиториям)
   - ✅ `read:org` (если используешь организацию)
6. Нажать **Generate token** — скопировать сразу!
7. Вставить в `.mcp.json` вместо `ВАШ_GITHUB_TOKEN_ЗДЕСЬ`

---

## Шаг 6 — Проверить все серверы

```bash
cd ~/C++/GPUWorkLib
claude mcp list
```

Ожидаемый результат — все `✓ Connected`:
```
sequential-thinking: ... ✓ Connected
context7:            ... ✓ Connected
filesystem:          ... ✓ Connected
memory:              ... ✓ Connected
git:                 ... ✓ Connected
fetch:               ... ✓ Connected
repomix:             ... ✓ Connected
github:              ... ✓ Connected
```

Если что-то `✗ Failed` — проверь:
```bash
node --version    # v20+?
npx --version     # есть?
which npx         # путь найден?
```

---

## Шаг 7 — Настроить ~/.claude/settings.json

```bash
mkdir -p ~/.claude
cat > ~/.claude/settings.json << 'EOF'
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
EOF
```

---

## Проверка безопасности — .mcp.json не в git

```bash
cd ~/C++/GPUWorkLib
git check-ignore -v .mcp.json
# Должно показать: .gitignore:111:.mcp.json

git ls-files .mcp.json
# Должно быть ПУСТО (файл не отслеживается)

cd ~/C++/Refactoring
git check-ignore -v .mcp.json
git ls-files .mcp.json
# Аналогично — пусто
```

> ✅ Если `git ls-files` пустой — токены в безопасности, в GitHub не уйдут!

---

## Разница конфигов: Windows vs Linux

| Параметр | Windows | Linux |
|----------|---------|-------|
| filesystem path | `E:/C++/GPUWorkLib` | `/home/alex/C++/GPUWorkLib` |
| git repo | `E:/C++/GPUWorkLib` | `/home/alex/C++/GPUWorkLib` |
| github token | Свой токен Windows | Свой токен Linux |
| node | `npx` | `npx` |

`.mcp.json` — **локальный файл на каждой машине**, в git не попадает. ✅

---

*Сохранено: 2026-04-05 | Кодо*
