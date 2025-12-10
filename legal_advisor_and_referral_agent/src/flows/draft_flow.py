from __future__ import annotations

from typing import Optional, Any

from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
    get_mode_config,
)




def build_draft_decider_chain() -> RunnableSerializable[dict, Any]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a decision helper for the LegalAdvisorAgent in DRAFT MODE.\n"
                    "Your only job is to decide whether a concrete written draft "
                    "(such as an email, letter, clause, or simple form) is helpful "
                    "for the user at this stage.\n\n"
                    "Base your decision primarily on the legal context and the extra notes, "
                    "but also consider the user request.\n\n"
                    "Answer exactly one of:\n"
                    "- 'DRAFT'    if a concrete draft document would clearly help the user.\n"
                    "- 'NO_DRAFT' if it is better to NOT produce a draft now "
                    "and the explanation/referral is sufficient.\n\n"
                    "Do not explain your reasoning. Do not output anything else."
                ),
            ),
            (
                "human",
                (
                    "User request:\n{request_description}\n\n"
                    "Legal / contextual information (may be empty):\n{law_context}\n\n"
                    "Extra notes (may be empty):\n{extra_notes}\n\n"
                    "Remember: reply with exactly 'DRAFT' or 'NO_DRAFT'."
                ),
            ),
        ]
    )

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.0,
        max_tokens=8,
    )

    chain: RunnableSerializable[dict, Any] = prompt | llm
    return chain


def decide_should_draft(
    request_description: str,
    law_context: str = "",
    extra_notes: Optional[str] = None,
) -> bool:

    chain = build_draft_decider_chain()

    resp = chain.invoke(
        {
            "request_description": request_description,
            "law_context": law_context or "",
            "extra_notes": extra_notes or "",
        }
    )

    decision = (resp.content or "").strip().upper()
    return decision == "DRAFT"



def build_draft_chain() -> RunnableSerializable[dict, Any]:
    mode = get_mode_config("draft")
    system_prompt = mode.load_system_prompt()
    examples_prompt = mode.load_examples_prompt() or ""

    full_system_prompt = system_prompt
    if examples_prompt:
        full_system_prompt = f"{system_prompt}\n\n### Examples\n\n{examples_prompt}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", full_system_prompt),
            (
                "human",
                (
                    "User request:\n{request_description}\n\n"
                    "Relevant legal / internal context (if any):\n\n{law_context}\n\n"
                    "If there are specific constraints or preferences, follow them."
                ),
            ),
        ]
    )

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    chain = prompt | llm
    return chain


def run_draft_flow(
    request_description: str,
    law_context: str = "",
    extra_notes: Optional[str] = None,
) -> str:
    should_draft = decide_should_draft(
        request_description=request_description,
        law_context=law_context,
        extra_notes=extra_notes,
    )

    if not should_draft:
        return (
            "At this stage, a concrete draft document (email, letter, clause, or form) "
            "does not appear strictly necessary based on your situation and the legal "
            "context provided.\n\n"
            "- You can rely on the explanation and referral above as next steps.\n"
            "- If you explicitly want a template email or document, you can ask for it "
            "in a follow-up (for example: \"Draft an email to my employer explaining X\")."
        )

    chain = build_draft_chain()

    combined_context = law_context
    if extra_notes:
        combined_context = f"{law_context}\n\n[Additional context]\n{extra_notes}"

    resp = chain.invoke(
        {
            "request_description": request_description,
            "law_context": combined_context,
        }
    )

    return resp.content
