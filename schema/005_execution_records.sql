CREATE TABLE IF NOT EXISTS execution_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  command_name TEXT NOT NULL,
  command TEXT NOT NULL,
  cwd TEXT NOT NULL,
  status TEXT NOT NULL,
  exit_code INTEGER,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  duration_ms INTEGER,
  stdout_summary TEXT,
  stderr_summary TEXT,
  artifact_refs_json TEXT NOT NULL DEFAULT '[]',
  report_refs_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (run_id) REFERENCES agent_runs(id)
);
