---
name: github-ops
description: "Use when searching GitHub repositories, inspecting issues, analyzing pull requests, checking CI/CD workflow runs, reading remote code, or tracking releases."
version: "1.0.0"
lifecycle: ACTIVE
domain: engineering
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
probe_cmd: "test -x /opt/homebrew/bin/gh || which gh > /dev/null"
---
# 🐙 GitHub Operations Skill (`github-ops`)

> 💡 **TL;DR:** Sovereign, token-efficient GitHub integration using the official GitHub CLI (`gh`). Adheres strictly to **Rule #16 (Think in Code / Terminal Filtering)**, **Rule #44 (Context Bundling & Stream Trimming)**, and **Rule #59 (Official Toolchain Gate)**. Replaces heavy raw JSON dumps with precise `--json` and `--jq` filtering to reduce LLM context consumption by $\ge 95\%$.
> 🛡️ **Air-Gap Invariant (Rule #58 & Rule #67):** The local Obsidian Vault is hermetic and not a git repository. This skill operates strictly on external repositories (e.g. in `/WORK/`, Pulsar, Xcode, or open-source GitHub remotes). Never push or export internal Vault notes to public remotes without explicit approval.
> 🔗 **Cross-Links:** [[SYSTEM|SYSTEM.md]] | [[and_os/lib/skills/ROUTING|ROUTING.md]] | [[and_os/lib/skills/REGISTRY|REGISTRY.md]]

---

## 🎯 Architecture & Operating Principles

1. **Official Toolchain First:**
   - Uses `/opt/homebrew/bin/gh` natively without unverified Python wrapper layers.
   - Authentication is managed via system Keychain (`gh auth status`).
2. **Context Budget Protection (Rule #44):**
   - NEVER run bare commands like `gh issue view` or `gh pr diff` without limits or filters.
   - Always project fields using `--json` and format cleanly via `--jq` to return $< 100$ tokens of actionable data.
3. **Approval Safeguard for State Mutations:**
   - **Read Operations (Autonomous):** `gh search`, `gh issue list/view`, `gh pr list/view/checks`, `gh run view`, `gh release list/view`.
   - **Write Operations (Requires User Confirmation):** `gh issue create/close`, `gh pr create/merge/review`, `gh release create`. Always display the payload to the user before submitting.

---

## ⚙️ Execution Contours

Detailed projection patterns, jq recipes, and release invariants are codified in:
- [[and_os/lib/skills/github-ops/references/gh_recipes|gh_recipes.md]] (Contour A: Daily Operations Recipes)
- [[and_os/lib/skills/github-ops/references/zero_leak_release_protocol|zero_leak_release_protocol.md]] (Contour B: Zero-Leak Release Protocol & Air-Gap Locks)

---

### 🌐 КОНТУР А: Оперативное взаимодействие (Daily Operations & Telemetry)
*Применяется для быстрого токеноэффективного анализа открытых репозиториев, PR, задач и CI/CD.*

- **Mode 1: Fast Repository & Code Discovery:**
  ```bash
  /opt/homebrew/bin/gh search repos "<query>" --limit 5 --json fullName,description,stargazersCount,updatedAt --jq '.[] | "\(.fullName) (\(.stargazersCount)★): \(.description)"'
  ```
- **Mode 2: Issue Triage & Summarization:**
  ```bash
  /opt/homebrew/bin/gh issue list --repo <owner/repo> --state open --limit 10 --json number,title,labels,updatedAt --jq '.[] | "#\(.number) [\(.labels | map(.name) | join(","))]: \(.title)"'
  ```
- **Mode 3: Pull Request Analysis (Zero-Diff Invariant):**
  ```bash
  /opt/homebrew/bin/gh pr view <number> --repo <owner/repo> --json title,state,author,files,reviewDecision --jq '{title: .title, state: .state, author: .author.login, review: .reviewDecision, files: [.files[].path]}'
  ```
- **Mode 4: CI/CD Workflow Health & Failed Logs:**
  ```bash
  /opt/homebrew/bin/gh run list --repo <owner/repo> --limit 5 --json databaseId,status,conclusion,name,headBranch --jq '.[] | "[\(.conclusion // .status)] #\(.databaseId) \(.name) (\(.headBranch))"'
  /opt/homebrew/bin/gh run view <run-id> --repo <owner/repo> --log-failed
  ```

---

### 🛡️ КОНТУР Б: Регламент безопасной публикации ядра (Zero-Leak Release Pipeline)
*Применяется строго при экспорте и выкладке модулей из хранилища в открытый доступ на GitHub.*

1. **Тотальные локи приватных каталогов (Vault Red Zone):**
   - 🔒 `Nero/` (Здоровье, анализы, семья, биометрия telemetry_sync, личные цели) — **ЗАПРЕЩЕНО К ЭКСПОРТУ**.
   - 🔒 `Product/`, `Studio/`, `Tasks/` (Студийные проекты полнометражной анимации, NDA, сметы) — **ЗАПРЕЩЕНО**.
   - 🔒 `Ta-Bu/`, `Story/`, `Book/` (Сценарии, книги, питчи стартапа) — **ЗАПРЕЩЕНО**.
   - 🔒 `Industry/`, `Clippings/` (Выжимки книг, приватный консалтинг) — **ЗАПРЕЩЕНО**.
   - 🔒 `and_os/var/`, `and_os/backups/` (Реальные базы SQLite, токены сессий) — **ЗАПРЕЩЕНО**.
2. **Адаптация путей и связей (Autonomous Portability):**
   - Замена абсолютных путей `~/...` на относительные `./`.
   - Замена персональных/студийных имен на системные псевдонимы (`System Architect`, `Studio`).
   - Проверка отсутствия битых ссылок (Zero-Dangling Links) через `link_guard.py`.
3. **Многоуровневый фильтр качества в staged-каталоге:**
   - Шаг 1: `and_os/.venv/bin/python3 and_os/bin/export_kernel.py` (0 утечек).
   - Шаг 2: `quick_verify.py` внутри staged-каталога (`🟢 ALL PHASES PASSED`, 0 critical defects).
   - Шаг 3: `sys_cli skills --probe` (100% канареек здоровы).
   - Шаг 4: Наличие витрины (`README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`).
4. **Финальный гейт публикации:**
   - Публикация разрешена **строго после явного подтверждения Андрея** командой:
     ```bash
     /opt/homebrew/bin/gh repo create <owner>/<repo> --public --source=<path> --push --description "<desc>"
     ```

---

## 📋 Definition of Done Checklist

Перед завершением любой операции через скилл `github-ops`:
- [ ] **Контур А (Повседневный):** Вывод отфильтрован через `--jq` (никаких портянок терминала $> 50$ строк).
- [ ] **Контур Б (Релизный):**
  - [ ] Ни один файл из Red Zone (`Nero/`, `Product/`, `Ta-Bu/`, `Story/`, `Clippings/`) не попал в git.
  - [ ] Пути адаптированы, абсолютные пути `~` полностью нейтрализованы.
  - [ ] Пакетные манифесты присутствуют: `.gitignore`, `pyproject.toml`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`.
  - [ ] Байткод (`__pycache__`, `*.pyc`), логи тестов (`events.jsonl`) и артефакты БД очищены.
  - [ ] Авторство коммита нейтрализовано: `System Architect <noreply@github.com>` (без локальных хостов).
  - [ ] `quick_verify.py` вернул `🟢 ALL PHASES PASSED`.
  - [ ] Канарейки скиллов `sys_cli skills --probe` подтвердили 100% здоровье.
  - [ ] Рабочее дерево `git status --porcelain` кристально чистое (0 untracked/dirty файлов).
  - [ ] Любое создание репозитория или `push` явно подтверждены пользователем.
