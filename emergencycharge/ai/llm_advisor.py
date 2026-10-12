"""
Hybrid AI Advisor: Bridges Offline Expert Rule Engine with Optional LLM (Gemini).
Works 100% offline without any API key, and dynamically utilizes Google Gemini
if an API key is provided by the user.
"""

import logging
import os
from typing import Optional

from emergencycharge.ai.rule_engine import AIAdvisorEngine, AIAnalysisReport

logger = logging.getLogger("emergencycharge.llm")


class HybridAIAdvisor:
    """Provides instant offline analysis with optional LLM augmentation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.rule_engine = AIAdvisorEngine()
        self._llm_client = None
        self._init_llm_if_available()

    def _init_llm_if_available(self):
        if not self.api_key:
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._llm_client = genai.GenerativeModel("gemini-1.5-flash")
            logger.info("Configured optional Google Gemini LLM advisor.")
        except Exception as e:
            logger.debug(f"Optional LLM init skipped: {e}")
            self._llm_client = None

    def update_api_key(self, api_key: str):
        self.api_key = api_key
        self._init_llm_if_available()

    def analyze(self, laptop_info, phone_info, estimate, emergency_mode_active: bool = False) -> AIAnalysisReport:
        # Core structured report always generated deterministically by expert rule engine
        return self.rule_engine.analyze(laptop_info, phone_info, estimate, emergency_mode_active)

    def ask(self, query: str, report: AIAnalysisReport) -> str:
        """Answers user question using optional LLM or rock-solid offline rule engine."""
        if self._llm_client:
            try:
                system_context = (
                    "You are EmergencyCharge AI, an expert systems and electrical hardware engineer. "
                    "Analyze the user's laptop-to-phone emergency charging question based on this context:\n"
                    f"Summary: {report.summary}\n"
                    f"Bottlenecks: {', '.join(report.bottlenecks)}\n"
                    f"Port Advice: {report.port_advice}\n"
                    f"Power Management: {report.power_advice}\n"
                    f"Rule: Never claim software can override USB hardware power limits or modify PCB resistors.\n"
                    "Keep answers crisp, practical, and technically accurate."
                )
                prompt = f"{system_context}\n\nUser Question: {query}"
                resp = self._llm_client.generate_content(prompt)
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"LLM query failed ({e}), falling back to offline rule engine.")

        # Offline fallback
        return self.rule_engine.answer_query(query, report)
