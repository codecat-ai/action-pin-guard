from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from action_pin_guard.scanner import (
    Finding,
    is_policy_violation,
    scan_paths,
    summarize_findings,
)

ANNOTATION_TITLE = "Unpinned GitHub Actions reference"
ANNOTATION_GUIDANCE = (
    "pin external actions to a full 40-character commit SHA or explicitly allow "
    "the owner."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="action-pin-guard",
        description="Check GitHub Actions uses: references for immutable pins.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="scan workflow files")
    check.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="workflow files or directories to scan; defaults to .github/workflows",
    )
    check.add_argument("--json", action="store_true", help="write JSON output")
    check.add_argument(
        "--warn-only",
        action="store_true",
        help="report findings without returning a failing exit code",
    )
    check.add_argument(
        "--allow-owner",
        action="append",
        default=[],
        metavar="OWNER",
        help="treat actions owned by OWNER as allowed even when not pinned",
    )
    check.add_argument(
        "--allow-local",
        action="store_true",
        default=True,
        help="allow local action references; enabled by default",
    )
    check.add_argument(
        "--deny-docker",
        action="store_true",
        help="treat docker:// action references as policy violations",
    )
    check.add_argument(
        "--github-annotations",
        action="store_true",
        help="write GitHub Actions warning annotations for policy violations to stderr",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return run_check(args)

    parser.error("unknown command")
    return 2


def run_check(args: argparse.Namespace) -> int:
    findings = scan_paths(args.paths or [Path(".github/workflows")])
    allow_owners = {owner.lower() for owner in args.allow_owner}
    summary = summarize_findings(
        findings,
        allow_owners=allow_owners,
        allow_local=args.allow_local,
        deny_docker=args.deny_docker,
    )

    if args.json:
        payload = {
            "summary": summary.to_json(),
            "findings": [finding.to_json() for finding in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print_human(findings, summary.unpinned_external)

    if args.github_annotations:
        print_github_annotations(
            findings,
            allow_owners=allow_owners,
            allow_local=args.allow_local,
            deny_docker=args.deny_docker,
        )

    if summary.unpinned_external and not args.warn_only:
        return 1
    return 0


def print_human(findings: Sequence[Finding], violations: int) -> None:
    for finding in findings:
        step = finding.step_name or f"step #{finding.step_index}"
        print(
            f"{finding.file}:{finding.line}: {finding.job} / {step}: "
            f"{finding.uses} [{finding.classification}]"
        )

    if not findings:
        print("No action uses references found.")
    elif violations:
        noun = "action" if violations == 1 else "actions"
        print(f"{violations} unpinned external {noun} found.")
    else:
        print("No unpinned external actions found.")


def print_github_annotations(
    findings: Sequence[Finding],
    *,
    allow_owners: set[str],
    allow_local: bool,
    deny_docker: bool,
) -> None:
    for finding in findings:
        if not is_policy_violation(
            finding,
            allow_owners=allow_owners,
            allow_local=allow_local,
            deny_docker=deny_docker,
        ):
            continue

        properties = (
            f"file={_escape_annotation_property(finding.file)},"
            f"line={finding.line},"
            f"title={_escape_annotation_property(ANNOTATION_TITLE)}"
        )
        message = f"{finding.uses} is {finding.classification}; {ANNOTATION_GUIDANCE}"
        print(
            f"::warning {properties}::{_escape_annotation_message(message)}",
            file=sys.stderr,
        )


def _escape_annotation_property(value: object) -> str:
    return _escape_annotation(str(value), escape_colon_and_comma=True)


def _escape_annotation_message(value: object) -> str:
    return _escape_annotation(str(value), escape_colon_and_comma=False)


def _escape_annotation(value: str, *, escape_colon_and_comma: bool) -> str:
    escaped = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if escape_colon_and_comma:
        escaped = escaped.replace(":", "%3A").replace(",", "%2C")
    return escaped


if __name__ == "__main__":
    sys.exit(main())
