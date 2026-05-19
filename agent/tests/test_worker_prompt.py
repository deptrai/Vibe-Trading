from __future__ import annotations

import pytest

from src.swarm.models import SwarmAgentSpec
from src.swarm.worker import build_worker_prompt


def _spec() -> SwarmAgentSpec:
    return SwarmAgentSpec(
        id="dummy",
        role="research analyst",
        system_prompt="Analyze the asset.",
    )


@pytest.mark.unit
def test_worker_prompt_includes_critical_claude_guardrails() -> None:
    prompt = build_worker_prompt(_spec(), {}, "(no matching skills)")
    assert "every response in iterations 0..N-1 MUST include at least one tool call" in prompt
    assert "Do NOT submit a plan-only response" in prompt
    assert "If `bash` tool is unavailable" in prompt
