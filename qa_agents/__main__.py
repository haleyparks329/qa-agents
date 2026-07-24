from __future__ import annotations

import sys

from .cli import main as planner_main
from .demo_export import main as export_demo_main
from .investigate import main as investigate_main
from .public_export import main as export_public_main
from .run import main as run_main


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "investigate":
        return investigate_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        return run_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] == "export-demo":
        return export_demo_main(sys.argv[2:])
    if len(sys.argv) > 1 and sys.argv[1] in {"review", "export-public"}:
        return export_public_main(sys.argv[2:])
    return planner_main()


if __name__ == "__main__":
    raise SystemExit(main())
