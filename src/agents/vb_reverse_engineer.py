"""
VB.NET Reverse Engineering Agent.

Single responsibility:
- Reverse engineer VB.NET source code
- Extract architecture and design information
- Produce structured analysis for documentation and refactoring
"""

import json
from typing import Any, Dict, Optional

from src.core import Agent, CostOptimizedModelRouter, get_prompt_manager


class VBReverseEngineeringAgent(Agent):
    """
    Analyzes VB.NET code and produces a structured reverse‑engineering report.

    This agent is intentionally generic so it can be reused across
    different workflows (CLI, web UI, AgentCore orchestrators, etc.).
    """

    def __init__(self, prompt_version: str = "1.0.0"):
        # Use complex reasoning profile for deep code analysis
        primary, fallback, breaker, config = CostOptimizedModelRouter.get_providers_for_task(
            "complex_reasoning"
        )

        # Guardrails are disabled here because input is source code, which
        # often contains tokens that look like PII but are not real data.
        super().__init__(
            name="vb_reverse_engineer",
            primary_provider=primary,
            fallback_provider=fallback,
            circuit_breaker=breaker,
            guardrail_id=None,
        )

        self.config = config
        self.prompt_version = prompt_version
        self.prompt_manager = get_prompt_manager()

    def process(
        self,
        user_message: str,
        correlation_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Reverse‑engineer VB.NET code and return a structured analysis.

        Expected inputs (flexible):
        - user_message: natural language instructions and/or inline VB.NET code
        - context.vb_code / context.code: raw VB.NET source (preferred)
        - context.analysis_goal: optional extra guidance (e.g. "focus on data access layer")

        Returns a dict with (at minimum):
        - success: bool
        - high_level_summary: str
        - modules: list
        - classes: list
        - external_dependencies: list
        - risks: list
        - refactoring_opportunities: list
        """
        is_valid, error = self.validate_input(user_message)
        if not is_valid:
            return {
                "success": False,
                "error": error,
            }

        system_prompt = self.prompt_manager.load_prompt(
            "vb_reverse_engineer",
            self.prompt_version,
        )

        vb_code = ""
        analysis_goal = None

        if context:
            # Prefer explicitly provided code
            if isinstance(context.get("vb_code"), str):
                vb_code = context["vb_code"]
            elif isinstance(context.get("code"), str):
                vb_code = context["code"]

            if isinstance(context.get("analysis_goal"), str):
                analysis_goal = context["analysis_goal"]

        # If no separate code was provided, assume the message carries the code
        if not vb_code:
            vb_code = user_message

        # If the message is separate from the code, treat it as the goal
        if not analysis_goal and vb_code != user_message:
            analysis_goal = user_message

        if not analysis_goal:
            analysis_goal = (
                "Reverse engineer this VB.NET codebase. "
                "Describe its architecture, responsibilities, and risks."
            )

        # Wrap everything into a single JSON payload for the LLM
        payload = {
            "language": "VB.NET",
            "code": vb_code,
            "analysis_goal": analysis_goal,
            "correlation_id": correlation_id,
        }

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": json.dumps(payload),
                    }
                ],
            }
        ]

        response = self.invoke_llm(
            messages=messages,
            system_prompt=system_prompt,
            temperature=self.config["temperature"],
            max_tokens=self.config["max_tokens"],
        )

        raw_content = response.get("content", "").strip()

        # Strip optional markdown code fences if the model returns them
        if raw_content.startswith("```"):
            # Remove leading ```json / ``` line
            if "\n" in raw_content:
                raw_content = raw_content.split("\n", 1)[1]
            # Remove trailing ``` if present
            if "```" in raw_content:
                raw_content = raw_content.rsplit("```", 1)[0]
            raw_content = raw_content.strip()

        try:
            analysis = json.loads(raw_content)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Failed to parse JSON analysis from LLM response.",
                "raw_response": response.get("content", ""),
            }

        # Enrich with runtime metadata
        analysis["success"] = bool(analysis.get("success", True))
        analysis["model"] = response.get("model")

        usage = response.get("usage")
        if isinstance(usage, dict):
            analysis["cost"] = self.calculate_cost(usage)

        return analysis

