# Memory Manage Protocol (Review / Prune / Export)

> **Mandatory Reference for `knowledge-promoter` Mode 3 (v2.1).**  
> Periodic memory-diet procedure: keep the closed-loop memory (Rule #13) lean and current without losing evidence.

---

## 1. When to Run

- Quarterly, or after any large skill cycle that produced multiple `learn` records.
- **Mandatory trigger:** any domain holding more than 30 active (`status: VERIFIED`) records.
- After a toolchain/stack change (renamed engines, moved paths) — stale-reference sweep.

## 2. Record Anatomy (SSoT)

- **Note** (source of truth): `Nero/knowledge/engineers/<topic_slug>.md`, frontmatter carries `status:`, `domain:`, dates.
- **Index entry** (fast lookup only): `Clippings/quick_knowledge_db.json`, records with `source` starting `[[Nero/knowledge/engineers/`.
- The note frontmatter wins over the index on any conflict; the index is rebuilt, the note is not.

## 3. Review Procedure (Read-Only)

1. Count records per domain:
   ```bash
   python3 -c "import json; db=json.load(open('Clippings/quick_knowledge_db.json')); import collections; recs=[r for r in db if str(r.get('source','')).startswith('[[Nero/knowledge/engineers/')]; print(collections.Counter(r.get('category','?') for r in recs).most_common())"
   ```
2. Point queries per domain: `python3 and_os/bin/sys_cli.py find "<domain-keyword>" --json --limit 50`.
3. For each candidate for pruning, read the note frontmatter via the Vault Guard (`sys_cli.py vault patch --dry-run` read path or `mcp_vault_guard` section read) — never blind full-file reads of `Nero/` notes (Rule #19).

## 4. Prune Criteria (status transition, never deletion)

| # | Criterion | Test | Action |
| :---: | :--- | :--- | :--- |
| 1 | Superseded | A newer record on the same topic carries a better/verified solution | `status: PRUNED` + `superseded_by: <newer note>` |
| 2 | Stale reference | The record cites a tool/path/command that no longer exists (verify with `skill_diet.py` drift logic or a direct probe) | `status: PRUNED` + `prune_reason: stale reference: <what>` |
| 3 | Duplicate | Same pattern recorded twice (same domain + near-identical problem/solution) | keep the newer/better note; prune the other with `prune_reason: duplicate of <note>` |
| 4 | Unverifiable legacy | No verification trail and pre-dates the Proof-of-Reality Gate | `status: REVIEW` (not auto-prune) — route to the user |

Mechanics (all via the Vault Guard, zero physical deletion):
```bash
python3 and_os/bin/sys_cli.py vault patch --file Nero/knowledge/engineers/<note>.md \
  --find "status: VERIFIED" --replace "status: PRUNED"
python3 and_os/bin/sys_cli.py vault patch --file Nero/knowledge/engineers/<note>.md \
  --find "<last frontmatter line>" --replace "<last frontmatter line>
pruned: 2026-11-13
prune_reason: <one line>"
```
Index entries are **kept** (the note frontmatter is the status SSoT; the retriever must check `status:` before acting on a record).

## 5. Export Format (per-domain digest)

Output: `Nero/knowledge/memory_export_<domain>_<YYYY-MM-DD>.md`
```markdown
---
type: memory-export
domain: <domain>
exported: <YYYY-MM-DD>
active: <n>
pruned_total: <n>
---
# Memory Digest — <domain> (<n> active)
| # | Topic | Problem (short) | Solution (short) | Since |
| :--- | :--- | :--- | :--- | :--- |
```
Digest lists ACTIVE records only; PRUNED records are counted, not listed (their notes remain in place as evidence).

## 6. Invariants

- **Zero physical deletion** of learn-notes; `sys_cli.py trash` is not used for records (it is for files).
- Every prune is auditable: `pruned:` date + `prune_reason:` are mandatory frontmatter fields.
- A pruned record that is needed again is restored (`status: VERIFIED` + `restored:` date) — the evidence never left the vault.
- Export digests are created, never rewritten in place; each export is a dated snapshot.
- The Manage pass is read-mostly: it must not create new learn-records (writing memory is Mode 2's job).
