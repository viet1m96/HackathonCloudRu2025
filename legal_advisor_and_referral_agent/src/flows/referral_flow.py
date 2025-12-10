from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableSerializable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from ..config import (
    MODEL_NAME,
    TEMPERATURE,
    MAX_TOKENS,
    get_mode_config,
)
from ..mcp_client import (
    SupportMCPError,
    SUPPORT_MCP_TOOLS,
    call_support_tool,
)


def format_providers_for_context(providers: List[Dict[str, Any]]) -> str:
    if not providers:
        return "No provider data was found."

    lines: List[str] = []
    for idx, p in enumerate(providers, start=1):
        name = p.get("name", "Unknown name")
        location = p.get("location", p.get("jurisdiction", "Unknown location"))
        practice_areas = ", ".join(p.get("practice_areas", [])) or "N/A"
        languages = ", ".join(p.get("languages", [])) or "N/A"
        website = p.get("website", "N/A")
        notes = p.get("notes", "")

        lines.append(f"{idx}. {name}")
        lines.append(f"   Location / Jurisdiction: {location}")
        lines.append(f"   Practice areas: {practice_areas}")
        lines.append(f"   Languages: {languages}")
        lines.append(f"   Website: {website}")
        if notes:
            lines.append(f"   Notes: {notes}")
        lines.append("")

    return "\n".join(lines)


AVAILABLE_TOOL_NAMES: List[str] = list(SUPPORT_MCP_TOOLS.keys())
TOOLS_LIST_STR = ", ".join(AVAILABLE_TOOL_NAMES)


def build_referral_decider_chain() -> RunnableSerializable[dict, Any]:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a decision helper for a legal referral agent.\n"
                    "You must decide which external provider-search tools (if any) "
                    "should be called.\n\n"
                    "Available tools (names):\n"
                    f"{TOOLS_LIST_STR}\n\n"
                    "If you think NO external provider search is needed, "
                    "answer exactly 'NO_TOOL'.\n\n"
                    "If you think one or more tools should be called, "
                    "answer with one or more tool names from the list above, "
                    "separated by commas or new lines.\n\n"
                    "Do not explain your reasoning. Do not output anything else."
                ),
            ),
            (
                "human",
                (
                    "User situation:\n{user_situation}\n\n"
                    "Extra notes (may be empty):\n{extra_notes}\n\n"
                    "Remember: reply with exactly either:\n"
                    "- 'NO_TOOL'\n"
                    "or\n"
                    "- one or more tool names from the list, separated by commas or new lines."
                ),
            ),
        ]
    )

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=0.0,
        max_tokens=64,
    )

    chain: RunnableSerializable[dict, Any] = prompt | llm
    return chain


def decide_support_tools(
    user_situation: str,
    extra_notes: Optional[str] = None,
) -> List[str]:
    chain = build_referral_decider_chain()

    resp = chain.invoke(
        {
            "user_situation": user_situation,
            "extra_notes": extra_notes or "",
        }
    )

    raw = (resp.content or "").strip()
    normalized = raw.upper()

    if normalized == "NO_TOOL":
        return []

    candidates: List[str] = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.split(",")]
        for part in parts:
            if part:
                candidates.append(part)

    selected: List[str] = []
    for name in candidates:
        if name in AVAILABLE_TOOL_NAMES and name not in selected:
            selected.append(name)

    return selected



def build_referral_chain() -> RunnableSerializable[dict, Any]:
    mode = get_mode_config("referral")
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
                    "User situation:\n{user_situation}\n\n"
                    "Available providers (if any):\n\n{provider_block}\n\n"
                    "Based on this, explain what type of legal help is appropriate, "
                    "suggest some providers (if available) in a neutral way, "
                    "and give criteria and next steps as described in the system instructions."
                ),
            ),
        ]
    )

    llm = ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    chain: RunnableSerializable[dict, Any] = prompt | llm
    return chain


def run_referral_flow(
    user_situation: str,
    providers: Optional[List[Dict[str, Any]]] = None,
    extra_notes: Optional[str] = None,
) -> str:
    if not providers:
        tool_names = decide_support_tools(
            user_situation=user_situation,
            extra_notes=extra_notes,
        )

        all_providers: List[Dict[str, Any]] = []

        for tool_name in tool_names:
            try:
                result = call_support_tool(
                    tool_name=tool_name,
                    user_situation=user_situation,
                    extra_notes=extra_notes,
                )
                all_providers.extend(result)
            except SupportMCPError:
                continue

        providers = all_providers

    chain = build_referral_chain()

    provider_block = format_providers_for_context(providers or [])

    situation_block = user_situation
    if extra_notes:
        situation_block = f"{user_situation}\n\n[Additional preferences]\n{extra_notes}"

    resp = chain.invoke(
        {
            "user_situation": situation_block,
            "provider_block": provider_block,
        }
    )

    return resp.content
