from __future__ import annotations

import argparse
import json
import sys

from qa_agents.profile_config import (
    agent_context,
    get_dotted,
    load_profile_data,
    resolve_profile_path,
    validate_profile_data,
)
from qa_agents.profiles import ProfileError, available_profiles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect generic QA agent profiles.")
    parser.add_argument("--profile", help="Profile name. Defaults to QA_AGENTS_PROFILE, QA_PROFILE, or ecommerce.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    subparsers.add_parser("show")
    subparsers.add_parser("summary")
    subparsers.add_parser("validate")
    subparsers.add_parser("repo-root")
    subparsers.add_parser("repo-name")
    subparsers.add_parser("tracker")
    paths_parser = subparsers.add_parser("paths")
    paths_parser.add_argument("keys", nargs="*")
    tool_parser = subparsers.add_parser("tool")
    tool_parser.add_argument("name")
    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("path")
    resolve_parser = subparsers.add_parser("resolve-path")
    resolve_parser.add_argument("path")
    context_parser = subparsers.add_parser("agent-context")
    context_parser.add_argument("agent")
    subparsers.add_parser("ticket-prefixes")

    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            print("\n".join(available_profiles()))
            return 0

        data = load_profile_data(args.profile)

        if args.command == "show":
            print(json.dumps(data, indent=2, sort_keys=True))
        elif args.command == "summary":
            print(f"{data['name']}: {data['app_description']}")
        elif args.command == "validate":
            missing = validate_profile_data(data)
            if missing:
                print(f"missing fields: {', '.join(missing)}", file=sys.stderr)
                return 1
            print(f"{data['name']} is valid")
        elif args.command == "repo-root":
            print(data.get("repo_root", "."))
        elif args.command == "repo-name":
            print(data.get("repo_name", data.get("name")))
        elif args.command == "tracker":
            print(json.dumps(data.get("issue_tracker", {}), sort_keys=True))
        elif args.command == "ticket-prefixes":
            prefixes = data.get("issue_tracker", {}).get("ticket_prefixes", [])
            print("\n".join(prefixes))
        elif args.command == "paths":
            layout = data.get("test_layout", {})
            if args.keys:
                print(json.dumps({key: layout.get(key) for key in args.keys}, sort_keys=True))
            else:
                print(json.dumps(layout, indent=2, sort_keys=True))
        elif args.command == "tool":
            print(json.dumps(data.get("tools", {}).get(args.name), sort_keys=True))
        elif args.command == "get":
            print(json.dumps(get_dotted(data, args.path), sort_keys=True))
        elif args.command == "resolve-path":
            print(resolve_profile_path(data, args.path))
        elif args.command == "agent-context":
            print(json.dumps(agent_context(args.agent, data), indent=2, sort_keys=True))
    except (OSError, ProfileError, KeyError) as exc:
        print(f"profile.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
