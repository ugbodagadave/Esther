import os
import json
import logging
from typing import Optional, Dict, Any, List

try:
    # Lazy import dependency; only constructed when enabled
    from src.nlp import NLPClient
except Exception:  # pragma: no cover - tests will inject a mock client
    NLPClient = None  # type: ignore

logger = logging.getLogger(__name__)


class FailureAdvisor:
    """LLM-powered advisor that turns structured error context into friendly guidance.

    The advisor is strictly best-effort and only runs when ERROR_ADVISOR_ENABLED=true.
    It never controls application flow; it only returns a user-facing summary and actions.
    """

    def __init__(self, nlp_client: Optional[object] = None, model_type: str = "flash") -> None:
        self._nlp_client = nlp_client
        self._model_type = model_type

    @property
    def enabled(self) -> bool:
        return str(os.getenv("ERROR_ADVISOR_ENABLED", "false")).lower() == "true"

    def _get_nlp(self):
        if self._nlp_client is not None:
            return self._nlp_client
        if NLPClient is None:
            # Dependency not available; act as disabled
            raise RuntimeError("NLPClient unavailable")
        self._nlp_client = NLPClient()
        return self._nlp_client

    def _build_prompt(self, error_context: Dict[str, Any]) -> str:
        """Construct a precise role-based prompt for the LLM."""
        allowed_actions = [
            "Retry", "Help", "Settings", "Wait", "Cancel", "Swap"
        ]
        context_json = json.dumps(error_context, ensure_ascii=False)
        prompt = (
            "You are 'FailureAdvisor', a concise assistant for a crypto trading bot.\n"
            "Input: strictly structured, non-sensitive error context (JSON).\n"
            "Task: 1) Diagnose the likely user-facing issue, 2) Provide ONE friendly sentence addressing the user in second person,"
            " 3) Suggest 2-3 single-word action labels chosen from this set: "
            f"{allowed_actions}.\n"
            "Rules:\n"
            "- Do NOT include stack traces or internal identifiers beyond what is in the context.\n"
            "- Keep the sentence non-technical and helpful.\n"
            "- Only output a JSON object with keys 'message' (string) and 'actions' (array of 2-3 Title Case strings).\n"
            "- No code fences. No commentary.\n"
            f"Context: {context_json}\n"
        )
        return prompt

    def _parse_response_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response text into {message, actions}. Robust to minor formatting issues."""
        try:
            cleaned = text.strip()
            # Strip common code fencing
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`")
                # In case 'json' language tag present, drop potential leading tag residue
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:].lstrip()
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            message = data.get("message")
            actions = data.get("actions")
            if not isinstance(message, str):
                return None
            if not isinstance(actions, list):
                return None
            normalized: List[str] = []
            for a in actions:
                if isinstance(a, str) and a.strip():
                    title = a.strip().title()
                    if title not in normalized:
                        normalized.append(title)
            if len(normalized) == 0:
                return None
            # Keep at most 3 actions
            return {"message": message.strip(), "actions": normalized[:3]}
        except Exception as e:
            logger.warning("FailureAdvisor: could not parse LLM response: %s", e)
            return None

    def summarize(self, error_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return a best-effort actionable summary for the given error context or None on any failure."""
        if not self.enabled:
            return None
        try:
            prompt = self._build_prompt(error_context)
            nlp = self._get_nlp()
            # Prefer Flash for speed/cost
            model = getattr(nlp, "flash_model") if self._model_type == "flash" else getattr(nlp, "pro_model")
            response = model.generate_content(prompt)
            text = getattr(response, "text", "") or ""
            if not text:
                # Some SDK variants expose parts; try to reconstruct
                parts = getattr(response, "parts", None)
                if parts:
                    text = "\n".join(str(p) for p in parts if p)
            parsed = self._parse_response_text(text)
            return parsed
        except Exception as e:  # Never let advisor failures affect UX
            logger.info("FailureAdvisor disabled due to runtime error: %s", e)
            return None 