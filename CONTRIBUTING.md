# Contributing

Thanks for improving `action-pin-guard`.

## Development Setup

Use a local clone:

```bash
git clone https://github.com/your-org/action-pin-guard.git
cd action-pin-guard
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Workflow

1. Write or update behavior tests first.
2. Run the narrowest relevant pytest target and confirm the expected failure.
3. Implement the smallest change that makes the tests pass.
4. Run `pytest`, `ruff check .`, and `python -m build`.
5. Keep commit messages in Conventional Commit style when practical.

Use English for code comments, commit messages, and issue discussion in this
repository.

## Scope

The project is intentionally local and read-only. Changes should not add network
calls, workflow execution, automatic edits, or marketplace metadata checks
without a design discussion first.
