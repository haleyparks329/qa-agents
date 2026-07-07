import json

from qa_agents.gap_detector import (
    coverage_files_with_missing_lines,
    detect_gaps,
    surviving_mutations,
)


def test_detects_missing_unit_gap_from_changed_python_without_coverage():
    gaps = detect_gaps(["app/service.py", "README.md"])

    assert gaps == [
        (
            "missing_unit_test",
            "app/service.py",
            "changed Python file should be reviewed for unit coverage",
        )
    ]


def test_detects_coverage_and_mutation_gaps(tmp_path):
    coverage = tmp_path / "coverage.json"
    coverage.write_text(
        json.dumps({"files": {"app/service.py": {"missing_lines": [10]}}}),
        encoding="utf-8",
    )
    mutation = tmp_path / "mutations.json"
    mutation.write_text(
        json.dumps({"mutations": [{"file": "app/service.py", "status": "survived"}]}),
        encoding="utf-8",
    )

    gaps = detect_gaps(["app/service.py"], coverage, mutation)

    assert ("missing_unit_test", "app/service.py", "changed Python file has uncovered lines") in gaps
    assert ("surviving_mutant", "app/service.py", "mutation survived deterministic test run") in gaps
    assert coverage_files_with_missing_lines(coverage) == {"app/service.py"}
    assert surviving_mutations(mutation)[0]["status"] == "survived"
