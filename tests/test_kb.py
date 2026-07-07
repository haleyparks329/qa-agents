from qa_agents.kb import connect, list_open_gaps, migrate, record_gap, route_gaps, stats


def test_kb_records_and_routes_gap(tmp_path):
    conn = connect(tmp_path / "qa.db")
    migrate(conn)

    record_gap("missing_unit_test", "app/example.py", "changed Python file", conn)
    routed = route_gaps(conn)

    assert routed[0]["recommended_agent"] == "quill"
    assert routed[0]["route_reason"] == "test authoring gap"
    assert len(list_open_gaps(conn)) == 1
    assert any(line.startswith("gap_records:") for line in stats(conn))
