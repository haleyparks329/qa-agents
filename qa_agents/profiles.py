from __future__ import annotations

import json
from pathlib import Path

from .models import QAProfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILES_DIR = PROJECT_ROOT / "profiles"


class ProfileError(ValueError):
    """Raised when a QA profile cannot be loaded or validated."""


def available_profiles(profiles_dir: Path = DEFAULT_PROFILES_DIR) -> list[str]:
    if not profiles_dir.exists():
        return []
    return sorted(path.stem for path in profiles_dir.glob("*.json"))


def load_profile(name: str, profiles_dir: Path = DEFAULT_PROFILES_DIR) -> QAProfile:
    profile_path = profiles_dir / f"{name}.json"
    if not profile_path.exists():
        known = ", ".join(available_profiles(profiles_dir)) or "none"
        raise ProfileError(f"Unknown profile '{name}'. Available profiles: {known}.")

    data = json.loads(profile_path.read_text(encoding="utf-8"))
    required_fields = {
        "name",
        "app_description",
        "key_user_flows",
        "risk_areas",
        "test_priorities",
        "constraints",
    }
    missing = sorted(required_fields - set(data))
    if missing:
        raise ProfileError(f"Profile '{name}' is missing fields: {', '.join(missing)}.")

    return QAProfile(
        name=str(data["name"]),
        app_description=str(data["app_description"]),
        key_user_flows=_string_list(data["key_user_flows"], "key_user_flows"),
        risk_areas=_string_list(data["risk_areas"], "risk_areas"),
        test_priorities=_string_list(data["test_priorities"], "test_priorities"),
        constraints=_string_list(data["constraints"], "constraints"),
    )


def _string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProfileError(f"Profile field '{field_name}' must be a list of strings.")
    return value
