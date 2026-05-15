from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")
TAG_RE = re.compile(r"^v?\d+(?:\.\d+){0,3}(?:[-+][0-9A-Za-z.-]+)?$")
WORKFLOW_SUFFIXES = {".yml", ".yaml"}
BRANCH_NAMES = {"main", "master", "develop", "development", "trunk"}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    job: str
    step_name: str | None
    step_index: int | None
    uses: str
    owner: str | None
    repo: str | None
    ref: str | None
    classification: str

    def to_json(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "job": self.job,
            "step_name": self.step_name,
            "step_index": self.step_index,
            "uses": self.uses,
            "owner": self.owner,
            "repo": self.repo,
            "ref": self.ref,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class Summary:
    total: int
    pinned_sha: int
    tag: int
    branch_or_other: int
    local_action: int
    docker_action: int
    reusable_workflow: int
    unpinned_external: int

    def to_json(self) -> dict[str, int]:
        return {
            "total": self.total,
            "pinned_sha": self.pinned_sha,
            "tag": self.tag,
            "branch_or_other": self.branch_or_other,
            "local_action": self.local_action,
            "docker_action": self.docker_action,
            "reusable_workflow": self.reusable_workflow,
            "unpinned_external": self.unpinned_external,
        }


def scan_paths(paths: Sequence[Path]) -> list[Finding]:
    workflow_files: list[Path] = []
    for path in paths:
        workflow_files.extend(_workflow_files(path))

    findings: list[Finding] = []
    for workflow_file in sorted(dict.fromkeys(workflow_files)):
        findings.extend(scan_workflow(workflow_file))
    return findings


def scan_workflow(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []

    if not text.strip():
        return []

    root = yaml.compose(text)
    if not isinstance(root, yaml.MappingNode):
        return []

    findings: list[Finding] = []
    jobs = _mapping_value(root, "jobs")
    if not isinstance(jobs, yaml.MappingNode):
        return findings

    for job_key, job_node in _mapping_items(jobs):
        job_name = _node_value(job_key)
        if not isinstance(job_name, str) or not isinstance(job_node, yaml.MappingNode):
            continue

        job_uses = _mapping_value(job_node, "uses")
        if isinstance(job_uses, yaml.ScalarNode):
            findings.append(_finding(path, job_uses, job_name, None, None))

        steps = _mapping_value(job_node, "steps")
        if not isinstance(steps, yaml.SequenceNode):
            continue

        for index, step_node in enumerate(steps.value):
            if not isinstance(step_node, yaml.MappingNode):
                continue
            uses_node = _mapping_value(step_node, "uses")
            if not isinstance(uses_node, yaml.ScalarNode):
                continue
            step_name_node = _mapping_value(step_node, "name")
            step_name = (
                str(step_name_node.value)
                if isinstance(step_name_node, yaml.ScalarNode)
                else None
            )
            findings.append(_finding(path, uses_node, job_name, step_name, index))

    return findings


def summarize_findings(
    findings: Sequence[Finding],
    *,
    allow_owners: set[str],
    allow_local: bool,
    deny_docker: bool,
) -> Summary:
    classifications = [finding.classification for finding in findings]
    violations = sum(
        1
        for finding in findings
        if is_policy_violation(
            finding,
            allow_owners=allow_owners,
            allow_local=allow_local,
            deny_docker=deny_docker,
        )
    )
    return Summary(
        total=len(findings),
        pinned_sha=classifications.count("pinned-sha"),
        tag=classifications.count("tag"),
        branch_or_other=classifications.count("branch-or-other"),
        local_action=classifications.count("local-action"),
        docker_action=classifications.count("docker-action"),
        reusable_workflow=classifications.count("reusable-workflow"),
        unpinned_external=violations,
    )


def _workflow_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix in WORKFLOW_SUFFIXES:
            yield path
        return
    if path.is_dir():
        for suffix in WORKFLOW_SUFFIXES:
            yield from path.rglob(f"*{suffix}")


def _finding(
    path: Path,
    uses_node: yaml.ScalarNode,
    job: str,
    step_name: str | None,
    step_index: int | None,
) -> Finding:
    uses = str(uses_node.value)
    owner, repo, ref = _split_action_ref(uses)
    return Finding(
        file=str(path),
        line=uses_node.start_mark.line + 1,
        job=job,
        step_name=step_name,
        step_index=step_index,
        uses=uses,
        owner=owner,
        repo=repo,
        ref=ref,
        classification=_classify(uses, ref),
    )


def _classify(uses: str, ref: str | None) -> str:
    if uses.startswith(("./", "../")):
        return "local-action"
    if uses.startswith("docker://"):
        return "docker-action"
    if "/.github/workflows/" in uses:
        return "reusable-workflow"
    if ref and SHA40_RE.fullmatch(ref):
        return "pinned-sha"
    if ref and _looks_like_tag(ref):
        return "tag"
    return "branch-or-other"


def _looks_like_tag(ref: str) -> bool:
    if ref in BRANCH_NAMES or ref.startswith(("refs/heads/", "heads/")):
        return False
    return bool(TAG_RE.fullmatch(ref))


def _split_action_ref(uses: str) -> tuple[str | None, str | None, str | None]:
    if uses.startswith(("./", "../", "docker://")):
        return None, None, None

    path_part, separator, ref = uses.rpartition("@")
    if not separator:
        path_part = uses
        ref = None

    parts = path_part.split("/")
    owner = parts[0] if len(parts) >= 2 else None
    repo = parts[1] if len(parts) >= 2 else None
    return owner, repo, ref


def is_policy_violation(
    finding: Finding,
    *,
    allow_owners: set[str],
    allow_local: bool,
    deny_docker: bool,
) -> bool:
    if finding.classification == "local-action":
        return not allow_local
    if finding.classification == "docker-action":
        return deny_docker
    if finding.classification == "pinned-sha":
        return False
    return not (finding.owner and finding.owner.lower() in allow_owners)


def _mapping_value(node: yaml.MappingNode, key: str) -> yaml.Node | None:
    for key_node, value_node in node.value:
        if _node_value(key_node) == key:
            return value_node
    return None


def _mapping_items(node: yaml.MappingNode) -> Iterable[tuple[yaml.Node, yaml.Node]]:
    return node.value


def _node_value(node: yaml.Node) -> Any:
    return getattr(node, "value", None)
