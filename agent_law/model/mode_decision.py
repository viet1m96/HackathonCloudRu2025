from pydantic import BaseModel

class ModeDecision(BaseModel):
    mode: str  # explain / draft / referral / pipeline