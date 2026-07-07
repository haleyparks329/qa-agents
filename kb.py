from qa_agents.kb import (
    connect,
    format_rows,
    kb_path,
    list_open_gaps,
    main,
    migrate,
    query_surface,
    record_gap,
    route_gap_type,
    route_gaps,
    stats,
)

__all__ = [
    "connect",
    "format_rows",
    "kb_path",
    "list_open_gaps",
    "main",
    "migrate",
    "query_surface",
    "record_gap",
    "route_gap_type",
    "route_gaps",
    "stats",
]


if __name__ == "__main__":
    raise SystemExit(main())
