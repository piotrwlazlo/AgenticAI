"""
Enhanced Tutoring Skill - Main conversation mode with adaptive corrections.

Features:
- AI-driven adaptive error correction
- i+1 content delivery (teaching slightly above current level)
- Mistake awareness and targeted corrections
- Session continuity and context retention
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ._base import Skill


class EnhancedTutorResponse(BaseModel):
    """Extended tutoring response with correction metadata."""

    thinking: str = Field(
        description="Internal reasoning: what you noticed about student's language use, what learning opportunity you see, your correction strategy for this turn. Be analytical and pedagogical."
    )

    ai_response: str = Field(
        description="Your response to the student. In target language if appropriate. Include natural corrections if needed. Be warm, encouraging, and authentic."
    )

    corrections_made: List[str] = Field(
        default_factory=list,
        description="List of corrections made this turn for tracking. Format: 'error_type: student_form → correct_form'. Example: ['verb_tense: go yesterday → went yesterday', 'article: I like cat → I like cats']. Empty list if no corrections."
    )

    i_plus_one_delivered: bool = Field(
        default=False,
        description="True if your response introduced language slightly above student's current level (i+1). Examples: new vocabulary, complex structure, idiom. False if at comfortable level (i)."
    )

    # Homework management (Phase 3)
    homework_assigned: Optional[str] = Field(
        default=None,
        description="Homework task description if assigned this turn. E.g., 'Practice describing your morning routine in past tense (5-10 min)'. None if no homework assigned."
    )

    homework_focus_area: Optional[str] = Field(
        default=None,
        description="Focus area for assigned homework. One of: 'speaking', 'grammar', 'vocabulary', 'writing', 'listening'. Required if homework_assigned."
    )

    homework_checked: bool = Field(
        default=False,
        description="True if you checked student's previous homework this turn."
    )

    homework_feedback: Optional[str] = Field(
        default=None,
        description="Feedback on student's homework submission. Required if homework_checked=True."
    )


class EnhancedTutoringSkill(Skill):
    """
    Enhanced tutoring skill with adaptive pedagogy.

    Replaces basic tutoring.py with intelligent features:
    - Correction policy auto-adjusted by AI
    - Recurring mistakes prioritized
    - i+1 content delivery
    - Session continuity
    """

    @property
    def name(self) -> str:
        return "enhanced_tutoring"

    @property
    def description(self) -> str:
        return "Enhanced tutoring with adaptive corrections and i+1 delivery"

    @property
    def output_model(self) -> type[BaseModel]:
        return EnhancedTutorResponse

    def get_prompt_template(self):
        """Load enhanced_tutoring.j2 template."""
        env = Environment(loader=FileSystemLoader(Path(__file__).parent))
        return env.get_template("enhanced_tutoring.j2")
