CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_observations_kind ON observations(kind);
CREATE INDEX IF NOT EXISTS idx_gap_records_status ON gap_records(status);
CREATE INDEX IF NOT EXISTS idx_bugs_error_fingerprint ON bugs(error_fingerprint);
