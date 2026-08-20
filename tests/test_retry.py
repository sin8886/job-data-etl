import pytest

from pipeline import retry as retry_module


def test_retry_returns_result_after_transient_failures(monkeypatch):

    calls = []
    delays = []

    def flaky_function():
        calls.append("attempt")
        if len(calls) < 3:
            raise RuntimeError("temporary failure")
        return "loaded"

    monkeypatch.setattr(retry_module.time, "sleep", delays.append)

    result = retry_module.retry(flaky_function, max_retries=3, base_delay=2)

    assert result == "loaded"
    assert len(calls) == 3
    assert delays == [2, 4]


def test_retry_raises_final_exception_after_all_attempts(monkeypatch):

    calls = []
    delays = []

    def always_fails():
        calls.append("attempt")
        raise ValueError("database unavailable")

    monkeypatch.setattr(retry_module.time, "sleep", delays.append)

    with pytest.raises(ValueError, match="database unavailable"):
        retry_module.retry(always_fails, max_retries=2, base_delay=1)

    assert len(calls) == 3
    assert delays == [1, 2]
