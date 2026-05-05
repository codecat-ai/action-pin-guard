# Clean-room brief: action-pin-guard

Decision report:
- community need: 8/10 — GitHub Actions workflows are common and supply-chain reproducibility/security pain around mutable action refs is recurring.
- originality: 7/10 — focus on a small local CLI that inventories action refs with explicit policy, JSON output, and allowlists for internal actions.
- implementation feasibility: 8/10 — static YAML parsing and deterministic diagnostics are suitable for a one-run MVP.
- maintenance cost: 7/10 — small Python package, few dependencies.
- testing feasibility: 9/10 — fixtures can exercise pinned SHA, tag, branch, Docker, and local actions.
- documentation clarity: 8/10 — simple clone/local usage because no package registry publication.
- legal/security/platform risk: low — read-only local file scanner; does not execute workflow content.

Target users: maintainers who want a lightweight pre-commit/CI check for GitHub Actions `uses:` references.
Problem: Workflow files often use mutable tags or branch refs. Maintainers want to see which actions are pinned to immutable commit SHAs and optionally fail CI when third-party actions are not pinned.
Non-goals: resolving remote tags, contacting GitHub APIs, auto-editing workflows, executing workflow steps, checking marketplace metadata.
MVP features:
- Python CLI `action-pin-guard check [PATH...]` scanning `.github/workflows` by default.
- Parse YAML safely as data; never execute content.
- Report each action `uses:` reference with file, line, job, step name/index, owner/repo/ref, classification.
- Classifications: `pinned-sha`, `tag`, `branch-or-other`, `local-action`, `docker-action`, `reusable-workflow`.
- Exit code 1 when unpinned external actions are found unless `--warn-only` is set.
- Options: `--json`, `--allow-owner OWNER` (treat owner actions as allowed), `--allow-local`, `--deny-docker`.
- README docs in English, Chinese, Japanese; MIT license; GitHub Actions CI with Python 3.11/3.12, ruff, pytest, build.
Test scenarios:
- detects tag action as unpinned and returns nonzero.
- accepts 40-char SHA refs.
- ignores local actions when allow-local default is true.
- JSON output is stable and includes counts.
- reusable workflow references are classified.
File structure: src/action_pin_guard/, tests/, pyproject.toml, README*.md, LICENSE, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, .github templates and CI.
