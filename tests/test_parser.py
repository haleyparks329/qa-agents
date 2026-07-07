from qa_agents.parser import parse_feature_request


def test_parses_feature_request():
    feature = parse_feature_request("examples/feature_request.md")

    assert feature.title == "Saved Cart Reminder"
    assert "Returning shoppers" in feature.summary
    assert len(feature.requirements) == 4
