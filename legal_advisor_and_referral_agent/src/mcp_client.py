from __future__ import annotations

from typing import Any, Dict, List, Optional

import os
import requests


SUPPORT_MCP_BASE_URL = os.getenv("SUPPORT_MCP_BASE_URL", "http://support-mcp:8000")


class SupportMCPError(RuntimeError):
    """Raised when the Support MCP call fails."""

SUPPORT_MCP_TOOLS: Dict[str, str] = {
    # still waiting
}


def call_support_tool(
    tool_name: str,
    user_situation: str,
    extra_notes: Optional[str] = None,
) -> List[Dict[str, Any]]:
    path = SUPPORT_MCP_TOOLS.get(tool_name)
    if not path:
        raise SupportMCPError(f"Unknown Support MCP tool: {tool_name}")

    base = SUPPORT_MCP_BASE_URL.rstrip("/")
    url = f"{base}{path}"

    payload: Dict[str, Any] = {"situation": user_situation}
    if extra_notes:
        payload["extra_notes"] = extra_notes

    try:
        resp = requests.post(url, json=payload, timeout=10)
    except requests.RequestException as e:
        raise SupportMCPError(f"Failed to reach Support MCP at {url}: {e}") from e

    if resp.status_code != 200:
        raise SupportMCPError(
            f"Support MCP returned status {resp.status_code}: {resp.text}"
        )

    try:
        data = resp.json()
    except ValueError as e:
        raise SupportMCPError(
            f"Support MCP returned invalid JSON: {resp.text}"
        ) from e

    providers = data.get("providers", [])
    if not isinstance(providers, list):
        raise SupportMCPError(
            f"Support MCP response 'providers' is not a list: {providers!r}"
        )

    normalized: List[Dict[str, Any]] = []
    for p in providers:
        if isinstance(p, dict):
            normalized.append(p)

    return normalized


def search_support_providers(
    user_situation: str,
    extra_notes: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return call_support_tool(
        tool_name="support.search_providers",
        user_situation=user_situation,
        extra_notes=extra_notes,
    )
