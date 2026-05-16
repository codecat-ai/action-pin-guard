from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_KEYS = frozenset({"allow_owners", "deny_docker", "warn_only"})


@dataclass(frozen=True)
class PolicyConfig:
    allow_owners: list[str] = field(default_factory=list)
    deny_docker: bool | None = None
    warn_only: bool | None = None


class ConfigError(ValueError):
    pass


def load_policy_config(path: Path) -> PolicyConfig:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc

    suffix = path.suffix.lower()
    if suffix == ".json":
        data = _parse_json(raw, path)
    elif suffix == ".toml":
        data = _parse_toml(raw, path)
    else:
        raise ConfigError(
            f"unsupported config extension for {path}: expected .json or .toml"
        )

    return validate_policy_config(data)


def validate_policy_config(data: Any) -> PolicyConfig:
    if not isinstance(data, dict):
        raise ConfigError("config must be an object")

    unknown_keys = sorted(set(data) - SUPPORTED_KEYS)
    if unknown_keys:
        names = ", ".join(unknown_keys)
        raise ConfigError(f"unknown config key: {names}")

    allow_owners = data.get("allow_owners", [])
    if not isinstance(allow_owners, list) or not all(
        isinstance(owner, str) for owner in allow_owners
    ):
        raise ConfigError("allow_owners must be a list of strings")

    deny_docker = _optional_bool(data, "deny_docker")
    warn_only = _optional_bool(data, "warn_only")
    return PolicyConfig(
        allow_owners=allow_owners,
        deny_docker=deny_docker,
        warn_only=warn_only,
    )


def _parse_json(raw: str, path: Path) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON config {path}: {exc.msg}") from exc


def _parse_toml(raw: str, path: Path) -> Any:
    try:
        import tomllib
    except ModuleNotFoundError as exc:
        raise ConfigError("TOML config requires Python 3.11 tomllib") from exc

    try:
        return tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML config {path}: {exc}") from exc


def _optional_bool(data: dict[str, Any], key: str) -> bool | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, bool):
        raise ConfigError(f"{key} must be a boolean")
    return value
