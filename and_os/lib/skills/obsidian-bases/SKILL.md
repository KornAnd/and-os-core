---
name: obsidian-bases
description: "Use when creating, validating, and maintaining Obsidian Bases (.base files) with views, reactive filters, formulas, and summaries for database-like tables across vault notes."
version: "1.0.0"
lifecycle: ACTIVE
domain: system
island: 8
context_tier: WORK
facade_binding: "sys_cli"
modality: DECLARATIVE_KNOWLEDGE
allowed-tools: ["Read", "Write", "Grep", "Bash"]
probe_cmd: "test -d and_os/lib/skills/obsidian-bases"
---
## Catalogs & Scope
- [[and_os/lib/skills/ROUTING|ROUTING — Skills and domain routing matrix]]
- [[SYSTEM|SYSTEM — Core manifest and governance]]
- [[and_os/docs/specs/ANTI_SLOP_STANDARD|Anti-Slop standard]]

## Scope
Defines standards and validation rules for **Obsidian Bases (`.base` files)** in AnD os. Enables declarative, reactive, database-like representations over vault markdown frontmatter properties without requiring heavy third-party JavaScript plugins (Dataview).

---

## ⚙️ Architecture & File Structure

A `.base` file is a strict YAML configuration containing 4 top-level sections:

```yaml
filters:
  and:
    - file.inFolder("Folder/Path")
    - 'file.ext == "md"'

formulas:
  days_ago: '(today() - date(date)).days'
  is_active: 'if(status != "done", true, false)'

properties:
  formula.days_ago:
    displayName: "Days Elapsed"
  formula.is_active:
    displayName: "Active"

views:
  - type: table
    name: "Default View"
    order:
      - file.name
      - formula.days_ago
      - formula.is_active
    summaries:
      file.name: Count
```

---

## 📐 View Types

| View Type | Structure & Best Use |
|-----------|----------------------|
| `table`   | Tabular view with column sorting, grouping (`groupBy`), and aggregation summaries (`Sum`, `Average`, `Count`, `Latest`). |
| `cards`   | Visual gallery/kanban cards using frontmatter metadata (`cover_image`, `sticker`, `color`). |
| `list`    | Compact single-column view with primary status property. |
| `map`     | Geographic map view requiring latitude/longitude properties. |

---

## ⚡ Core Formula Rules & Invariants

1. **Duration Invariant (CRITICAL):**
   - Subtracting dates `(date(due) - today())` returns a **Duration** object, NOT a scalar integer.
   - You MUST access `.days`, `.hours`, or `.minutes` before applying numeric math or rounding:
     ```yaml
     # CORRECT:
     "(date(due) - today()).days"
     "(today() - date(created)).days.round(0)"

     # FORBIDDEN (Crashes Obsidian Base engine):
     "((date(due) - today()) / 86400000).round(0)"
     ```

2. **YAML Quote Escaping:**
   - Always wrap formulas containing double quotes inside single quotes:
     ```yaml
     # CORRECT:
     status_label: 'if(status == "done", "🟢 Done", "🟡 Active")'

     # FORBIDDEN:
     status_label: "if(status == "done", "🟢 Done", "🟡 Active")"
     ```

3. **Null-Safety Guard:**
   - Guard missing optional properties with `if()` to prevent formula runtime crashes:
     ```yaml
     days_remaining: 'if(due, (date(due) - today()).days, "")'
     ```

---

## 🔗 Embed Syntax in Markdown Notes

To embed an Obsidian Base into any markdown report or dashboard:

```markdown
![[Database_Name.base]]

<!-- Embed specific view -->
![[Database_Name.base#View Name]]
```

---

## ✅ Verification Checklist
- [ ] YAML syntax valid with zero tab characters
- [ ] Duration calculations explicitly access scalar properties (`.days`)
- [ ] Formulas wrapped in single quotes when containing double-quoted strings
- [ ] All `formula.X` references in `views.order` defined in `formulas` block
- [ ] Embed links tested in reading view
