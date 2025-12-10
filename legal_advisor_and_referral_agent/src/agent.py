from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .intents import ModeName
from .flows import (
    run_explain_flow,
    run_draft_flow,
    run_referral_flow,
)


class LegalAdvisorAgent:

    def __init__(self) -> None:

        pass

    @staticmethod
    def handle_request(
        self,
        request_payload: Dict[str, Any],
    ) -> Tuple[ModeName, str]:

        query = request_payload.get("query", "") or ""
        if not query.strip():
            raise ValueError("Missing 'query' in payload")

        law_context: str = request_payload.get("law_context", "") or ""


        providers_raw = request_payload.get("providers") or []
        providers: List[Dict[str, Any]] = list(providers_raw)

        extra_notes: Optional[str] = request_payload.get("extra_notes")

        explain_text = run_explain_flow(
            question=query,
            law_context=law_context,
            extra_notes=extra_notes,
        )

        referral_text = run_referral_flow(
            user_situation=query,
            providers=providers,
            extra_notes=extra_notes,
        )

        draft_text = run_draft_flow(
            request_description=query,
            law_context=law_context,
            extra_notes=extra_notes,
        )

        full_answer = (
            "## Explanation\n\n"
            + explain_text.strip()
            + "\n\n---\n\n"
            + "## Referral\n\n"
            + referral_text.strip()
            + "\n\n---\n\n"
            + "## Draft\n\n"
            + draft_text.strip()
        )

        mode_used: ModeName = "pipeline"

        return mode_used, full_answer
