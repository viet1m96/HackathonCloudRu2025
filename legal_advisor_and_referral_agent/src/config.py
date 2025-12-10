from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


SRC_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = SRC_DIR / "prompts"


MODEL_NAME: str = "unknown"

TEMPERATURE: float = 0.2

MAX_TOKENS: int = 2000


@dataclass
class ModeConfig:
    name: str
    system_prompt_path: Path
    examples_prompt_path: Optional[Path]
    allowed_tools: List[str]

    def load_system_prompt(self) -> str:
        return load_prompt(self.system_prompt_path)

    def load_examples_prompt(self) -> Optional[str]:
        if self.examples_prompt_path and self.examples_prompt_path.exists():
            return load_prompt(self.examples_prompt_path)
        return None


def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


MODES: Dict[str, ModeConfig] = {
    "explain": ModeConfig(
        name="explain",
        system_prompt_path=PROMPTS_DIR / "style_explain.md",
        examples_prompt_path=None,
        allowed_tools=[],
    ),
    "draft": ModeConfig(
        name="draft",
        system_prompt_path=PROMPTS_DIR / "system_draft.md",
        examples_prompt_path=None,
        allowed_tools=[],
    ),
    "referral": ModeConfig(
        name="referral",
        system_prompt_path=PROMPTS_DIR / "system_referral.md",
        examples_prompt_path=None,
        allowed_tools=[
            #still waiting
        ],
    ),
}


def get_mode_config(mode_name: str) -> ModeConfig:
    key = mode_name.strip().lower()
    if key not in MODES:
        raise ValueError(f"Unknown mode '{mode_name}'. Valid modes: {list(MODES.keys())}")
    return MODES[key]
