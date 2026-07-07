from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import generate_test_plan
from .parser import parse_feature_request
from .profiles import ProfileError, available_profiles, load_profile
from .renderer import render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qa-agents",
        description="Generate a deterministic QA test plan from a simulated feature request.",
    )
    parser.add_argument("feature_request", help="Path to a simulated Markdown feature request.")
    parser.add_argument(
        "--profile",
        required=True,
        help=f"QA profile to use. Available: {', '.join(available_profiles())}",
    )
    parser.add_argument(
        "--stubs",
        action="store_true",
        help="Include Playwright-style test stubs in the generated plan.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the Markdown test plan. Defaults to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        profile = load_profile(args.profile)
        feature = parse_feature_request(args.feature_request)
        plan = generate_test_plan(feature, profile, include_playwright_stubs=args.stubs)
        rendered = render_markdown(plan)
    except (OSError, ValueError, ProfileError) as exc:
        print(f"qa-agents: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0
