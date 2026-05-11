"""Unit tests for AgentLoop core logic."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agent.loop import AgentLoop


class TestAgentLoopCore:
    @pytest.fixture
    def mock_deps(self) -> tuple[MagicMock, MagicMock]:
        registry = MagicMock()
        llm = MagicMock()
        return registry, llm

    def test_loop_initialization(self, mock_deps: tuple[MagicMock, MagicMock]) -> None:
        registry, llm = mock_deps
        loop = AgentLoop(registry, llm)
        assert loop.registry == registry
        assert loop.llm == llm
        assert loop.max_iterations == 50

    @patch("src.agent.loop.RunStateStore")
    @patch("src.agent.loop.TraceWriter")
    @patch("src.agent.loop.ContextBuilder")
    @patch("src.agent.loop.get_background_manager")
    def test_run_single_iteration_answer(
        self,
        mock_bg: MagicMock,
        mock_context_builder_cls: MagicMock,
        mock_trace_writer_cls: MagicMock,
        mock_state_store_cls: MagicMock,
        mock_deps: tuple[MagicMock, MagicMock],
    ) -> None:
        registry, llm = mock_deps
        
        # Setup mocks
        mock_state_store = MagicMock()
        mock_state_store_cls.return_value = mock_state_store
        
        mock_trace_writer = MagicMock()
        mock_trace_writer_cls.return_value = mock_trace_writer
        
        mock_context_builder = MagicMock()
        mock_context_builder_cls.return_value = mock_context_builder
        mock_context_builder.build_messages.return_value = [{"role": "system", "content": "sys"}]
        
        # Mock LLM response: simple text answer
        mock_response = MagicMock()
        mock_response.has_tool_calls = False
        mock_response.content = "I am an AI."
        llm.stream_chat.return_value = mock_response
        
        mock_bg_manager = MagicMock()
        mock_bg_manager.drain_notifications.return_value = []
        mock_bg.return_value = mock_bg_manager

        loop = AgentLoop(registry, llm)
        result = loop.run("Who are you?")

        assert result["status"] == "success"
        assert result["content"] == "I am an AI."
        assert llm.stream_chat.call_count == 1
        mock_state_store.save_request.assert_called_once()
        mock_trace_writer.write.assert_any_call({"type": "answer", "iter": 1, "content": "I am an AI."})

    @patch("src.agent.loop.RunStateStore")
    @patch("src.agent.loop.TraceWriter")
    @patch("src.agent.loop.ContextBuilder")
    @patch("src.agent.loop.get_background_manager")
    def test_run_tool_execution(
        self,
        mock_bg: MagicMock,
        mock_context_builder_cls: MagicMock,
        mock_trace_writer_cls: MagicMock,
        mock_state_store_cls: MagicMock,
        mock_deps: tuple[MagicMock, MagicMock],
    ) -> None:
        registry, llm = mock_deps
        
        mock_context_builder = MagicMock()
        mock_context_builder_cls.return_value = mock_context_builder
        mock_context_builder.build_messages.return_value = [{"role": "system", "content": "sys"}]
        
        # 1st Iteration: Tool Call
        res1 = MagicMock()
        res1.has_tool_calls = True
        tc = MagicMock()
        tc.name = "get_weather"
        tc.id = "call_1"
        tc.arguments = {"city": "Hanoi"}
        res1.tool_calls = [tc]
        
        # 2nd Iteration: Final Answer
        res2 = MagicMock()
        res2.has_tool_calls = False
        res2.content = "It is sunny in Hanoi."
        
        llm.stream_chat.side_effect = [res1, res2]
        
        # Tool execution mock
        registry.execute.return_value = '{"status": "ok", "weather": "sunny"}'
        mock_tool_def = MagicMock()
        mock_tool_def.is_readonly = True
        registry.get.return_value = mock_tool_def

        loop = AgentLoop(registry, llm)
        result = loop.run("What's the weather?")

        assert result["status"] == "success"
        assert result["content"] == "It is sunny in Hanoi."
        assert registry.execute.call_count == 1
        assert llm.stream_chat.call_count == 2

    def test_cancel_loop(self, mock_deps: tuple[MagicMock, MagicMock]) -> None:
        registry, llm = mock_deps
        loop = AgentLoop(registry, llm)
        
        # Trigger cancel during the first iteration via side effect
        def side_effect(*args, **kwargs):
            loop.cancel()
            mock_res = MagicMock()
            mock_res.has_tool_calls = False
            mock_res.content = "Interrupted"
            return mock_res
            
        llm.stream_chat.side_effect = side_effect
        
        with patch("src.agent.loop.RunStateStore"), \
             patch("src.agent.loop.TraceWriter"), \
             patch("src.agent.loop.ContextBuilder"), \
             patch("src.agent.loop.get_background_manager"):
            result = loop.run("task")
            
        assert result["status"] == "cancelled"

    def test_run_headless_success(self, mock_deps: tuple[MagicMock, MagicMock], tmp_path) -> None:
        registry, llm = mock_deps
        loop = AgentLoop(registry, llm)
        
        # Mock run to return success without actually invoking the LLM
        def mock_run(user_message, session_id):
            code_dir = tmp_path / "code"
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "signal_engine.py").write_text("print('hello')")
            return {"status": "success", "run_dir": str(tmp_path), "react_trace": [{"type": "answer", "content": "done"}]}
            
        with patch.object(loop, 'run', side_effect=mock_run) as mock_run_method:
            result = loop.run_headless("Buy high sell low", tmp_path)
            
        mock_run_method.assert_called_once()
        assert result["status"] == "success"
        assert result["run_dir"] == str(tmp_path)
        assert len(result["react_trace"]) == 1

    def test_run_headless_failure(self, mock_deps: tuple[MagicMock, MagicMock], tmp_path) -> None:
        registry, llm = mock_deps
        loop = AgentLoop(registry, llm)
        
        # Mock run, but strategy.py is not created
        def mock_run(user_message, session_id):
            return {"status": "success", "run_dir": str(tmp_path), "react_trace": []}
            
        with patch.object(loop, 'run', side_effect=mock_run) as mock_run_method:
            result = loop.run_headless("Do nothing", tmp_path)
            
        mock_run_method.assert_called_once()
        assert result["status"] == "failed"
        assert "not generated" in result["reason"]
