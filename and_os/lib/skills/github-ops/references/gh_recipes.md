# GitHub CLI (`gh`) Token-Efficient Recipes & Projections

> Reference guide for `github-ops` skill. Provides deterministic, token-efficient command templates using the official GitHub CLI (`gh`) with `--json` and `--jq`.

---

## 1. Authentication & Status

```bash
# Check current authentication status
/opt/homebrew/bin/gh auth status

# Interactive login (if not authenticated)
/opt/homebrew/bin/gh auth login
```

---

## 2. Repositories & Search

```bash
# Search repositories (returns: full_name (stars★): description)
/opt/homebrew/bin/gh search repos "<query>" --limit 5 --json fullName,description,stargazersCount,updatedAt --jq '.[] | "\(.fullName) (\(.stargazersCount)★): \(.description)"'

# View repository overview (description, license, default branch, stars)
/opt/homebrew/bin/gh repo view <owner/repo> --json name,description,stargazerCount,forkCount,licenseInfo,defaultBranchRef --jq '{name: .name, desc: .description, stars: .stargazerCount, forks: .forkCount, license: .licenseInfo.name, branch: .defaultBranchRef.name}'

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

# View latest release notes
/opt/homebrew/bin/gh release view --repo <owner/repo> --json tagName,name,publishedAt,body --jq '{tag: .tagName, name: .name, date: .publishedAt, notes: .body}'
```
