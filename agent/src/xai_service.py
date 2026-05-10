from __future__ import annotations

import json
import os
import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.providers.llm import build_llm

logger = logging.getLogger(__name__)

class XAICitation(BaseModel):
    metric: str
    before: float
    after: float
    delta: float

class XAIResponse(BaseModel):
    rationale: str
    citations: List[XAICitation]
    confidence: str = "high"  # "high", "medium", "low"

class XAIService:
    def __init__(self, runs_dir: str):
        self.runs_dir = runs_dir

    def _load_data(self, job_id: str) -> Optional[Dict[str, Any]]:
        job_dir = os.path.join(self.runs_dir, job_id)
        optimized_file = os.path.join(job_dir, "optimized_params.json")

        if not os.path.exists(optimized_file):
            return None

        try:
            with open(optimized_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read optimization data: {e}")
            return None

    def get_explanation(self, job_id: str) -> Optional[XAIResponse]:
        """
        Generate a natural language explanation for strategy modifications.
        Fallback to template-based if LLM is unavailable.
        """
        data = self._load_data(job_id)
        if not data:
            return None

        # 1. Extract Metrics for Citations
        target = data.get("optimization_target", "sharpe")
        before = data.get("baseline_score", 0.0)
        after = data.get("best_score", 0.0)
        improvement = data.get("improvement_pct", 0.0)

        citations = [
            XAICitation(
                metric=target.capitalize(),
                before=round(before, 4),
                after=round(after, 4),
                delta=round(improvement, 2)
            )
        ]

        # 2. Template-based Rationale (Fallback)
        best_params = data.get("best_params", {})
        baseline_params = {
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "ma_period": 50,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10
        }

        changes = []
        for key, val in best_params.items():
            base_val = baseline_params.get(key)
            if base_val is not None and val != base_val:
                diff = "increased" if val > base_val else "decreased"
                changes.append(f"{key.replace('_', ' ')} was {diff} to {val}")

        rationale = f"Strategy performance improved by {round(improvement, 2)}%."
        if changes:
            rationale += " Key modifications include: " + ", ".join(changes) + "."
        else:
            rationale += " No significant parameter changes were found."

        return XAIResponse(
            rationale=rationale,
            citations=citations,
            confidence="high"
        )

    def _hallucination_guard(self, rationale: str, data: Dict[str, Any]) -> str:
        """
        Verify that all numbers in the rationale exist in the source data.
        Handles percentages (0.05 -> 4) and minor rounding.
        """
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", rationale)
        
        # Flatten source data
        source_values = set()
        source_values.add(round(data.get("improvement_pct", 0.0), 2))
        source_values.add(round(data.get("best_score", 0.0), 4))
        source_values.add(round(data.get("baseline_score", 0.0), 4))
        
        for p in data.get("best_params", {}).values():
            val = float(p)
            source_values.add(val)
            # Add percentage variants (e.g. 0.04 -> 4)
            if 0 < val < 1:
                source_values.add(round(val * 100, 2))
                source_values.add(int(val * 100))

        mismatch = False
        for n in numbers:
            try:
                num_val = float(n)
                # Check if this number is "close enough" to any source value
                if not any(abs(num_val - sv) < 0.001 for sv in source_values):
                    logger.warning(f"XAI Guard: Potential hallucination detected. Value {n} not in source context.")
                    mismatch = True
            except ValueError:
                continue
                
        return "low" if mismatch else "high"

    async def generate_with_llm(self, job_id: str) -> Optional[XAIResponse]:
        """
        Rich explanation using LLM with Hallucination Guard.
        """
        data = self._load_data(job_id)
        if not data:
            return None

        try:
            llm = build_llm()
            prompt = f"""
            You are a Financial Quantitative Analyst. Explain the reasoning behind these strategy parameter optimizations.
            
            Optimization Data:
            - Target Metric: {data.get('optimization_target')}
            - Performance Improvement: {data.get('improvement_pct')}%
            - Final {data.get('optimization_target')}: {data.get('best_score')} (Baseline: {data.get('baseline_score')})
            - Optimized Parameters: {json.dumps(data.get('best_params'))}
            
            Instructions:
            1. Write a professional, concise explanation (2-3 sentences) of WHY these changes help.
            2. Mention specific numbers (improvement %, parameter values).
            3. Do NOT invent data. If you don't know the impact of a specific parameter, don't guess.
            
            Example: "By reducing the RSI period to 10 and increasing the Moving Average to 100, the strategy captures shorter-term momentum while filtering noise, resulting in a 54.17% improvement in the Sharpe ratio."
            """
            
            response = await llm.ainvoke(prompt)
            rationale = response.content.strip()
            
            # Run Guard
            confidence = self._hallucination_guard(rationale, data)
            
            # Get base citations
            base_xai = self.get_explanation(job_id)
            
            return XAIResponse(
                rationale=rationale,
                citations=base_xai.citations if base_xai else [],
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"LLM XAI failed: {e}. Falling back to template.")
            return self.get_explanation(job_id)
