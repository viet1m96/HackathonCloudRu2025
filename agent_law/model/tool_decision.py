from pydantic import BaseModel
from typing import Optional, Dict

class ToolDecision(BaseModel):
    tool: str
    arguments: Optional[Dict] = {}