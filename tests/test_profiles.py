from qa_agents.profiles import available_profiles, load_profile


def test_loads_ecommerce_profile():
    profile = load_profile("ecommerce")

    assert profile.name == "ecommerce"
    assert profile.key_user_flows
    assert "simulated" in " ".join(profile.constraints).lower()


def test_lists_profiles():
    assert {"ecommerce", "saas_dashboard"}.issubset(set(available_profiles()))
