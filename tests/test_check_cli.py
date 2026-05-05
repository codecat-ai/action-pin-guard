import json

from action_pin_guard.cli import main


def write_workflow(path, text):
    workflow_dir = path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci.yml"
    workflow.write_text(text, encoding="utf-8")
    return workflow


def test_tag_action_is_unpinned_and_returns_nonzero(tmp_path, capsys):
    workflow = write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
""",
    )

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert str(workflow) in output
    assert "actions/checkout@v4" in output
    assert "tag" in output
    assert "unpinned external action" in output


def test_40_character_sha_ref_is_accepted(tmp_path, capsys):
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@0123456789abcdef0123456789abcdef01234567
""",
    )

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "pinned-sha" in output
    assert "No unpinned external actions found." in output


def test_local_actions_are_allowed_by_default(tmp_path, capsys):
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Local action
        uses: ./.github/actions/build
""",
    )

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "local-action" in output


def test_json_output_is_stable_and_includes_counts(tmp_path, capsys):
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Pinned
        uses: actions/cache@0123456789abcdef0123456789abcdef01234567
      - name: Tag
        uses: actions/checkout@v4
      - name: Local
        uses: ./tools/action
      - name: Docker
        uses: docker://alpine:3.20
""",
    )

    exit_code = main(["check", "--json", str(tmp_path)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert list(payload) == ["summary", "findings"]
    assert payload["summary"] == {
        "total": 4,
        "pinned_sha": 1,
        "tag": 1,
        "branch_or_other": 0,
        "local_action": 1,
        "docker_action": 1,
        "reusable_workflow": 0,
        "unpinned_external": 1,
    }
    assert [finding["uses"] for finding in payload["findings"]] == [
        "actions/cache@0123456789abcdef0123456789abcdef01234567",
        "actions/checkout@v4",
        "./tools/action",
        "docker://alpine:3.20",
    ]


def test_reusable_workflow_references_are_classified(tmp_path, capsys):
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  call:
    uses: octo-org/shared/.github/workflows/reuse.yml@main
""",
    )

    exit_code = main(["check", "--json", "--warn-only", str(tmp_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"][0]["classification"] == "reusable-workflow"
    assert payload["findings"][0]["job"] == "call"
