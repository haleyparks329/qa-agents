from __future__ import annotations

import sys

from .cli import main as planner_main
from .run import main as run_main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        raise SystemExit(run_main(sys.argv[2:]))
    raise SystemExit(planner_main())
