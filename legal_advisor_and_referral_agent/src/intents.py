from __future__ import annotations

from typing import Literal, Optional


ModeName = Literal["pipeline", "explain", "draft", "referral"]


def classify_intent(
    user_query: str,
    preferred_mode: Optional[ModeName] = None,
) -> ModeName:

    if preferred_mode is not None:
        return preferred_mode

    text = user_query.lower()

    draft_keywords = [
        "draft", "write", "redraft", "rewrite", "clause", "contract", "agreement",
        "letter", "email", "template", "add a clause", "modify the clause",
        "edit this clause", "edit this contract",
    ]

    if any(kw in text for kw in draft_keywords):
        return "draft"

    referral_keywords = [
        "lawyer", "attorney", "law firm", "legal firm", "legal provider",
        "recommend a lawyer", "find a lawyer", "hire a lawyer", "legal help",
        "legal services", "which law firm",
    ]

    if any(kw in text for kw in referral_keywords):
        return "referral"

    return "pipeline"
