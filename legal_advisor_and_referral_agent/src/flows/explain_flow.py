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


def build_explain_chain() -> RunnableSerializable[dict, Any]:
    mode = get_mode_config("explain")
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
                    "Here is the legal context you can use:\n\n"
                    "{law_context}\n\n"
                    "User question:\n{question}"
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


def run_explain_flow(
    question: str,
    law_context: str,
    extra_notes: Optional[str] = None,
) -> str:
    chain = build_explain_chain()

    combined_context = law_context
    if extra_notes:
        combined_context = f"{law_context}\n\n[Additional context]\n{extra_notes}"

    resp = chain.invoke(
        {
            "law_context": combined_context,
            "question": question,
        }
    )

    return resp.content
