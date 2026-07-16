from qa_agents.strategies import available_strategies, load_strategy


def test_loads_meticulous_strategy():
    strategy = load_strategy("meticulous")

    assert strategy.id == "meticulous"
    assert strategy.quality_model == "replay_first"
    assert "not an official Meticulous integration" in strategy.disclaimer
    assert "meticulous" in available_strategies()
