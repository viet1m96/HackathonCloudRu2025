from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import LegalAdvisorAgent
from .intents import ModeName




class ProviderInput(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    jurisdiction: Optional[str] = None
    practice_areas: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class A2ARequest(BaseModel):
    mode: Optional[ModeName] = None
    query: str
    law_context: Optional[str] = ""
    extra_notes: Optional[str] = None


class A2AResponse(BaseModel):
    mode_used: ModeName
    answer_markdown: str
    meta: Dict[str, Any]



app = FastAPI(
    title="Legal Advisor & Referral Agent",
    description="HTTP API for agent-to-agent (A2A) communication.",
    version="0.1.0",
)

_agent = LegalAdvisorAgent()


@app.post("/legal-advisor-and-referral", response_model=A2AResponse)
async def legal_advisor_endpoint(request: A2ARequest) -> A2AResponse:
    try:
        payload: Dict[str, Any] = request.model_dump()
        mode_used, answer = _agent.handle_request(payload)

        return A2AResponse(
            mode_used=mode_used,
            answer_markdown=answer,
            meta={
                "success": True,
                "error": None,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected server-side error
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
