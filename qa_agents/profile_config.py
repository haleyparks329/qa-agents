from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .profiles import DEFAULT_PROFILES_DIR, ProfileError, available_profiles, profile_json_path


DEFAULT_PROFILE = "ecommerce"
PROFILE_ENV_VARS = ("QA_AGENTS_PROFILE", "QA_PROFILE")


def active_profile_name(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for env_var in PROFILE_ENV_VARS:
        value = os.getenv(env_var)
        if value:
            return value
    return DEFAULT_PROFILE


def load_profile_data(name: str | None = None, profiles_dir: Path = DEFAULT_PROFILES_DIR) -> dict[str, Any]:
    resolved_name = active_profile_name(name)
    path = profile_json_path(resolved_name, profiles_dir)
    if not path.exists():
        known = ", ".join(available_profiles(profiles_dir)) or "none"
        raise ProfileError(f"Unknown profile '{resolved_name}'. Available profiles: {known}.")
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("name", resolved_name)
    return data


def validate_profile_data(data: dict[str, Any]) -> list[str]:
    required = [
        "name",
        "app_description",
        "key_user_flows",
        "risk_areas",
        "test_priorities",
        "constraints",
    ]
    return [field for field in required if field not in data]


def get_dotted(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise ProfileError(f"Profile path not found: {dotted_path}")
    return current


def resolve_profile_path(data: dict[str, Any], dotted_path: str) -> str:
    value = get_dotted(data, dotted_path)
    if not isinstance(value, str):
        raise ProfileError(f"Profile path is not a string: {dotted_path}")
    root = Path(str(data.get("repo_root", "."))).expanduser()
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else root / path)


def agent_context(agent: str, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent": agent,
        "profile": data.get("name"),
        "app_description": data.get("app_description"),
        "key_user_flows": data.get("key_user_flows", []),
        "risk_areas": data.get("risk_areas", []),
        "test_priorities": data.get("test_priorities", []),
        "constraints": data.get("constraints", []),
        "repo": {
            "name": data.get("repo_name", data.get("name")),
            "root": data.get("repo_root", "."),
        },
        "test_layout": data.get("test_layout", {}),
        "tools": data.get("tools", {}),
        "issue_tracker": data.get("issue_tracker", {}),
    }
