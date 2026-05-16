# action-pin-guard

[English](README.md) | [中文](README-zh.md) | [日本語](README-ja.md)


`action-pin-guard` is a read-only local CLI for inventorying `uses:` references in
GitHub Actions workflows. It highlights third-party actions that are not pinned
to immutable 40-character commit SHAs.

The scanner parses workflow YAML as data. It does not execute workflows, resolve
remote tags, call GitHub APIs, or edit files.

## Problem and Motivation

Mutable action refs such as tags and branches can change after a workflow has
already been reviewed. Pinning third-party actions to full commit SHAs improves
reproducibility and makes supply-chain reviews easier. `action-pin-guard` gives
maintainers a small local check that can be used before enabling stricter CI
policy.

## Features

- Scans `.github/workflows` by default.
- Reports file, line, job, step, owner, repository, ref, and classification.
- Classifies references as `pinned-sha`, `tag`, `branch-or-other`,
  `local-action`, `docker-action`, or `reusable-workflow`.
- Returns exit code `1` for unpinned external actions unless `--warn-only` is
  used.
- Supports stable JSON output for CI processing.
- Can emit GitHub Actions warning annotations for policy violations while
  keeping JSON on stdout parseable.
- Allows local actions by default and supports owner allowlists.
- Supports optional JSON or TOML config files for shared policy.

## Local Setup

This project is not published to a package registry. Use it from a local clone.

```bash
git clone https://github.com/codecat-ai/action-pin-guard.git
cd action-pin-guard
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the CLI from the clone:

```bash
action-pin-guard check
```

You can also run it as a module:

```bash
python -m action_pin_guard check .github/workflows
```

## Usage

Scan the default workflow directory:

```bash
action-pin-guard check
```

Scan specific files or directories:

```bash
action-pin-guard check .github/workflows/ci.yml examples/
```

Write JSON:

```bash
action-pin-guard check --json
```

Report without failing CI:

```bash
action-pin-guard check --warn-only
```

Allow actions from an internal owner:

```bash
action-pin-guard check --allow-owner my-org
```

Fail on Docker action references:

```bash
action-pin-guard check --deny-docker
```

Read shared policy from a config file:

```bash
action-pin-guard check --config .action-pin-guard.json
```

Emit GitHub Actions warning annotations to stderr:

```bash
action-pin-guard check --github-annotations
```

Keep JSON parseable on stdout while adding CI annotations:

```bash
action-pin-guard check --json --github-annotations
```

## Configuration

- `--allow-owner OWNER` lets internal or already-reviewed action owners pass
  without a full SHA pin.
- `--warn-only` keeps the command advisory while teams migrate existing
  workflows.
- `--deny-docker` treats `docker://` action references as violations.
- `--config FILE` reads shared policy from a `.json` or `.toml` file.
- `--github-annotations` writes one GitHub Actions `::warning` line to stderr
  for each policy violation only. Pinned SHA refs, allowed owners, allowed local
  actions, and allowed Docker refs are not annotated; Docker refs are annotated
  when combined with `--deny-docker`.

Example `.action-pin-guard.json`:

```json
{
  "allow_owners": ["my-org", "trusted-actions"],
  "deny_docker": true,
  "warn_only": false
}
```

Example `.action-pin-guard.toml`:

```toml
allow_owners = ["my-org", "trusted-actions"]
deny_docker = true
warn_only = false
```

Supported keys are `allow_owners`, `deny_docker`, and `warn_only`. JSON is
always supported. TOML is supported when Python 3.11's `tomllib` is available.
File extensions select the parser, so config files must end in `.json` or
`.toml`.

CLI flags take precedence over config values when provided. `--allow-owner`
combines with `allow_owners` from the config instead of replacing it.

## GitHub Actions Example

Use from a source checkout inside the workflow:

```yaml
steps:
  - uses: actions/checkout@v4
  - run: python -m pip install -e ".[dev]"
  - run: action-pin-guard check --github-annotations
```

## Roadmap

- Baseline reports to help teams track migration progress over time.
- More detailed remediation hints.
- SARIF output for CI integrations.

## Contributing

Issues and small pull requests are welcome. Please keep the scanner read-only,
write behavior tests before implementation changes, and run the development
checks below. This project is maintained with AI assistance, but changes are
verified with tests and CI before merging.

## Development

```bash
pytest
ruff check .
ruff format --check .
python -m build
```

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
