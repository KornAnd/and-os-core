# GitHub CLI (`gh`) Token-Efficient Recipes & Projections

> Reference guide for `github-ops` skill. Provides deterministic, token-efficient command templates using the official GitHub CLI (`gh`) with `--json` and `--jq` filtering.  
> **Recipe validity invariant (v1.1):** all `--json` field names validated against the live API on 2026-11-13; jq projections are null-safe (`// fallback`). Re-validate fields after any major `gh` update.

---

## 1. Authentication & Status

```bash
# Check current authentication status (run before ANY write operation:
# token present, correct account, least-privilege scopes for the intended action)
/opt/homebrew/bin/gh auth status

# Interactive login (if not authenticated)
/opt/homebrew/bin/gh auth login
```

---

## 2. Repositories & Search

```bash
# Search repositories (returns: full_name (stars★): description)
/opt/homebrew/bin/gh search repos "<query>" --limit 5 --json fullName,description,stargazersCount,updatedAt --jq '.[] | "\(.fullName) (\(.stargazersCount)★): \(.description)"'

# View repository overview (visibility, license, default branch, stars)
# NOTE: the visibility field is `visibility` (values PUBLIC/PRIVATE) — `isPublic` is NOT a valid field.
# licenseInfo is null when no license is detected — projection must be null-safe.
/opt/homebrew/bin/gh repo view <owner/repo> --json name,description,visibility,stargazerCount,forkCount,licenseInfo,defaultBranchRef --jq '{name: .name, desc: .description, visibility: .visibility, stars: .stargazerCount, forks: .forkCount, license: (.licenseInfo.spdxId // "none"), branch: .defaultBranchRef.name}'

# Pre-push visibility double-check (declare the intended visibility before pushing)
/opt/homebrew/bin/gh repo view <owner>/<repo> --json visibility,fullName --jq '"\(.fullName) is \(.visibility)"'

# Search code across GitHub without downloading repos
/opt/homebrew/bin/gh search code "<query>" --repo <owner/repo> --limit 5 --json path,repository --jq '.[] | "\(.path)"'
```

---

## 3. Issues Triage & Extraction

```bash
# List open issues with labels (1-line per issue)
/opt/homebrew/bin/gh issue list --repo <owner/repo> --state open --limit 10 --json number,title,labels,updatedAt --jq '.[] | "#\(.number) [\(.labels | map(.name) | join(","))]: \(.title)"'

# Inspect issue body and comments count
/opt/homebrew/bin/gh issue view <issue-number> --repo <owner/repo> --json number,title,state,author,body,comments --jq '{number: .number, title: .title, state: .state, author: .author.login, body: .body, comments_count: (.comments | length)}'

# Create issue (Requires explicit user confirmation before execution)
/opt/homebrew/bin/gh issue create --repo <owner/repo> --title "<title>" --body "<body>"
```

---

## 4. Pull Requests & Code Review

```bash
# List active PRs with draft & review status
/opt/homebrew/bin/gh pr list --repo <owner/repo> --state open --limit 10 --json number,title,author,isDraft,reviewDecision --jq '.[] | "#\(.number) \(.title) (by @\(.author.login)) [review: \(.reviewDecision // "PENDING")] [draft: \(.isDraft)]"'

# Inspect PR metadata and changed files list (Prevents dumping full diff)
/opt/homebrew/bin/gh pr view <pr-number> --repo <owner/repo> --json number,title,state,author,additions,deletions,files --jq '{pr: .number, title: .title, author: .author.login, delta: "+\(.additions)/-\(.deletions)", files: [.files[].path]}'

# View PR checks status
/opt/homebrew/bin/gh pr checks <pr-number> --repo <owner/repo>
```

---

## 5. GitHub Actions & CI/CD Debugging

```bash
# List recent workflow runs (status, conclusion, branch, id)
/opt/homebrew/bin/gh run list --repo <owner/repo> --limit 5 --json databaseId,status,conclusion,name,headBranch --jq '.[] | "[\(.conclusion // .status)] #\(.databaseId) \(.name) (\(.headBranch))"'

# Extract ONLY failing step logs (Zero-token wasted on successful steps)
/opt/homebrew/bin/gh run view <run-id> --repo <owner/repo> --log-failed

# Rerun failed jobs
/opt/homebrew/bin/gh run rerun <run-id> --repo <owner/repo> --failed
```

---

## 6. Releases & Tags

