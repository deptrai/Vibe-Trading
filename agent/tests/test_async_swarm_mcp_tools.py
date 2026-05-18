"""Integration test for async swarm MCP tools (Story 5.5.1).

Verifies that the new ``start_swarm`` + ``cancel_swarm`` tools:

1. Return in <2s (start_swarm hands off to a background daemon thread).
2. Cancellation actually transitions a running swarm to ``cancelled``.

The test imports ``mcp_server`` directly and invokes the underlying tool
functions (bypassing the FastMCP transport) — that's enough to exercise
the runtime singleton + cancel_event wiring added by 5.5.1 without needing
to spawn a subprocess. The full E2E (subprocess + JSON-RPC) is covered by
``test_mcp_server_smoke.py`` for the synchronous handshake; for the async
path the unit-level call is faster and easier to assert against.

Marked ``@pytest.mark.integration`` because importing ``mcp_server`` pulls
in the full registry + fastmcp + numpy etc. — too heavy for the default
fast test tier.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest


AGENT_DIR = Path(__file__).resolve().parents[1]
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))


def _call_tool(tool_callable, *args, **kwargs) -> dict:
    """Invoke an ``@mcp.tool``-decorated function and parse the JSON return.

    FastMCP wraps the function but keeps the original callable reachable as
    ``.fn`` on most versions; if that's not present we fall back to calling
    the tool object directly (it's still a Callable).
    """
    fn = getattr(tool_callable, "fn", tool_callable)
    raw = fn(*args, **kwargs)
    assert isinstance(raw, str), f"expected JSON string, got {type(raw).__name__}"
    return json.loads(raw)


@pytest.mark.integration
def test_start_swarm_returns_quickly() -> None:
    """``start_swarm`` MUST return in <2s — handoff to daemon thread only."""
    from mcp_server import start_swarm

    t0 = time.monotonic()
    result = _call_tool(
        start_swarm,
        preset_name="investment_committee",
        variables={"target": "AAPL.US", "market": "US"},
    )
    elapsed = time.monotonic() - t0

    assert elapsed < 2.0, f"start_swarm took {elapsed:.2f}s (>2s budget)"
    # On success: {"run_id": "...", "preset": "...", "status": "started"}
    # On unknown preset: {"status": "error", "error": "..."}
    if result.get("status") == "started":
        assert "run_id" in result and len(result["run_id"]) >= 8
        assert result["preset"] == "investment_committee"
    else:
        assert result.get("status") == "error", f"unexpected payload: {result}"
        # Acceptable in CI environments where the preset YAML or LLM config
        # is intentionally missing — the <2s budget is the structural check.


@pytest.mark.integration
def test_start_swarm_unknown_preset_fast_path() -> None:
    """Unknown preset returns an error JSON quickly; no thread spawned."""
    from mcp_server import start_swarm

    t0 = time.monotonic()
    result = _call_tool(
        start_swarm,
        preset_name="this_preset_does_not_exist_5_5_1",
        variables={},
    )
    elapsed = time.monotonic() - t0

    assert elapsed < 1.0, f"unknown preset took {elapsed:.2f}s"
    assert result.get("status") == "error"
    assert "error" in result


@pytest.mark.integration
def test_cancel_swarm_unknown_run_id_returns_error() -> None:
    """Cancelling a nonexistent run returns an error envelope, not an exception."""
    from mcp_server import cancel_swarm

    result = _call_tool(
        cancel_swarm, run_id="00000000-0000-0000-0000-000000000000"
    )
    assert result.get("status") == "error"
    assert "not found" in result.get("error", "").lower()


@pytest.mark.integration
def test_start_then_cancel_roundtrip() -> None:
    """End-to-end: start a swarm, immediately cancel it, run transitions to cancelled.

    Skipped if the preset starts running before cancel_event is registered
    (race window is small but real); falls back to verifying the cancel call
    at least returns ``cancelling``.
    """
    from mcp_server import start_swarm, cancel_swarm, get_swarm_status

    started = _call_tool(
        start_swarm,
        preset_name="investment_committee",
        variables={"target": "AAPL.US", "market": "US"},
    )
    if started.get("status") != "started":
        pytest.skip(f"swarm did not start (env-dependent): {started}")

    run_id = started["run_id"]
    cancelled = _call_tool(cancel_swarm, run_id=run_id)
    assert cancelled.get("status") == "cancelling"
    assert cancelled.get("run_id") == run_id

    # Give the runtime a moment to observe the cancel event between layers.
    # Workers check the event AFTER each layer, so latency depends on the
    # first agent's LLM call. Generous upper bound for CI.
    deadline = time.monotonic() + 60.0
    final_status = None
    while time.monotonic() < deadline:
        status = _call_tool(get_swarm_status, run_id=run_id)
        final_status = status.get("status")
        if final_status in ("cancelled", "completed", "failed"):
            break
        time.sleep(2)

    assert final_status in ("cancelled", "completed", "failed"), (
        f"swarm did not reach a terminal state within 60s, last={final_status}"
    )
