# action-pin-guard

[English](README.md) | [中文](README-zh.md) | [日本語](README-jp.md)


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
- Allows local actions by default and supports owner allowlists.

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

## Configuration

- `--allow-owner OWNER` lets internal or already-reviewed action owners pass
  without a full SHA pin.
- `--warn-only` keeps the command advisory while teams migrate existing
  workflows.
- `--deny-docker` treats `docker://` action references as violations.

## Roadmap

- Optional config file for shared policy.
- More detailed remediation hints.
- SARIF or annotations output for CI integrations.

## Contributing

Issues and small pull requests are welcome. Please keep the scanner read-only,
write behavior tests before implementation changes, and run the development
checks below. This project is maintained with AI assistance, but changes are
verified with tests and CI before merging.

## Development

```bash
pytest
ruff check .
python -m build
```

## License

This project is released under the MIT License. See [LICENSE](LICENSE).
