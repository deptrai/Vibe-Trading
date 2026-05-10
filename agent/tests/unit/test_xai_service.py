import pytest
import json
import os
import shutil
from unittest.mock import MagicMock, AsyncMock, patch
from src.xai_service import XAIService, XAICitation, XAIResponse

@pytest.fixture
def mock_runs_dir(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    return str(runs_dir)

@pytest.fixture
def xai_service(mock_runs_dir):
    return XAIService(runs_dir=mock_runs_dir)

@pytest.fixture
def sample_optimization_data():
    return {
        "status": "completed",
        "best_params": {
            "rsi_period": 10,
            "macd_fast": 15,
            "stop_loss_pct": 0.04
        },
        "best_score": 1.85,
        "optimization_target": "sharpe",
        "baseline_score": 1.2,
        "improvement_pct": 54.17
    }

def test_hallucination_guard_success(xai_service, sample_optimization_data):
    # Case 1: Perfect match
    rationale = "Improved by 54.17% with RSI 10 and SL 0.04"
    assert xai_service._hallucination_guard(rationale, sample_optimization_data) == "high"

    # Case 2: Percentage conversion (0.04 -> 4)
    rationale = "Performance up 54.17% using a 4% stop loss."
    assert xai_service._hallucination_guard(rationale, sample_optimization_data) == "high"

    # Case 3: Minor rounding
    rationale = "Sharpe ratio is 1.85 (up from 1.2)"
    assert xai_service._hallucination_guard(rationale, sample_optimization_data) == "high"

def test_hallucination_guard_failure(xai_service, sample_optimization_data):
    # Case 1: Invented improvement
    rationale = "Massive 99% improvement detected!"
    assert xai_service._hallucination_guard(rationale, sample_optimization_data) == "low"

    # Case 2: Wrong parameter value
    rationale = "RSI was set to 25"
    assert xai_service._hallucination_guard(rationale, sample_optimization_data) == "low"

def test_get_explanation_template(xai_service, mock_runs_dir, sample_optimization_data):
    job_id = "job123"
    job_dir = os.path.join(mock_runs_dir, job_id)
    os.makedirs(job_dir)
    
    with open(os.path.join(job_dir, "optimized_params.json"), "w") as f:
        json.dump(sample_optimization_data, f)
        
    explanation = xai_service.get_explanation(job_id)
    
    assert explanation is not None
    assert "54.17%" in explanation.rationale
    assert explanation.confidence == "high"
    assert len(explanation.citations) == 1
    assert explanation.citations[0].metric == "Sharpe"
    assert explanation.citations[0].after == 1.85

@pytest.mark.anyio
async def test_generate_with_llm(xai_service, mock_runs_dir, sample_optimization_data):
    job_id = "job_llm"
    job_dir = os.path.join(mock_runs_dir, job_id)
    os.makedirs(job_dir)
    with open(os.path.join(job_dir, "optimized_params.json"), "w") as f:
        json.dump(sample_optimization_data, f)

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Strategic shift to RSI 10 resulted in 54.17% gain."))

    with patch("src.xai_service.build_llm", return_value=mock_llm):
        explanation = await xai_service.generate_with_llm(job_id)
        
        assert explanation.confidence == "high"
        assert "RSI 10" in explanation.rationale
        assert "54.17%" in explanation.rationale

@pytest.mark.anyio
async def test_generate_with_llm_hallucination(xai_service, mock_runs_dir, sample_optimization_data):
    job_id = "job_hallucinate"
    job_dir = os.path.join(mock_runs_dir, job_id)
    os.makedirs(job_dir)
    with open(os.path.join(job_dir, "optimized_params.json"), "w") as f:
        json.dump(sample_optimization_data, f)

    mock_llm = MagicMock()
    # LLM invents a 75% improvement
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Wow! 75% improvement!"))

    with patch("src.xai_service.build_llm", return_value=mock_llm):
        explanation = await xai_service.generate_with_llm(job_id)
        assert explanation.confidence == "low"