```bash
# List recent releases
/opt/homebrew/bin/gh release list --repo <owner/repo> --limit 5

# View latest release notes (project WITHOUT body by default — notes can be huge;
# add .body to the projection only when the full text is actually needed)
/opt/homebrew/bin/gh release view --repo <owner/repo> --json tagName,name,publishedAt --jq '{tag: .tagName, name: .name, date: .publishedAt}'

# Create a release (write operation — explicit user confirmation required;
# notes always via --notes-file, never inline in argv)
/opt/homebrew/bin/gh release create <tag> --repo <owner/repo> --target main --title "<title>" --notes-file <notes.md>

# Inspect where a release tag points (pre-consumption check before any re-target)
/opt/homebrew/bin/gh api repos/<owner>/<repo>/git/refs/tags/<tag> --jq '.object.sha'
```

*Tag discipline:* force-move a release tag only before its first consumption and disclose it; a consumed tag is immutable — cut a new one.

---

## 7. Commits & Tree (Ground Truth)

```bash
# Recent commits (sha, date, neutral author, subject) — history audit
/opt/homebrew/bin/gh api "repos/<owner>/<repo>/commits?per_page=5" --jq '.[] | "\(.sha[0:7]) \(.commit.author.date) \(.commit.author.name) <\(.commit.author.email)> \(.commit.message | split("\n")[0])"'

# Full tree of the default branch (file inventory, privacy spot-checks)
/opt/homebrew/bin/gh api "repos/<owner>/<repo>/git/trees/main?recursive=1" --jq '{total: (.tree | length), top: [.tree[] | select(.path | split("/") | length == 1) | .path]}'

# Check whether a string is already public in the default branch (immutable-history rule)
/opt/homebrew/bin/gh search code "<string>" --repo <owner>/<repo> --limit 3 --json path --jq '.[] | .path'
```

---

## 8. Large Repositories (Partial Clone)

```bash
# Blobless clone for read/analysis work (full git objects on demand)
git clone --filter=blob:none https://github.com/<owner>/<repo>.git <dir>

# NEVER use shallow clones (--depth) for a push: the push needs full history
```

---

## 9. Stale PR Modernization (MODERNIZE / REWORK / CLOSE)

Deterministic triage for open PRs whose base has moved (gstack `/modernize` pattern).
Decision matrix, in order:
1. **CLOSE** — superseded by a merged PR or a new approach; the work is obsolete.
2. **MODERNIZE** — the change is still valid; only a rebase onto the new base is needed.
3. **REWORK** — base evolution invalidated the change's semantics; a rebase cannot fix it.

```bash
# 0. Triage: state, last activity, mergeability, review status
/opt/homebrew/bin/gh pr view <n> --repo <owner/repo> --json number,title,updatedAt,isDraft,mergeable,reviewDecision --jq '{pr: .number, title: .title, updated: .updatedAt, draft: .isDraft, mergeable: .mergeable, review: .reviewDecision // "PENDING"}'

# 1. MODERNIZE: checkout, rebase, PROOF, lease-push (write ops — user confirmation)
/opt/homebrew/bin/gh pr checkout <n> --repo <owner/repo>
git fetch origin main
OLD_HEAD=$(git rev-parse HEAD)
OLD_BASE=$(git merge-base HEAD origin/main)
git rebase origin/main
# range-diff proof: old commit range vs new commit range must be semantically identical
git range-diff "$OLD_BASE..$OLD_HEAD" "$(git merge-base HEAD origin/main)..HEAD"
# every commit line shows "=" (identical patch); a "!" with hunks changed BEYOND
# conflict resolution = STOP and review manually
git push --force-with-lease origin HEAD   # lease: fails if the remote branch moved

# 2. REWORK: new branch from main, port the intent, link the old PR
git checkout -b rework/pr-<n>-<slug> origin/main
# ...port the change...
/opt/homebrew/bin/gh pr create --repo <owner/repo> --title "<title>" --body "Supersedes #<n>: <what changed semantically>"

# 3. CLOSE: explanatory comment FIRST, then close (write ops — user confirmation)
/opt/homebrew/bin/gh pr comment <n> --repo <owner/repo> --body "Closing: <reason> (superseded by #<new-pr> / main@<sha>)"
/opt/homebrew/bin/gh pr close <n> --repo <owner/repo>
```

*Invariants:* bare `git push --force` on a PR branch is forbidden (`--force-with-lease` only); every MODERNIZE presents the range-diff proof + commit list as the approval artifact before pushing; every CLOSE leaves an explanatory comment (no silent closes); the decision (MODERNIZE/REWORK/CLOSE) is recorded in the cycle report.

---
[[Vault|← Vault]]
