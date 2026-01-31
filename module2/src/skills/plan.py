"""
Plan Skill - Onboarding Phase 3

Generates personalized learning plan based on:
- Point A: Student profile (level, experience, motivation)
- Point B: Goal (target level, deadline, success criteria)

This is a multi-turn skill - AI generates plan, student can request modifications,
finally student accepts and plan is saved.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ._base import Skill


class PlanOutput(BaseModel):
    """
    Output from Plan Skill.

    Multi-turn skill - fields are collected progressively until student accepts.
    """

    # Required: AI response to student
    ai_response: str = Field(description="Conversational response presenting the plan")

    # Plan components (filled when AI generates plan)
    weekly_hours: Optional[int] = Field(
        default=None,
        description="Recommended hours per week (e.g., 3, 5, 7)"
    )

    weekly_schedule: Optional[Dict[str, str]] = Field(
        default=None,
        description="Week structure, e.g., {'monday': 'grammar', 'wednesday': 'conversation', 'friday': 'vocabulary'}"
    )

    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Main focus areas for learning, e.g., ['speaking', 'vocabulary', 'grammar']"
    )

    milestones: Optional[Dict[str, str]] = Field(
        default=None,
        description="Progress checkpoints, e.g., {'1_month': 'A2 speaking', '3_months': 'B1 overall'}"
    )

    # Multi-turn tracking
    fields_collected: List[str] = Field(
        default_factory=list,
        description="Cumulative list of plan components collected: ['weekly_hours', 'schedule', 'focus_areas', 'milestones']"
    )

    is_complete: bool = Field(
        default=False,
        description="True when student accepts the plan (all 4 core fields + confirmation)"
    )


class PlanSkill(Skill):
    """
    Plan generation skill.

    Multi-turn conversational skill that:
    1. Generates learning plan based on Point A + Point B
    2. Presents plan to student
    3. Allows modifications if student requests changes
    4. Finalizes when student accepts
    """

    @property
    def name(self) -> str:
        return "plan"

    @property
    def description(self) -> str:
        return "Plan generation - creates personalized learning plan (multi-turn)"

    @property
    def output_model(self) -> type[BaseModel]:
        return PlanOutput

    def get_prompt_template(self):
        """Load plan.j2 template from same directory."""
        env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        return env.get_template("plan.j2")
