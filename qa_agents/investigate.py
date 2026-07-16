from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .strategies import StrategyError, available_strategies, run_investigation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qa-agents investigate",
        description="Investigate normalized deterministic replay evidence with a quality strategy.",
    )
    parser.add_argument(
        "--strategy",
        required=True,
        help=f"Quality strategy to use. Available: {', '.join(available_strategies())}",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a normalized replay evidence JSON artifact.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the investigation artifact. Defaults to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        investigation = run_investigation(args.strategy, args.input)
    except (OSError, json.JSONDecodeError, StrategyError) as exc:
        print(f"qa-agents investigate: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(investigation, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0
