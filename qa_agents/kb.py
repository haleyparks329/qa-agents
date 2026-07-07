from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = PROJECT_ROOT / "schema"
DEFAULT_KB_PATH = Path.home() / ".agents-state" / "qa.db"


def kb_path() -> Path:
    return Path(os.getenv("QA_KB_PATH", str(DEFAULT_KB_PATH))).expanduser()


def connect(path: Path | None = None) -> sqlite3.Connection:
    resolved = path or kb_path()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(conn: sqlite3.Connection | None = None) -> None:
    close = conn is None
    conn = conn or connect()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)")
        applied = {row["name"] for row in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(SCHEMA_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            sql = path.read_text(encoding="utf-8")
            try:
                conn.executescript(sql)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
            conn.execute("INSERT OR IGNORE INTO schema_migrations(name) VALUES (?)", (path.name,))
        conn.commit()
    finally:
        if close:
            conn.close()


def record_gap(
    gap_type: str,
    path: str,
    detail: str = "",
    conn: sqlite3.Connection | None = None,
) -> int:
    close = conn is None
    conn = conn or connect()
    try:
        migrate(conn)
        conn.execute(
            """
            INSERT OR IGNORE INTO gap_records(gap_type, path, detail)
            VALUES (?, ?, ?)
            """,
            (gap_type, path, detail),
        )
        row = conn.execute(
            """
            SELECT id FROM gap_records
            WHERE gap_type = ? AND path = ? AND detail = ? AND status = 'open'
            """,
            (gap_type, path, detail),
        ).fetchone()
        conn.commit()
        return int(row["id"])
    finally:
        if close:
            conn.close()


def list_open_gaps(conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    close = conn is None
    conn = conn or connect()
    try:
        migrate(conn)
        return list(
            conn.execute(
                """
                SELECT id, gap_type, path, detail, status, recommended_agent, route_reason
                FROM gap_records
                WHERE status = 'open'
                ORDER BY created_at, id
                """
            )
        )
    finally:
        if close:
            conn.close()


def route_gap_type(gap_type: str) -> tuple[str, str]:
    if gap_type in {"missing_unit_test", "surviving_mutant"}:
        return "quill", "test authoring gap"
    if gap_type in {"test_drift", "coverage_gap"}:
        return "auditor", "coverage or drift review"
    if gap_type in {"playwright_failure", "selector_rot"}:
        return "mender", "browser test repair"
    return "herbie", "needs QA scoping"


def route_gaps(conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    close = conn is None
    conn = conn or connect()
    try:
        migrate(conn)
        for gap in list_open_gaps(conn):
            agent, reason = route_gap_type(str(gap["gap_type"]))
            conn.execute(
                """
                UPDATE gap_records
                SET recommended_agent = ?, route_reason = ?
                WHERE id = ?
                """,
                (agent, reason, gap["id"]),
            )
        conn.commit()
        return list_open_gaps(conn)
    finally:
        if close:
            conn.close()


def stats(conn: sqlite3.Connection | None = None) -> list[str]:
    close = conn is None
    conn = conn or connect()
    try:
        migrate(conn)
        lines = ["agent_runs:"]
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM agent_runs GROUP BY status"):
            lines.append(f"- {row['status']}: {row['count']}")
        lines.append("observations:")
        for row in conn.execute("SELECT kind, COUNT(*) AS count FROM observations GROUP BY kind"):
            lines.append(f"- {row['kind']}: {row['count']}")
        lines.append("gap_records:")
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM gap_records GROUP BY status"):
            lines.append(f"- {row['status']}: {row['count']}")
        return lines
    finally:
        if close:
            conn.close()


def query_surface(surface: str, conn: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
    close = conn is None
    conn = conn or connect()
    try:
        migrate(conn)
        queries = {
            "gaps": "SELECT * FROM gap_records WHERE status = 'open' ORDER BY created_at, id",
            "handoff-debt": "SELECT * FROM observations WHERE kind = 'handoff_debt' ORDER BY created_at DESC",
            "abstentions": "SELECT * FROM observations WHERE kind = 'abstained' ORDER BY created_at DESC",
            "blocks": "SELECT * FROM observations WHERE kind = 'blocked' ORDER BY created_at DESC",
            "pending-patches": "SELECT * FROM patches WHERE status = 'pending' ORDER BY created_at DESC",
            "recurrences": "SELECT error_fingerprint, COUNT(*) AS count FROM bugs WHERE error_fingerprint IS NOT NULL GROUP BY error_fingerprint HAVING COUNT(*) > 1",
        }
        if surface not in queries:
            raise ValueError(f"Unknown query surface: {surface}")
        return list(conn.execute(queries[surface]))
    finally:
        if close:
            conn.close()


def format_rows(rows: Iterable[sqlite3.Row]) -> str:
    rows = list(rows)
    if not rows:
        return "No records."
    return "\n".join(dict(row).__repr__() for row in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the local QA agents SQLite knowledge base.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("migrate")
    subparsers.add_parser("stats")
    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("surface")
    subparsers.add_parser("route-gaps")
    args = parser.parse_args(argv)

    if args.command == "migrate":
        migrate()
        print(f"migrated {kb_path()}")
    elif args.command == "stats":
        print("\n".join(stats()))
    elif args.command == "query":
        print(format_rows(query_surface(args.surface)))
    elif args.command == "route-gaps":
        print(format_rows(route_gaps()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
