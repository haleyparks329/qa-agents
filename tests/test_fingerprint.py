from qa_agents.fingerprint import fingerprint_error, normalize_error


def test_fingerprint_normalizes_line_numbers_and_addresses():
    first = "Error at app.py:12 object 0xABC"
    second = "Error at app.py:99 object 0x123"

    assert normalize_error(first) == "error at app.py:line object 0xaddr"
    assert fingerprint_error(first) == fingerprint_error(second)
