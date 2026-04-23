import os
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_client():
    """Build a fully-wired mock Anthropic client for managed agents."""
    mock_client = MagicMock()

    mock_agent = MagicMock()
    mock_agent.id = "agent-test-123"
    mock_agent.version = 1
    mock_client.beta.agents.create.return_value = mock_agent

    mock_env = MagicMock()
    mock_env.id = "env-test-456"
    mock_client.beta.environments.create.return_value = mock_env

    mock_session = MagicMock()
    mock_session.id = "session-test-789"
    mock_client.beta.sessions.create.return_value = mock_session

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    # __enter__ returns a list so `for event in stream` iterates over [idle_event]
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    return mock_client


# ---------------------------------------------------------------------------
# run_path_b
# ---------------------------------------------------------------------------

def test_run_path_b_night2_calls_agents_create_with_opus():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    mock_client.beta.agents.create.assert_called_once()
    call_kwargs = mock_client.beta.agents.create.call_args
    assert call_kwargs.kwargs.get("model") == "claude-opus-4-7" or (
        len(call_kwargs.args) > 1 and call_kwargs.args[1] == "claude-opus-4-7"
    ), "agents.create must be called with model='claude-opus-4-7'"


def test_run_path_b_night2_calls_sessions_create():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.create.assert_called_once()


def test_run_path_b_night2_uses_stream_as_context_manager():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.stream.assert_called_once()
    stream_ctx = mock_client.beta.sessions.events.stream.return_value
    stream_ctx.__enter__.assert_called_once()
    stream_ctx.__exit__.assert_called_once()


def test_run_path_b_night2_calls_events_send():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.send.assert_called_once()
    send_call = mock_client.beta.sessions.events.send.call_args
    events_arg = send_call.kwargs.get("events") or send_call.args[1]
    assert events_arg[0]["type"] == "user.message"


def test_run_path_b_returns_expected_shape():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    assert "session_id" in result
    assert "agent_id" in result
    assert "output" in result
    assert result["status"] in ("completed", "error")


def test_run_path_b_stream_opened_before_send():
    """Verify stream is called (opened) before events.send is called."""
    call_order: list[str] = []
    mock_client = _make_mock_client()

    # Capture the pre-configured context manager before overriding side_effect,
    # so the tracking wrapper returns it directly (no recursive mock call).
    stream_ctx = mock_client.beta.sessions.events.stream.return_value

    def tracking_stream(*args, **kwargs):
        call_order.append("stream")
        return stream_ctx

    mock_client.beta.sessions.events.stream.side_effect = tracking_stream
    mock_client.beta.sessions.events.send.side_effect = (
        lambda *a, **kw: call_order.append("send")
    )

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    assert "stream" in call_order and "send" in call_order, (
        f"Expected both 'stream' and 'send' in call_order, got: {call_order}"
    )
    assert call_order.index("stream") < call_order.index("send")


# ---------------------------------------------------------------------------
# run_path_a
# ---------------------------------------------------------------------------

def test_run_path_a_raises_not_implemented_without_waitlist_env(monkeypatch):
    monkeypatch.delenv("MANAGED_AGENTS_WAITLIST", raising=False)
    with patch("theory_copilot.managed_agent_runner.anthropic"):
        from theory_copilot import managed_agent_runner
        with pytest.raises(NotImplementedError, match="callable_agents requires waitlist approval"):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_raises_when_waitlist_not_approved(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "pending")
    with patch("theory_copilot.managed_agent_runner.anthropic"):
        from theory_copilot import managed_agent_runner
        with pytest.raises(NotImplementedError):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_returns_without_error_when_approved(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "approved")

    mock_client = _make_mock_client()
    # run_path_a creates 3 agents and 3 sessions; return distinct mocks to keep it clean
    agent_ids = ["agent-proposer", "agent-searcher", "agent-falsifier"]
    session_ids = ["session-p", "session-s", "session-f"]

    agent_mocks = []
    for aid in agent_ids:
        m = MagicMock()
        m.id = aid
        agent_mocks.append(m)
    mock_client.beta.agents.create.side_effect = agent_mocks

    session_mocks = []
    for sid in session_ids:
        m = MagicMock()
        m.id = sid
        session_mocks.append(m)
    mock_client.beta.sessions.create.side_effect = session_mocks

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_a(night=2)

    assert isinstance(result, dict)
    assert "session_id" in result
    assert "agent_id" in result
    assert result["status"] in ("completed", "error")


