"""
Preferences Skill - Onboarding Phase 4 (Final step)

Collects student's learning style preferences through quick questions.
This is a single-turn skill - all 3 questions asked at once.

Preferences collected:
1. correction_intensity: How aggressive should error corrections be? (auto/gentle/balanced/strict)
2. homework_frequency: Do they want homework between sessions? (none/light/moderate/intensive)
3. session_length: Preferred session duration? (short/medium/long)

All preferences are optional - defaults are provided if student doesn't specify.
"""

from pydantic import BaseModel, Field
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ._base import Skill


class PreferencesOutput(BaseModel):
    """
    Output from Preferences Skill.

    Single-turn skill - collects all 3 preferences at once.
    All fields are optional (have defaults).
    """

    # Required: AI response to student
    ai_response: str = Field(description="Conversational response asking about preferences")

    # Preference fields (all optional, have defaults)
    correction_intensity: str = Field(
        default="auto",
        description="Correction intensity: 'auto' (AI decides), 'gentle', 'balanced', 'strict'"
    )

    homework_frequency: str = Field(
        default="none",
        description="Homework frequency: 'none', 'light', 'moderate', 'intensive'"
    )

    session_length: str = Field(
        default="medium",
        description="Preferred session length: 'short' (15min), 'medium' (30min), 'long' (45min+)"
    )

    # Completion flag
    is_complete: bool = Field(
        default=False,
        description="True when student has answered (or skipped) the questions"
    )


class PreferencesSkill(Skill):
    """
    Preferences collection skill.

    Single-turn conversational skill that:
    1. Asks 3 quick questions about learning preferences
    2. Collects student's answers (all optional)
    3. Finalizes onboarding
    """

    @property
    def name(self) -> str:
        return "preferences"

    @property
    def description(self) -> str:
        return "Preferences collection - learning style preferences (single-turn)"

    @property
    def output_model(self) -> type[BaseModel]:
        return PreferencesOutput

    def get_prompt_template(self):
        """Load preferences.j2 template from same directory."""
        env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        return env.get_template("preferences.j2")
