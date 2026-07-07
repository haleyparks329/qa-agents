from qa_agents.gap_detector import (
    changed_files,
    coverage_files_with_missing_lines,
    detect_gaps,
    main,
    surviving_mutations,
)

__all__ = [
    "changed_files",
    "coverage_files_with_missing_lines",
    "detect_gaps",
    "main",
    "surviving_mutations",
]


if __name__ == "__main__":
    raise SystemExit(main())