def test_run_path_a_approved_creates_three_agents(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "approved")

    mock_client = _make_mock_client()
    agent_mocks = []
    for i in range(3):
        m = MagicMock()
        m.id = f"agent-{i}"
        agent_mocks.append(m)
    mock_client.beta.agents.create.side_effect = agent_mocks

    session_mocks = []
    for i in range(3):
        m = MagicMock()
        m.id = f"session-{i}"
        session_mocks.append(m)
    mock_client.beta.sessions.create.side_effect = session_mocks

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_a(night=2)

    assert mock_client.beta.agents.create.call_count == 3
    models_used = [
        c.kwargs.get("model") for c in mock_client.beta.agents.create.call_args_list
    ]
    assert "claude-opus-4-7" in models_used
    assert "claude-sonnet-4-6" in models_used


# ---------------------------------------------------------------------------
# run_path_c_routine
# ---------------------------------------------------------------------------

def test_run_path_c_routine_rejects_invalid_night():
    from theory_copilot import managed_agent_runner
    with pytest.raises(ValueError):
        managed_agent_runner.run_path_c_routine(night=1)


def test_run_path_c_routine_runs_once_when_interval_zero(tmp_path):
    from theory_copilot import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": "s-1", "agent_id": "a-1", "output": "ok", "status": "completed"}

    log = tmp_path / "verdicts.jsonl"
    result = managed_agent_runner.run_path_c_routine(
        night=3,
        interval_seconds=0,
        max_iterations=0,
        log_path=str(log),
        invoke_fn=fake_invoke,
    )
    assert calls == [3]
    assert result["iteration_count"] == 1
    assert log.exists()
    entries = [__import__("json").loads(line) for line in log.read_text().splitlines()]
    assert entries[0]["night"] == 3
    assert entries[0]["status"] == "completed"


def test_run_path_c_routine_respects_max_iterations(tmp_path):
    from theory_copilot import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": f"s-{len(calls)}", "status": "completed", "output": ""}

    def fake_sleep(seconds):
        # no-op — we only care about iteration count
        return None

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=fake_sleep,
    )
    assert result["iteration_count"] == 3
    assert len(calls) == 3


def test_run_path_c_routine_watch_dir_skips_when_unchanged(tmp_path):
    from theory_copilot import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": "s", "status": "completed", "output": ""}

    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "data.csv").write_text("sample_id,label\ns1,1\n")

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        watch_dir=str(watch),
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=lambda _s: None,
    )
    # Baseline iteration runs; subsequent iterations see unchanged fingerprint
    assert len(calls) == 1
    assert result["iteration_count"] == 3
    # Verify at least one skip entry in the log
    entries = [__import__("json").loads(line) for line in (tmp_path / "v.jsonl").read_text().splitlines()]
    skipped = [e for e in entries if e["status"] == "skipped_no_change"]
    assert len(skipped) == 2


def test_run_path_c_routine_watch_dir_triggers_on_change(tmp_path):
    from theory_copilot import managed_agent_runner
    calls = []
    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "data.csv").write_text("sample_id,label\ns1,1\n")

    def fake_invoke(night):
        calls.append(night)
        # mutate watched dir on every invocation → next iter sees a change
        (watch / f"new_{len(calls)}.csv").write_text(f"row{len(calls)}")
        return {"session_id": "s", "status": "completed", "output": ""}

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        watch_dir=str(watch),
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=lambda _s: None,
    )
    # Every iteration triggers because fingerprint changes each time
    assert len(calls) == 3


def test_run_path_c_routine_log_path_is_jsonl_appendable(tmp_path):
    from theory_copilot import managed_agent_runner
    log = tmp_path / "a" / "b" / "verdicts.jsonl"

    def fake_invoke(night):
        return {"session_id": "s", "status": "completed", "output": "x" * 42}

    managed_agent_runner.run_path_c_routine(
        night=4,
        interval_seconds=0,
        log_path=str(log),
        invoke_fn=fake_invoke,
    )
    # Parent directories created; file is JSONL
    assert log.exists()
    line = log.read_text().strip()
    parsed = __import__("json").loads(line)
    assert parsed["night"] == 4
    assert parsed["output_chars"] == 42
