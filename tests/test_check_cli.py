import json

import pytest

from action_pin_guard.cli import main


def write_workflow(path, text):
    workflow_dir = path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci.yml"
    workflow.write_text(text, encoding="utf-8")
    return workflow


def write_config(path, name, text):
    config = path / name
    config.write_text(text, encoding="utf-8")
    return config


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


def test_github_annotations_are_emitted_to_stderr_for_violations_only(tmp_path, capsys):
    workflow = write_workflow(
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
      - name: Allowed owner
        uses: actions/checkout@v4
      - name: Violation
        uses: bad-owner/bad-action@main
      - name: Local
        uses: ./tools/action
      - name: Docker
        uses: docker://alpine:3.20
""",
    )

    exit_code = main(
        [
            "check",
            "--github-annotations",
            "--allow-owner",
            "actions",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "bad-owner/bad-action@main" in captured.out
    assert captured.err.splitlines() == [
        (
            f"::warning file={workflow},line=13,"
            "title=Unpinned GitHub Actions reference::"
            "bad-owner/bad-action@main is branch-or-other; pin external actions "
            "to a full 40-character commit SHA or explicitly allow the owner."
        )
    ]


def test_github_annotations_keep_json_parseable_and_escape_workflow_commands(
    tmp_path, capsys
):
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci:unsafe,name%0A.yml"
    workflow.write_text(
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Docker
        uses: docker://registry.example.com/ns/image:1.2%bad
""",
        encoding="utf-8",
    )

    exit_code = main(
        ["check", "--json", "--github-annotations", "--deny-docker", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["summary"]["docker_action"] == 1
    assert captured.err.splitlines() == [
        (
            f"::warning file={tmp_path}/.github/workflows/ci%3Aunsafe%2Cname%250A.yml,"
            "line=9,title=Unpinned GitHub Actions reference::"
            "docker://registry.example.com/ns/image:1.2%25bad is docker-action; "
            "pin external actions to a full 40-character commit SHA or explicitly "
            "allow the owner."
        )
    ]


def test_json_config_applies_shared_policy_to_json_output_and_exit_code(
    tmp_path, capsys
):
    config = write_config(
        tmp_path,
        ".action-pin-guard.json",
        json.dumps(
            {
                "allow_owners": ["actions"],
                "deny_docker": True,
                "warn_only": True,
            }
        ),
    )
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker://alpine:3.20
""",
    )

    exit_code = main(["check", "--json", "--config", str(config), str(tmp_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["tag"] == 1
    assert payload["summary"]["docker_action"] == 1
    assert payload["summary"]["unpinned_external"] == 1


def test_toml_config_is_supported_when_tomllib_is_available(tmp_path, capsys):
    pytest.importorskip("tomllib")
    config = write_config(
        tmp_path,
        ".action-pin-guard.toml",
        """
allow_owners = ["actions"]
warn_only = true
""",
    )
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
      - uses: bad-owner/tool@main
""",
    )

    exit_code = main(["check", "--json", "--config", str(config), str(tmp_path)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["unpinned_external"] == 1


def test_cli_flags_override_config_and_allow_owners_are_combined(tmp_path, capsys):
    config = write_config(
        tmp_path,
        ".action-pin-guard.json",
        json.dumps(
            {
                "allow_owners": ["actions"],
                "deny_docker": False,
                "warn_only": True,
            }
        ),
    )
    write_workflow(
        tmp_path,
        """
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: internal-org/build@main
      - uses: docker://alpine:3.20
""",
    )

    exit_code = main(
        [
            "check",
            "--json",
            "--config",
            str(config),
            "--allow-owner",
            "internal-org",
            "--deny-docker",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["unpinned_external"] == 1


@pytest.mark.parametrize(
    ("name", "contents", "message"),
    [
        (".action-pin-guard.yaml", "warn_only: true", "unsupported config extension"),
        (".action-pin-guard.json", "{", "invalid JSON config"),
        (
            ".action-pin-guard.json",
            json.dumps({"allow_owners": ["actions"], "extra": True}),
            "unknown config key",
        ),
        (
            ".action-pin-guard.json",
            json.dumps({"allow_owners": "actions"}),
            "allow_owners must be a list of strings",
        ),
        (
            ".action-pin-guard.json",
            json.dumps({"deny_docker": "yes"}),
            "deny_docker must be a boolean",
        ),
    ],
)
def test_invalid_config_exits_2_with_clear_stderr(
    tmp_path, capsys, name, contents, message
):
    config = write_config(tmp_path, name, contents)

    with pytest.raises(SystemExit) as exc:
        main(["check", "--config", str(config), str(tmp_path)])

    assert exc.value.code == 2
    assert message in capsys.readouterr().err


def test_missing_config_exits_2_with_clear_stderr(tmp_path, capsys):
    missing_config = tmp_path / ".action-pin-guard.json"

    with pytest.raises(SystemExit) as exc:
        main(["check", "--config", str(missing_config), str(tmp_path)])

    assert exc.value.code == 2
    assert "config file not found" in capsys.readouterr().err


def test_malformed_toml_config_exits_2_with_clear_stderr(tmp_path, capsys):
    pytest.importorskip("tomllib")
    config = write_config(tmp_path, ".action-pin-guard.toml", "warn_only =")

    with pytest.raises(SystemExit) as exc:
        main(["check", "--config", str(config), str(tmp_path)])

    assert exc.value.code == 2
    assert "invalid TOML config" in capsys.readouterr().err
