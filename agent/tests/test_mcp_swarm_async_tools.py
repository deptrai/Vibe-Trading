from __future__ import annotations

import json

import mcp_server
from src.swarm.models import RunStatus, SwarmAgentSpec, SwarmRun, SwarmTask, TaskStatus


def _make_run(run_id: str, status: RunStatus, account_id: str | None) -> SwarmRun:
    return SwarmRun(
        id=run_id,
        preset_name="investment_committee",
        account_id=account_id,
        status=status,
        user_vars={"target": "AAPL.US"},
        agents=[SwarmAgentSpec(id="analyst", role="analyst", system_prompt="x")],
        tasks=[
            SwarmTask(
                id="t1",
                agent_id="analyst",
                prompt_template="do work",
                status=TaskStatus.completed if status == RunStatus.completed else TaskStatus.pending,
            )
        ],
        created_at="2026-05-31T00:00:00Z",
        completed_at="2026-05-31T00:05:00Z" if status == RunStatus.completed else None,
        final_report="# report" if status == RunStatus.completed else None,
    )


class _FakeStore:
    def __init__(self, runs: dict[str, SwarmRun]):
        self._runs = runs

    def load_run(self, run_id: str) -> SwarmRun | None:
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 20) -> list[SwarmRun]:
        return list(self._runs.values())[:limit]


def test_start_swarm_returns_started_and_preserves_account_id(monkeypatch) -> None:
    run = _make_run("run-start", RunStatus.pending, "acc-1")

    class FakeStore:
        def __init__(self, base_dir):  # noqa: ANN001
            self.base_dir = base_dir

    class FakeRuntime:
        def __init__(self, store):  # noqa: ANN001
            self.store = store

        def start_run(self, preset_name, variables, account_id=None):  # noqa: ANN001
            assert preset_name == "investment_committee"
            assert variables == {"target": "AAPL.US"}
            assert account_id == "acc-1"
            return run

    import src.swarm.runtime as runtime_module
    import src.swarm.store as store_module

    monkeypatch.setattr(store_module, "SwarmStore", FakeStore)
    monkeypatch.setattr(runtime_module, "SwarmRuntime", FakeRuntime)

    payload = json.loads(
        mcp_server.start_swarm(
            preset_name="investment_committee",
            variables={"target": "AAPL.US"},
            account_id="acc-1",
        )
    )
    assert payload["status"] == "started"
    assert payload["run_id"] == "run-start"


def test_get_swarm_status_enforces_ownership(monkeypatch) -> None:
    run = _make_run("run-own", RunStatus.running, "acc-a")
    store = _FakeStore({run.id: run})
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    denied = json.loads(mcp_server.get_swarm_status(run.id, account_id="acc-b"))
    assert denied["status"] == "error"
    assert "not owned" in denied["error"].lower()

    allowed = json.loads(mcp_server.get_swarm_status(run.id, account_id="acc-a"))
    assert allowed["run_id"] == run.id
    assert allowed["status"] == "running"


def test_list_runs_filters_by_account_id(monkeypatch) -> None:
    run_a = _make_run("run-a", RunStatus.running, "acc-a")
    run_b = _make_run("run-b", RunStatus.running, "acc-b")
    run_legacy = _make_run("run-legacy", RunStatus.running, None)
    store = _FakeStore({run_a.id: run_a, run_b.id: run_b, run_legacy.id: run_legacy})
    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)

    all_runs = json.loads(mcp_server.list_runs(limit=20))
    assert {r["run_id"] for r in all_runs} == {"run-a", "run-b", "run-legacy"}

    scoped_runs = json.loads(mcp_server.list_runs(limit=20, account_id="acc-a"))
    assert [r["run_id"] for r in scoped_runs] == ["run-a"]


def test_cancel_swarm_returns_noop_for_terminal_and_cancelling_for_running(monkeypatch) -> None:
    terminal = _make_run("run-done", RunStatus.completed, "acc-a")
    running = _make_run("run-live", RunStatus.running, "acc-a")
    store = _FakeStore({terminal.id: terminal, running.id: running})

    class FakeRuntime:
        def cancel_run(self, run_id: str) -> bool:
            return run_id == running.id

    monkeypatch.setattr(mcp_server, "_get_swarm_store", lambda: store)
    monkeypatch.setattr(mcp_server, "_get_swarm_runtime", lambda: FakeRuntime())

    noop = json.loads(mcp_server.cancel_swarm(terminal.id, account_id="acc-a"))
    assert noop["status"] == "noop"
    assert noop["run_status"] == "completed"

    cancelling = json.loads(mcp_server.cancel_swarm(running.id, account_id="acc-a"))
    assert cancelling["status"] == "cancelling"
    assert cancelling["run_id"] == running.id
